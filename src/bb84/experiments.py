"""Eksperimenti H1 in H2 za BB84; rezultati se shranjujejo v results/."""

import argparse
import csv
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # Grafi se shranijo v datoteke, tudi brez odprtega namizja
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import PercentFormatter, ScalarFormatter
from scipy.stats import binom, binomtest

from bb84.analysis import calculate_qber, critical_error_count, detect_eavesdropping
from bb84.protocol import run_bb84, sift_transmissions

# Parametri raziskave: noise_level = 2 * QBER brez Eve
SAMPLE_SIZES = (20, 50, 100, 300, 500, 1000)
NOISE_LEVELS = (0.06, 0.10, 0.20, 0.40, 0.50)
INTERCEPTION_RATES = (0.0, 0.10, 0.20, 0.50, 1.0)
N = 2400
ALPHA = 0.05
REPETITIONS = 2000
BATCH_SIZE = 100
WORKERS = min(4, max(1, (os.cpu_count() or 1) // 2))
BASE_SEED = 20261107

RESULTS_DIR = Path("results")
DATA_FILE = RESULTS_DIR / "h1_h2_trials.csv"
SUMMARY_FILE = RESULTS_DIR / "h1_h2_summary.csv"

FIELDS = (
    ["noise_level", "interception_rate", "trial", "seed", "n", "alpha", "sifted_count"]
    + [f"detected_{m}" for m in SAMPLE_SIZES]
    + [f"errors_{m}" for m in SAMPLE_SIZES]
)


def run_trial(task: tuple[float, float, int, int]) -> dict:
    """Izvede eno neodvisno simulacijo in preveri vseh šest velikosti vzorca."""
    noise_level, interception_rate, trial, seed = task
    random.seed(seed)  # Ponovljivo generiranje bitov, baz in kontrolnih vzorcev

    transmissions = run_bb84(N, interception_rate, noise_level)
    sifted = sift_transmissions(transmissions)

    if len(sifted) < max(SAMPLE_SIZES):
        raise ValueError("Not enough sifted bits; increase N")

    # Vzorčimo brez ponavljanja; manjši vzorci so začetki istega vzorca.
    sampled = random.sample(sifted, max(SAMPLE_SIZES))
    expected_qber = noise_level / 2

    row = {
        "noise_level": noise_level,
        "interception_rate": interception_rate,
        "trial": trial,
        "seed": seed,
        "n": N,
        "alpha": ALPHA,
        "sifted_count": len(sifted),
    }

    for m in SAMPLE_SIZES:
        control = sampled[:m]
        _, errors, _ = calculate_qber(control)

        # True pomeni alarm; 0 % Eve -> FPR, sicer -> TPR.
        detected = detect_eavesdropping(control, expected_qber, ALPHA)
        row[f"detected_{m}"] = int(detected)
        row[f"errors_{m}"] = errors

    return row


def trial_seed(noise_level: float, interception_rate: float, trial: int) -> int:
    """Enolično seme v fiksni mreži (največ 100.000 ponovitev)."""
    if not 0 <= trial < 100_000:
        raise ValueError("trial must be between 0 and 99999")
    return (
        BASE_SEED
        + NOISE_LEVELS.index(noise_level) * 10_000_000
        + INTERCEPTION_RATES.index(interception_rate) * 100_000
        + trial
    )


def read_trials(path: Path) -> pd.DataFrame:
    """Preveri CSV pred nadaljevanjem ali analizo; poškodovanega ne spreminja."""
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            raise ValueError("Existing CSV is empty")
        stream.seek(-1, os.SEEK_END)
        if stream.read(1) != b"\n":
            raise ValueError("Existing CSV has an incomplete final line; inspect a copy manually")
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("Existing CSV has different columns")
        rows = list(reader)
    for row in rows:
        if None in row or any(value is None or value == "" for value in row.values()):
            raise ValueError("Existing CSV has an incomplete row")
        for field in FIELDS:
            row[field] = (
                float(row[field])
                if field in ("noise_level", "interception_rate", "alpha")
                else int(row[field])
            )
        if row["n"] != N or row["alpha"] != ALPHA:
            raise ValueError("Existing CSV uses different N or alpha")
        expected_seed = trial_seed(row["noise_level"], row["interception_rate"], row["trial"])
        if row["seed"] != expected_seed:
            raise ValueError("Existing CSV uses a different seed configuration")
        if not max(SAMPLE_SIZES) <= row["sifted_count"] <= N:
            raise ValueError("Existing CSV has an invalid sifted_count")
        previous_errors, previous_m = 0, 0
        for m in SAMPLE_SIZES:
            errors = row[f"errors_{m}"]
            if not 0 <= errors - previous_errors <= m - previous_m:
                raise ValueError("Existing CSV has invalid nested sample error counts")
            if row[f"detected_{m}"] not in (0, 1):
                raise ValueError("Existing CSV has an invalid detection flag")
            previous_errors, previous_m = errors, m
    data = pd.DataFrame(rows, columns=FIELDS)
    if data.duplicated(["noise_level", "interception_rate", "trial"]).any():
        raise ValueError("Existing CSV has duplicate trials")
    if not data.empty:
        for m in SAMPLE_SIZES:
            expected = binom.sf(data[f"errors_{m}"] - 1, m, data.noise_level / 2) <= ALPHA
            if (data[f"detected_{m}"] != expected).any():
                raise ValueError("Existing CSV has detection flags inconsistent with the test")
    return data


def run_experiments(
    repetitions: int = REPETITIONS, workers: int = WORKERS, results_dir: Path = RESULTS_DIR
) -> None:
    """Izvede manjkajoče poskuse; že shranjenih ne ponavlja."""
    if not 1 <= repetitions <= 100_000 or workers < 1:
        raise ValueError("Use 1..100000 repetitions and at least one worker")
    results_dir.mkdir(parents=True, exist_ok=True)
    data_file = results_dir / DATA_FILE.name
    completed = set()

    if data_file.exists():
        data = read_trials(data_file)
        completed = set(zip(data.noise_level, data.interception_rate, data.trial, strict=True))
        if not data.empty and data.trial.max() >= repetitions:
            raise ValueError(
                "Existing CSV has more trials than requested; use a separate directory"
            )

    new_file = not data_file.exists()
    with data_file.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
            file.flush()

        # En bazen procesov uporabimo za vse kombinacije parametrov.
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for noise_level in NOISE_LEVELS:
                for interception_rate in INTERCEPTION_RATES:
                    tasks = []
                    for trial in range(repetitions):
                        if (noise_level, interception_rate, trial) in completed:
                            continue
                        seed = trial_seed(noise_level, interception_rate, trial)
                        tasks.append((noise_level, interception_rate, trial, seed))

                    for start in range(0, len(tasks), BATCH_SIZE):
                        batch = tasks[start : start + BATCH_SIZE]
                        for row in executor.map(run_trial, batch, chunksize=1):
                            writer.writerow(row)
                            file.flush()  # Ob ponovnem zagonu uporabimo celotne zapisane vrstice.
                        print(
                            f"QBER0={noise_level / 2:.0%}, Eve={interception_rate:.0%}: "
                            f"{repetitions - len(tasks) + start + len(batch)}/{repetitions}",
                            flush=True,
                        )


def summarize_results(results_dir: Path = RESULTS_DIR) -> pd.DataFrame:
    """Iz ponovitev izračuna FPR/TPR in 95-% intervale zaupanja."""
    data = read_trials(results_dir / DATA_FILE.name)
    if data.empty:
        raise ValueError("No completed trials to summarize")
    rows = []

    for (noise_level, interception_rate), group in data.groupby(
        ["noise_level", "interception_rate"]
    ):
        q0 = noise_level / 2
        q1 = q0 + (1 - noise_level) * interception_rate / 4

        for m in SAMPLE_SIZES:
            alarms = int(group[f"detected_{m}"].sum())
            repetitions = len(group)
            ci = binomtest(alarms, repetitions).proportion_ci(method="wilson")

            # Teoretična moč istega eksaktnega testa, za primerjavo s simulacijo.
            critical_errors = critical_error_count(m, q0, ALPHA)
            theory_rate = float(binom.sf(critical_errors - 1, m, q1))

            rows.append(
                {
                    "qber_without_eve": q0,
                    "interception_rate": interception_rate,
                    "sample_size": m,
                    "repetitions": repetitions,
                    "alarms": alarms,
                    "observed_rate": alarms / repetitions,
                    "ci_low": ci.low,
                    "ci_high": ci.high,
                    "theoretical_rate": theory_rate,
                    "mean_sample_qber": group[f"errors_{m}"].mean() / m,
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(results_dir / SUMMARY_FILE.name, index=False)
    return summary


def analyze_h3(
    target_tpr: float = 0.95,
    max_sample_size: int = 50_000,
    results_dir: Path = RESULTS_DIR,
    formats: tuple[str, ...] = ("png",),
) -> pd.DataFrame:
    """Poišče najmanjši kontrolni vzorec za zahtevano uspešnost zaznavanja."""

    if not 0 < target_tpr < 1 or not isinstance(max_sample_size, int) or max_sample_size < 1:
        raise ValueError("Use 0 < target_tpr < 1 and a positive integer max_sample_size")
    results_dir.mkdir(parents=True, exist_ok=True)
    results = []

    # Preverimo vse velikosti kontrolnega vzorca do določene meje
    sample_sizes = np.arange(1, max_sample_size + 1)

    for noise_level in NOISE_LEVELS:
        q0 = noise_level / 2  # Pričakovani QBER brez Eve

        # Najmanjše število napak, pri katerem binomski test sproži alarm
        critical_errors = binom.ppf(1 - ALPHA, sample_sizes, q0).astype(int) + 1
        # Popravek numerične meje: enaka primerjava repa kot pri eksaktnem testu.
        while np.any(binom.sf(critical_errors - 2, sample_sizes, q0) <= ALPHA):
            critical_errors -= binom.sf(critical_errors - 2, sample_sizes, q0) <= ALPHA
        while np.any(binom.sf(critical_errors - 1, sample_sizes, q0) > ALPHA):
            critical_errors += binom.sf(critical_errors - 1, sample_sizes, q0) > ALPHA

        # Teoretična verjetnost lažnega alarma za vsako velikost vzorca
        fpr = binom.sf(critical_errors - 1, sample_sizes, q0)

        for interception_rate in INTERCEPTION_RATES:
            if interception_rate == 0:
                continue  # Brez Eve ni TPR, zato tega scenarija ne vključimo

            # Pričakovani QBER pri delnem prestrezanju Eve
            q1 = q0 + (1 - noise_level) * interception_rate / 4

            # Teoretična verjetnost zaznave pri posamezni velikosti vzorca
            tpr = binom.sf(critical_errors - 1, sample_sizes, q1)

            # Poiščemo vse velikosti, ki dosegajo zahtevani TPR in FPR
            valid = np.flatnonzero((tpr >= target_tpr) & (fpr <= ALPHA))

            if len(valid) > 0:
                index = valid[0]  # Prva ustrezna velikost je najmanjša
                min_size = int(sample_sizes[index])
                actual_tpr = float(tpr[index])
                actual_fpr = float(fpr[index])
            else:
                min_size = None  # Zahtevana uspešnost ni dosežena do max_sample_size
                actual_tpr = None
                actual_fpr = None

            results.append(
                {
                    "qber_without_eve": q0,
                    "interception_rate": interception_rate,
                    "min_sample_size": min_size,
                    "theoretical_tpr": actual_tpr,
                    "theoretical_fpr": actual_fpr,
                    "target_tpr": target_tpr,
                    "max_sample_size": max_sample_size,
                }
            )

    # Shranimo tabelo minimalnih velikosti kontrolnega vzorca
    summary = pd.DataFrame(results)
    summary.to_csv(results_dir / "h3_min_sample.csv", index=False)

    # Graf: potrebna velikost vzorca glede na šum in intenzivnost napada
    plt.figure()

    for eve_rate in INTERCEPTION_RATES:
        if eve_rate == 0:
            continue

        subset = summary[summary.interception_rate == eve_rate]

        plt.plot(
            subset.qber_without_eve * 100,
            subset.min_sample_size,
            marker="o",
            label=f"Eve={eve_rate:.0%}",
        )

    plt.xlabel("Osnovni QBER brez Eve (%)")
    plt.ylabel("Najmanjši kontrolni vzorec m (logaritemska skala)")
    plt.yscale("log")  # Velikosti se razlikujejo za več velikostnih redov
    plt.xticks([level / 2 * 100 for level in NOISE_LEVELS])
    plt.title(f"H3: teoretični minimum za TPR ≥ {target_tpr:.0%}, FPR ≤ {ALPHA:.0%}")
    plt.legend(title="Delež prestrezanja", fontsize="small")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    _save_figure(results_dir / "h3_min_sample", formats)
    plt.close()

    print("\nH3 - minimalne velikosti kontrolnih vzorcev:")
    print(summary.to_string(index=False))

    return summary


def _plot_rate(x, subset: pd.DataFrame, label: str) -> None:
    """Monte Carlo ocena z Wilsonovim intervalom in teorija istega testa."""
    line = plt.errorbar(
        x,
        subset.observed_rate,
        yerr=[subset.observed_rate - subset.ci_low, subset.ci_high - subset.observed_rate],
        marker="o",
        capsize=2,
        label=label,
    )
    plt.plot(x, subset.theoretical_rate, linestyle="--", color=line.lines[0].get_color())


def _save_figure(stem: Path, formats: tuple[str, ...]) -> None:
    for extension in formats:
        plt.savefig(stem.with_suffix(f".{extension}"), dpi=300, bbox_inches="tight")


def _sample_axis() -> None:
    plt.xscale("log")
    plt.xticks(SAMPLE_SIZES)
    plt.gca().xaxis.set_major_formatter(ScalarFormatter())
    plt.gca().minorticks_off()


def make_plots(
    summary: pd.DataFrame, results_dir: Path = RESULTS_DIR, formats: tuple[str, ...] = ("png",)
) -> None:
    """Shrani grafe za H1, H2 ter kontrolo lažnih alarmov."""
    # H1: TPR v odvisnosti od velikosti vzorca pri 20-% prestrezanju.
    plt.figure()
    for noise_level in NOISE_LEVELS:
        q0 = noise_level / 2
        subset = summary[(summary.qber_without_eve == q0) & (summary.interception_rate == 0.20)]
        _plot_rate(subset.sample_size, subset, f"QBER0={q0:.0%}")
    plt.xlabel("Velikost kontrolnega vzorca")
    _sample_axis()
    plt.title("H1: prestrezanje 20 %; α = 0,05")
    plt.ylabel("TPR (delež pravilnih zaznav)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    plt.ylim(0, 1.02)
    plt.legend(title="Točke: simulacija z 95-% IZ\nČrtkano: teorija", fontsize="small")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    _save_figure(results_dir / "h1_tpr_vs_sample", formats)
    plt.close()

    # H2: TPR v odvisnosti od šuma pri fiksnem vzorcu 300 bitov.
    plt.figure()
    for eve_rate in INTERCEPTION_RATES[1:]:
        subset = summary[(summary.sample_size == 300) & (summary.interception_rate == eve_rate)]
        _plot_rate(subset.qber_without_eve * 100, subset, f"Eve={eve_rate:.0%}")
    plt.xlabel("Osnovni QBER brez Eve (%)")
    plt.xticks([level / 2 * 100 for level in NOISE_LEVELS])
    plt.title("H2: kontrolni vzorec 300 bitov; α = 0,05")
    plt.ylabel("TPR (delež pravilnih zaznav)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    plt.ylim(0, 1.02)
    plt.legend(title="Točke: simulacija z 95-% IZ\nČrtkano: teorija", fontsize="small")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    _save_figure(results_dir / "h2_tpr_vs_noise", formats)
    plt.close()

    # Preverjanje FPR, ko Eve ni prisotna.
    plt.figure()
    for noise_level in NOISE_LEVELS:
        q0 = noise_level / 2
        subset = summary[(summary.qber_without_eve == q0) & (summary.interception_rate == 0)]
        _plot_rate(subset.sample_size, subset, f"QBER0={q0:.0%}")
    plt.axhline(ALPHA, linestyle=":", color="black", label="Nominalni α = 5 %")
    plt.title("Lažni alarmi: brez Eve")
    plt.xlabel("Velikost kontrolnega vzorca")
    _sample_axis()
    plt.ylabel("FPR (delež lažnih alarmov)")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    upper = max(ALPHA * 1.3, float(summary[summary.interception_rate == 0].ci_high.max()) * 1.12)
    plt.ylim(0, min(1.02, upper))
    plt.legend(title="Točke: simulacija z 95-% IZ\nČrtkano: teorija", fontsize="small")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    _save_figure(results_dir / "fpr_vs_sample", formats)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=REPETITIONS)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if not args.summarize_only:
        run_experiments(args.repetitions, args.workers, args.output_dir)
    summary = summarize_results(args.output_dir)
    make_plots(summary, args.output_dir)
    analyze_h3(results_dir=args.output_dir)
    print(f"\nRezultati in grafi so shranjeni v: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
