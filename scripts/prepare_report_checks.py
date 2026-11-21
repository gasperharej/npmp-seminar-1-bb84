#!/usr/bin/env python3
"""Dodatna preverjanja za zahteve QC: idealni kanal in lastnosti vezij.

Ne spreminja raziskovalnega nabora H1/H2. Primerjava QBER uporablja en
nov prenos 6000 signalov na konfiguracijo; ni ocena TPR iz 2000 ponovitev.
Prevedena vezja so dodatna diagnostika. Glavni eksperiment vezij ne prevaja.
"""

import csv
import json
import platform
import random
from importlib.metadata import version
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from scipy.stats import binomtest

from bb84.analysis import calculate_qber
from bb84.protocol import interception, measure_state, prepare_state, run_bb84, sift_transmissions

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report" / "evidence"
SEED = 20261121
SIGNALS = 6000


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tex_number(value: float, decimals: int = 2) -> str:
    return rf"\num{{{value:.{decimals}f}}}"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (noise, rate) in enumerate(
        (noise, rate) for noise in (0.0, 0.06, 0.5) for rate in (0.0, 0.2, 1.0)
    ):
        seed = SEED + index
        random.seed(seed)
        sifted = sift_transmissions(run_bb84(SIGNALS, rate, noise))
        qber, errors, count = calculate_qber(sifted)
        ci = binomtest(errors, count).proportion_ci(method="wilson")
        rows.append(
            dict(
                noise_level=noise,
                interception_rate=rate,
                seed=seed,
                n=SIGNALS,
                shots_per_circuit=1,
                sifted_count=count,
                errors=errors,
                observed_qber=qber,
                ci_low=float(ci.low),
                ci_high=float(ci.high),
                theoretical_qber=noise / 2 + (1 - noise) * rate / 4,
            )
        )
        print(f"lambda={noise:g}, r={rate:g}: QBER={qber:.4%}", flush=True)
    write_csv(OUTPUT / "ideal_vs_noisy.csv", rows)
    table = [
        r"\begin{tabular}{rrrrl}",
        r"\toprule",
        r"$\lambda$ & $r$ & QBER teor. [\%] & QBER sim. [\%] & 95-\% IZ [\%] \\",
        r"\midrule",
    ]
    for row in rows:
        table.append(
            " & ".join(
                [
                    tex_number(row["noise_level"]),
                    tex_number(row["interception_rate"]),
                    tex_number(100 * row["theoretical_qber"]),
                    tex_number(100 * row["observed_qber"]),
                    f"[{tex_number(100 * row['ci_low'])}; "
                    f"{tex_number(100 * row['ci_high'])}]",
                ]
            )
            + r" \\"
        )
    table.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "ideal_vs_noisy.tex").write_text("\n".join(table) + "\n", encoding="utf-8")

    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(depolarizing_error(0.2, 1), ["id"])
    simulator = AerSimulator(noise_model=noise_model, max_parallel_threads=1)
    metrics = []
    for bit in (0, 1):
        for alice in ("X", "Z"):
            for bob in ("X", "Z"):
                for eve in (None, "X", "Z"):
                    circuit = QuantumCircuit(1, 2)
                    prepare_state(circuit, bit, alice)
                    if eve is not None:
                        interception(circuit, eve)
                    circuit.id(0)
                    measure_state(circuit, bob)
                    compiled = transpile(
                        circuit, simulator, optimization_level=0, seed_transpiler=SEED
                    )
                    if compiled.count_ops().get("id", 0) != 1:
                        raise RuntimeError("Compilation removed the channel's id gate")
                    for stage, item in (("original", circuit), ("transpiled", compiled)):
                        metrics.append(
                            dict(
                                alice_bit=bit,
                                alice_basis=alice,
                                bob_basis=bob,
                                eve_basis=eve or "none",
                                stage=stage,
                                qubits=item.num_qubits,
                                classical_bits=item.num_clbits,
                                depth=item.depth(),
                                two_qubit_gates=sum(
                                    instruction.operation.num_qubits == 2
                                    and instruction.operation.name != "barrier"
                                    for instruction in item.data
                                ),
                                id_gates=int(item.count_ops().get("id", 0)),
                                operations=json.dumps(dict(item.count_ops()), sort_keys=True),
                            )
                        )
    write_csv(OUTPUT / "circuit_metrics.csv", metrics)
    table = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Eve & Kubiti & Globina prej & Globina potem & Dvokubitna vrata \\",
        r"\midrule",
    ]
    for eve, name in (("none", "brez Eve"), ("X", "baza X"), ("Z", "baza Z")):
        depths = []
        for stage in ("original", "transpiled"):
            values = [
                item["depth"]
                for item in metrics
                if item["eve_basis"] == eve and item["stage"] == stage
            ]
            depths.append(f"{min(values)}--{max(values)}")
        table.append(f"{name} & 1 & {depths[0]} & {depths[1]} & 0" + r" \\")
    table.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "circuit_metrics.tex").write_text("\n".join(table) + "\n", encoding="utf-8")

    # Dejanski neuspesen poskus za razdelek Kaj ni delovalo: optimizacija
    # odstrani id in s tem kanal suma. Glavnega eksperimenta ne spreminjamo.
    pitfall_noise = NoiseModel()
    pitfall_noise.add_all_qubit_quantum_error(depolarizing_error(0.5, 1), ["id"])
    pitfall_simulator = AerSimulator(noise_model=pitfall_noise, max_parallel_threads=1)
    circuit = QuantumCircuit(1, 2)
    circuit.id(0)
    circuit.measure(0, 0)
    pitfall = []
    for level in (0, 1, 3):
        compiled = transpile(
            circuit, pitfall_simulator, optimization_level=level, seed_transpiler=SEED
        )
        counts = pitfall_simulator.run(
            compiled, shots=10000, seed_simulator=SEED
        ).result().get_counts()
        errors = sum(count for bits, count in counts.items() if bits[-1] == "1")
        pitfall.append(
            dict(
                optimization_level=level,
                noise_level=0.5,
                shots=10000,
                seed_simulator=SEED,
                id_gates=int(compiled.count_ops().get("id", 0)),
                errors=errors,
                observed_qber=errors / 10000,
                intended_qber=0.25,
            )
        )
    write_csv(OUTPUT / "optimization_pitfall.csv", pitfall)
    metadata = {
        "purpose": "Additional QC requirements; separate from the original H1/H2 experiment",
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ("qiskit", "qiskit-aer", "scipy")},
        "ideal_comparison": "One session of 6000 signals per setting; shots=1 per circuit",
        "circuit_diagnostics": {
            "backend": "AerSimulator with depolarizing_error(0.2, 1) on id",
            "optimization_level": 0,
            "seed_transpiler": SEED,
            "hardware_jobs": "None; no real quantum processor used",
            "original_experiment": "Circuits submitted directly to Aer, without transpile",
        },
        "optimization_pitfall": "Separate 10000-shot circuits; compare levels 0, 1 and 3",
    }
    (OUTPUT / "environment.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Saved evidence to {OUTPUT}")


if __name__ == "__main__":
    main()
