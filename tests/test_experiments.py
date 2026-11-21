import csv
from concurrent.futures import ProcessPoolExecutor
from unittest.mock import MagicMock

import numpy as np
import pytest
from scipy.stats import binom

from bb84 import experiments as exp
from bb84.analysis import critical_error_count


def write_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=exp.FIELDS)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def row():
    return {
        "noise_level": 0.06,
        "interception_rate": 0.0,
        "trial": 0,
        "seed": exp.trial_seed(0.06, 0.0, 0),
        "n": exp.N,
        "alpha": exp.ALPHA,
        "sifted_count": 1200,
        **{f"detected_{m}": 0 for m in exp.SAMPLE_SIZES},
        **{f"errors_{m}": 0 for m in exp.SAMPLE_SIZES},
    }


@pytest.mark.parametrize("failure", ["duplicate", "seed", "truncated", "errors", "flag"])
def test_invalid_csv_is_not_modified(tmp_path, row, failure):
    path = tmp_path / exp.DATA_FILE.name
    if failure == "seed":
        row["seed"] += 1
    if failure == "errors":
        row["errors_20"] = 21
    if failure == "flag":
        row["detected_20"] = 1
    write_rows(path, [row, row] if failure == "duplicate" else [row])
    if failure == "truncated":
        path.write_bytes(path.read_bytes()[:-5])
    before = path.read_bytes()
    with pytest.raises(ValueError):
        exp.run_experiments(1, 1, tmp_path)
    assert path.read_bytes() == before


def test_nested_samples_and_insufficient_sifted_bits(monkeypatch):
    transmissions = [
        dict(alice_basis="X", bob_basis="X", alice_bit=0, bob_bit=int(i % 5 == 0))
        for i in range(1100)
    ]
    monkeypatch.setattr(exp, "run_bb84", lambda *args: transmissions)
    row = exp.run_trial((0.2, 0.2, 0, 120))
    previous, previous_m = 0, 0
    for m in exp.SAMPLE_SIZES:
        assert 0 <= row[f"errors_{m}"] - previous <= m - previous_m
        previous, previous_m = row[f"errors_{m}"], m
    transmissions[:] = transmissions[:999]
    with pytest.raises(ValueError, match="Not enough"):
        exp.run_trial((0.2, 0.2, 0, 120))


def test_parallel_results_match_serial():
    tasks = [
        (noise, rate, 0, exp.trial_seed(noise, rate, 0))
        for noise, rate in [(0.06, 0.0), (0.2, 0.2)]
    ]
    serial = [exp.run_trial(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=2) as executor:
        parallel = list(executor.map(exp.run_trial, reversed(tasks)))
    assert parallel == list(reversed(serial))


def test_summary_wilson_and_theory(tmp_path, row):
    write_rows(tmp_path / exp.DATA_FILE.name, [row])
    summary = exp.summarize_results(tmp_path)
    assert (summary.observed_rate == 0).all()
    assert np.allclose(summary.ci_low, 0)
    assert np.allclose(summary.ci_high, 0.7934506856227626)
    for item in summary.itertuples():
        k = critical_error_count(item.sample_size, 0.03)
        assert item.theoretical_rate == binom.sf(k - 1, item.sample_size, 0.03)


def test_interrupted_run_resumes_without_duplicates(monkeypatch, tmp_path, row):
    executor = MagicMock()
    executor.__enter__.return_value = executor
    executor.map.side_effect = lambda function, tasks, **kwargs: map(function, tasks)
    monkeypatch.setattr(exp, "ProcessPoolExecutor", lambda **kwargs: executor)
    calls = []

    def trial(task):
        if len(calls) == 3:
            raise RuntimeError("simulated interruption")
        calls.append(task)
        noise, rate, index, seed = task
        return dict(row, noise_level=noise, interception_rate=rate, trial=index, seed=seed)

    monkeypatch.setattr(exp, "run_trial", trial)
    with pytest.raises(RuntimeError, match="interruption"):
        exp.run_experiments(2, 1, tmp_path)
    path = tmp_path / exp.DATA_FILE.name
    assert len(exp.read_trials(path)) == 3
    saved_calls = calls.copy()

    def resumed_trial(task):
        assert task not in saved_calls
        calls.append(task)
        noise, rate, index, seed = task
        return dict(row, noise_level=noise, interception_rate=rate, trial=index, seed=seed)

    monkeypatch.setattr(exp, "run_trial", resumed_trial)
    exp.run_experiments(2, 1, tmp_path)
    assert len(exp.read_trials(path)) == 50
    assert len(calls) == len(set(calls)) == 50
    before = path.read_bytes()
    exp.run_experiments(2, 1, tmp_path)
    assert path.read_bytes() == before
    assert len(calls) == 50
