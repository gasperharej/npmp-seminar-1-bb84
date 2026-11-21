import random

import pytest
from scipy.stats import binom, binomtest

from bb84.analysis import (
    calculate_qber,
    critical_error_count,
    detect_eavesdropping,
    select_control_sample,
)


def bits(n, errors):
    return [{"alice_bit": 0, "bob_bit": int(i < errors)} for i in range(n)]


def test_qber_and_sample_partition():
    source = bits(20, 4)
    assert calculate_qber(source) == (0.2, 4, 20)
    random.seed(32)
    sample, remaining = select_control_sample(source, 8)
    assert len(sample) == 8 and len(remaining) == 12
    assert len({id(item) for item in sample + remaining}) == 20
    assert len(source) == 20
    assert select_control_sample(source, 0) == ([], source)
    with pytest.raises(ValueError):
        select_control_sample(source, 21)
    with pytest.raises(ValueError):
        calculate_qber([])


@pytest.mark.parametrize(
    "m,q0,alpha",
    [
        (20, 0.03, 0.05),
        (50, 0.25, 0.05),
        (100, 0.1, 0.05),
        (1, 0, 0.05),
        (1, 1, 0.05),
        (10, 0.2, float(binom.sf(1, 10, 0.2))),
    ],
)
def test_critical_threshold_matches_every_exact_decision(m, q0, alpha):
    threshold = critical_error_count(m, q0, alpha)
    for errors in range(m + 1):
        expected = bool(binomtest(errors, m, q0, alternative="greater").pvalue <= alpha)
        assert detect_eavesdropping(bits(m, errors), q0, alpha) == expected
        assert (errors >= threshold) == expected
    assert binom.sf(threshold - 1, m, q0) <= alpha
    if threshold <= m:
        assert binom.sf(threshold - 2, m, q0) > alpha


@pytest.mark.parametrize(
    "q0,alpha", [(-0.1, 0.05), (1.1, 0.05), (0.1, 0), (0.1, 1), (float("nan"), 0.05)]
)
def test_invalid_detection_parameters(q0, alpha):
    with pytest.raises(ValueError):
        detect_eavesdropping(bits(1, 0), q0, alpha)


def test_empty_control_rejected():
    with pytest.raises(ValueError):
        detect_eavesdropping([], 0.1)
