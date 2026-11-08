import random

from scipy.stats import binom, binomtest


def calculate_qber(sifted: list[dict]) -> tuple[float, int, int]:
    """Izračuna delež napak med obdržanimi biti."""
    if not sifted:
        raise ValueError("No sifted bits available")

    errors = 0

    for transmission in sifted:
        if transmission["alice_bit"] != transmission["bob_bit"]:
            errors += 1

    return errors / len(sifted), errors, len(sifted)


def select_control_sample(sifted: list[dict], sample_size: int) -> tuple[list[dict], list[dict]]:
    """Vrne kontrolni vzorec in preostale prenose."""

    if not 0 <= sample_size <= len(sifted):
        raise ValueError("Invalid control sample size")

    sample_indices = set(random.sample(range(len(sifted)), sample_size))

    control = []
    remaining = []

    for index, transmission in enumerate(sifted):
        if index in sample_indices:
            control.append(transmission)
        else:
            remaining.append(transmission)

    return control, remaining


def detect_eavesdropping(control: list[dict], expected_qber: float, alpha: float = 0.05) -> bool:
    """Odloči, ali je število napak sumljivo glede na pričakovani šum."""
    if not control:
        raise ValueError("Control sample cannot be empty")

    if not 0 <= expected_qber <= 1:
        raise ValueError("Expected QBER must be between 0 and 1")

    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1 (exclusive)")

    _, errors, total = calculate_qber(control)

    test = binomtest(
        k=errors,
        n=total,
        p=expected_qber,
        alternative="greater",
    )

    return bool(test.pvalue <= alpha)


def critical_error_count(sample_size: int, expected_qber: float, alpha: float = 0.05) -> int:
    """Najmanjši k s P(Bin(m,q0) >= k) <= alpha; m+1 pomeni brez zavrnitve.

    Primerjamo rep neposredno, enako kot binomtest(alternative="greater"),
    tudi na meji pvalue == alpha in pri q0=0 ali q0=1.
    """
    if not isinstance(sample_size, int) or sample_size < 1:
        raise ValueError("sample_size must be a positive integer")
    if not 0 <= expected_qber <= 1 or not 0 < alpha < 1:
        raise ValueError("Invalid expected_qber or alpha")
    low, high = 0, sample_size + 1
    while low < high:
        middle = (low + high) // 2
        if binom.sf(middle - 1, sample_size, expected_qber) <= alpha:
            high = middle
        else:
            low = middle + 1
    return low
