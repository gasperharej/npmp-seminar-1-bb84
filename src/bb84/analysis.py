import random

def calculate_qber(sifted: list[dict]) -> float:
    """Izračuna delež napak med obdržanimi biti."""
    if not sifted:
        raise ValueError("No sifted bits available")

    errors = 0

    for transmission in sifted:
        if transmission["alice_bit"] != transmission["bob_bit"]:
            errors += 1

    return errors / len(sifted)

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