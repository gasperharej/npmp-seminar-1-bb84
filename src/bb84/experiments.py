import os
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from bb84.protocol import run_bb84, sift_transmissions
from bb84.analysis import select_control_sample, detect_eavesdropping


def run_trial(
    n: int,
    sample_size: int,
    noise_level: float,
    interception_rate: float,
    alpha: float = 0.05,
) -> bool:
    """Izvede en BB84 poskus in vrne odločitev o prisluškovanju."""

    # Simulacija prenosa in izbira bitov z ujemajočima se bazama
    transmissions = run_bb84(n, interception_rate, noise_level)
    sifted = sift_transmissions(transmissions)

    if len(sifted) < sample_size:
        raise ValueError("Not enough sifted bits for control sample")

    # Naključno izberemo bite za javno preverjanje
    control, _ = select_control_sample(sifted, sample_size)

    # Pričakovana stopnja napak brez Eve za izbrani depolarizacijski model
    expected_qber = noise_level / 2

    # Preverimo, ali je število napak statistično značilno povečano
    return detect_eavesdropping(control, expected_qber, alpha)


def estimate_detection_rate(
    repetitions: int,
    n: int,
    sample_size: int,
    noise_level: float,
    interception_rate: float,
    alpha: float = 0.05,
    workers: int | None = None,
) -> float:

    if repetitions <= 0:
        raise ValueError("Repetitions must be positive")

    if workers is None:
        workers = min(8, max(1, (os.cpu_count() or 1) // 2))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = executor.map(
            run_trial,
            repeat(n, repetitions),
            repeat(sample_size, repetitions),
            repeat(noise_level, repetitions),
            repeat(interception_rate, repetitions),
            repeat(alpha, repetitions),
            chunksize=4,
        )

        return sum(results) / repetitions # detection rate = št. sproženih zaznav / št. ponovitev


import time

if __name__ == "__main__":
    for workers in [1, 2, 4, 8]:
        start = time.perf_counter()

        rate = estimate_detection_rate(
            repetitions=16,
            n=300,
            sample_size=50,
            noise_level=0.2,
            interception_rate=1.0,
            workers=workers,
        )

        elapsed = time.perf_counter() - start

        print(f"{workers} procesov: {elapsed:.2f} s, zaznave: {rate:.1%}")