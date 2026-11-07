import random
from scipy.stats import binomtest
import numpy as np

def calculate_qber(sifted: list[dict]) ->  tuple[float, int, int]:
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

    sample_indices = set(random.sample(range(len(sifted)), sample_size)) #naključno izberemo indekse prenosov, ki jih bomo uporabili kot kontrolne

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

    qber, errors, total = calculate_qber(control)

    test = binomtest(
        k=errors,
        n=total,
        p=expected_qber,
        alternative="greater",
    )

    return test.pvalue <= alpha