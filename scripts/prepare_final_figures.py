#!/usr/bin/env python3
"""Pripravi končne grafe iz popolnega CSV brez novih kvantnih simulacij."""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from importlib.metadata import distributions
from pathlib import Path

import matplotlib.pyplot as plt
from cycler import cycler

from bb84.experiments import (
    INTERCEPTION_RATES,
    NOISE_LEVELS,
    REPETITIONS,
    make_plots,
    read_trials,
    summarize_results,
)

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "src/bb84/results/h1_h2_trials.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/final-figures")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_dir.resolve()
    source_hash = sha256(source)
    data = read_trials(source)
    expected_groups = {(noise, rate) for noise in NOISE_LEVELS for rate in INTERCEPTION_RATES}
    groups = data.groupby(["noise_level", "interception_rate"])
    if set(groups.groups) != expected_groups:
        raise ValueError("Final figures require all 25 research configurations")
    if any(
        len(group) != REPETITIONS or set(group.trial) != set(range(REPETITIONS))
        for _, group in groups
    ):
        raise ValueError(f"Final figures require trials 0..{REPETITIONS - 1} in each group")

    # Nova mapa prepreči nenamerno prepisovanje obstoječih raziskovalnih izhodov.
    output.mkdir(parents=True, exist_ok=False)
    copied = output / "h1_h2_trials.csv"
    shutil.copy2(source, copied)
    if sha256(copied) != source_hash:
        raise ValueError("Source changed while copying; inspect the input before retrying")

    style = {
        "figure.figsize": (8.0, 5.1),
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": cycler(color=["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7"]),
        "legend.fontsize": 9,
        "legend.title_fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    }
    with plt.rc_context(style):
        summary = summarize_results(output)
        make_plots(summary, output, formats=("png", "pdf", "svg"))

    snapshot = output / "source_snapshot"
    snapshot.mkdir()
    for path in [
        ROOT / "src/bb84/analysis.py",
        ROOT / "src/bb84/experiments.py",
        ROOT / "src/bb84/protocol.py",
        Path(__file__).resolve(),
        ROOT / "pyproject.toml",
        ROOT / "requirements.lock",
        ROOT / "uv.lock",
    ]:
        shutil.copy2(path, snapshot / path.name)

    (output / "README.md").write_text(
        """# Končni grafi za seminarsko nalogo BB84

Grafi izhajajo iz 50.000 shranjenih poskusov: 25 konfiguracij × 2000 ponovitev.
Pri pripravi niso bile izvedene nove kvantne simulacije. Izvirni podatki in grafi
so ostali nedotaknjeni. Kopija izvornih podatkov je `h1_h2_trials.csv`.

Za vključitev v LaTeX uporabimo PDF, za urejanje SVG, za Word ali predstavitev PNG
(300 dpi). PDF in SVG sta vektorska. PNG, PDF in SVG z istim imenom kažejo isto sliko.
Številčne podlage so v `h1_h2_summary.csv`.

## Predlagani opisi slik

1. **h1_tpr_vs_sample** — Vpliv velikosti kontrolnega vzorca na verjetnost zaznave
   pri 20-% prestrezanju in različnih osnovnih QBER. Točke kažejo empirični TPR,
   navpične oznake dvostranske 95-% Wilsonove intervale, črtkane krivulje pa moč
   eksaktnega binomskega testa. α = 0,05, N = 2400, 2000 ponovitev na konfiguracijo.
   Vodoravna os je logaritemska, označene so vse simulirane velikosti vzorca.

2. **h2_tpr_vs_noise** — Vpliv osnovnega QBER na zaznavo pri kontrolnem vzorcu
   m = 300 in različnih deležih prestrezanja. Točke kažejo empirični TPR z 95-%
   Wilsonovimi intervali, črtkane krivulje teoretični TPR. α = 0,05, N = 2400,
   2000 ponovitev na konfiguracijo. Osnovni QBER je λ/2, ne λ.

3. **fpr_vs_sample** — Delež lažnih alarmov brez Eve pri različnih velikostih
   vzorca in osnovnih QBER. Točke kažejo empirični FPR z 95-% Wilsonovimi intervali,
   barvne črtkane krivulje dejanski teoretični FPR, črna pikčasta črta nominalni
   α = 5 %. Diskretni test je konservativen. Vodoravna os je logaritemska.

Intervali so točkovni, ne simultani. Šest kontrolnih vzorcev istega poskusa je
gnezdenih in medsebojno odvisnih. Povezave med točkami služijo berljivosti,
ne dokazujejo monotonosti ali rezultatov pri nesimuliranih nastavitvah.
Zaznavanje odstopanja od modela šuma ne dokazuje varnosti končnega ključa.

## Ponovljivost

Iz korena izvornega repozitorija s pripravljenim okoljem:

```bash
MPLCONFIGDIR=.cache/matplotlib .venv/bin/python scripts/prepare_final_figures.py \\
  --source src/bb84/results/h1_h2_trials.csv \\
  --output-dir results/final-figures-new
```

Izhodna mapa mora biti nova. `provenance.json` vsebuje SHA-256 podatkov in izhodov,
različice trenutnega okolja ter revizijo kode. `source_snapshot/` hrani uporabljeno
kodo in zaklepa odvisnosti; gre za arhivski posnetek, ne samostojen projekt.
Različice so različice **priprave grafov**; prvotni CSV ne beleži zgodovinskega
okolja simulacij. Revizija Git sama ne vključuje še nepotrjenih lokalnih sprememb,
zato je priložen tudi posnetek trenutne kode.
""",
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_csv": str(source),
        "source_sha256": source_hash,
        "trials": len(data),
        "repetitions_per_configuration": REPETITIONS,
        "summary_rows": len(summary),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "figure_generation_packages": {
            dist.metadata["Name"]: dist.version for dist in distributions()
        },
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_tracked_files_modified": subprocess.run(
            ["git", "diff", "HEAD", "--quiet"], cwd=ROOT, check=False
        ).returncode
        != 0,
        "original_simulation_environment": "Not recorded in source CSV",
        "command": (
            ".venv/bin/python scripts/prepare_final_figures.py "
            f"--source {source} --output-dir {output}"
        ),
        "files_sha256": {
            str(path.relative_to(output)): sha256(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    (output / "provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if sha256(source) != source_hash:
        raise ValueError("Source changed during figure preparation")
    print(f"\nKončni grafi (PNG/PDF/SVG): {output}")


if __name__ == "__main__":
    main()
