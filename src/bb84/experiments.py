"""Eksperimenti H1 in H2 za BB84; rezultati se shranjujejo v results/."""

import csv
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Grafi se shranijo v datoteke, tudi brez odprtega namizja
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import binom, binomtest

from bb84.protocol import run_bb84, sift_transmissions
from bb84.analysis import calculate_qber, detect_eavesdropping


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


def run_experiments() -> None:
    """Izvede manjkajoče poskuse; že shranjenih ne ponavlja."""
    RESULTS_DIR.mkdir(exist_ok=True)
    completed = set()

    if DATA_FILE.exists():
        with DATA_FILE.open(newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != FIELDS:
                raise ValueError("Existing CSV has different columns")
            for row in reader:
                if int(row["n"]) != N or float(row["alpha"]) != ALPHA:
                    raise ValueError("Existing CSV uses different N or alpha")
                completed.add((float(row["noise_level"]), float(row["interception_rate"]), int(row["trial"])))

    new_file = not DATA_FILE.exists()
    with DATA_FILE.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        # En bazen procesov uporabimo za vse kombinacije parametrov.
        with ProcessPoolExecutor(max_workers=WORKERS) as executor:
            for noise_index, noise_level in enumerate(NOISE_LEVELS):
                for eve_index, interception_rate in enumerate(INTERCEPTION_RATES):
                    tasks = []
                    for trial in range(REPETITIONS):
                        if (noise_level, interception_rate, trial) in completed:
                            continue
                        seed = BASE_SEED + noise_index * 10_000_000 + eve_index * 100_000 + trial
                        tasks.append((noise_level, interception_rate, trial, seed))

                    for start in range(0, len(tasks), BATCH_SIZE):
                        batch = tasks[start:start + BATCH_SIZE]
                        for row in executor.map(run_trial, batch, chunksize=1):
                            writer.writerow(row)
                        file.flush()  # Rezultati ostanejo shranjeni tudi ob prekinitvi.
                        print(
                            f"QBER0={noise_level / 2:.0%}, Eve={interception_rate:.0%}: "
                            f"{min(REPETITIONS, REPETITIONS - len(tasks) + start + len(batch))}/{REPETITIONS}",
                            flush=True,
                        )


def summarize_results() -> pd.DataFrame:
    """Iz ponovitev izračuna FPR/TPR in 95-% intervale zaupanja."""
    data = pd.read_csv(DATA_FILE)
    rows = []

    for (noise_level, interception_rate), group in data.groupby(["noise_level", "interception_rate"]):
        q0 = noise_level / 2
        q1 = q0 + (1 - noise_level) * interception_rate / 4

        for m in SAMPLE_SIZES:
            alarms = int(group[f"detected_{m}"].sum())
            repetitions = len(group)
            ci = binomtest(alarms, repetitions).proportion_ci(method="wilson")

            # Teoretična moč istega eksaktnega testa, za primerjavo s simulacijo.
            critical_errors = int(binom.ppf(1 - ALPHA, m, q0)) + 1
            theory_rate = float(binom.sf(critical_errors - 1, m, q1))

            rows.append({
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
            })

    summary = pd.DataFrame(rows)
    summary.to_csv(SUMMARY_FILE, index=False)
    return summary


def preview_h3(summary: pd.DataFrame) -> None:
    """Približna H3: najmanjši izmed testiranih vzorcev s teoretičnim TPR >= 95 %."""
    rows = []
    for noise_level in NOISE_LEVELS:
        for eve_rate in INTERCEPTION_RATES[1:]:
            subset = summary[
                (summary.qber_without_eve == noise_level / 2)
                & (summary.interception_rate == eve_rate)
                & (summary.theoretical_rate >= 0.95)
            ]
            rows.append({
                "qber_without_eve": noise_level / 2,
                "interception_rate": eve_rate,
                "smallest_tested_m": int(subset.sample_size.min()) if not subset.empty else None,
            })
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "h3_coarse_preview.csv", index=False)


def make_plots(summary: pd.DataFrame) -> None:
    """Shrani grafe za H1, H2 ter kontrolo lažnih alarmov."""
    # H1: TPR v odvisnosti od velikosti vzorca pri 20-% prestrezanju.
    plt.figure()
    for noise_level in NOISE_LEVELS:
        q0 = noise_level / 2
        subset = summary[(summary.qber_without_eve == q0) & (summary.interception_rate == 0.20)]
        plt.plot(subset.sample_size, subset.observed_rate, marker="o", label=f"QBER0={q0:.0%}")
    plt.xlabel("Velikost kontrolnega vzorca")
    plt.ylabel("TPR (delež pravilnih zaznav)")
    plt.ylim(0, 1.02)
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "h1_tpr_vs_sample.png", dpi=180)
    plt.close()

    # H2: TPR v odvisnosti od šuma pri fiksnem vzorcu 300 bitov.
    plt.figure()
    for eve_rate in INTERCEPTION_RATES[1:]:
        subset = summary[(summary.sample_size == 300) & (summary.interception_rate == eve_rate)]
        plt.plot(subset.qber_without_eve * 100, subset.observed_rate, marker="o", label=f"Eve={eve_rate:.0%}")
    plt.xlabel("Osnovni QBER brez Eve (%)")
    plt.ylabel("TPR (delež pravilnih zaznav)")
    plt.ylim(0, 1.02)
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "h2_tpr_vs_noise.png", dpi=180)
    plt.close()

    # Preverjanje FPR, ko Eve ni prisotna.
    plt.figure()
    for noise_level in NOISE_LEVELS:
        q0 = noise_level / 2
        subset = summary[(summary.qber_without_eve == q0) & (summary.interception_rate == 0)]
        plt.plot(subset.sample_size, subset.observed_rate, marker="o", label=f"QBER0={q0:.0%}")
    plt.axhline(ALPHA, linestyle="--", label="alpha = 5 %")
    plt.xlabel("Velikost kontrolnega vzorca")
    plt.ylabel("FPR (delež lažnih alarmov)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "fpr_vs_sample.png", dpi=180)
    plt.close()


if __name__ == "__main__":
    run_experiments()
    summary = summarize_results()
    make_plots(summary)
    preview_h3(summary)
    print(f"\nRezultati in grafi so shranjeni v: {RESULTS_DIR.resolve()}")
