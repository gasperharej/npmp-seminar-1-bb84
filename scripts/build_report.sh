#!/usr/bin/env bash
# Prevede lokalni osnutek v report/build/editor.pdf.
set -euo pipefail

bb84_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
bb84_tex_bin="$bb84_root/.tools/.TinyTeX/bin/x86_64-linux"
if [[ -x "$bb84_tex_bin/latexmk" ]]; then
    export PATH="$bb84_tex_bin:$PATH"
fi
if ! command -v latexmk >/dev/null 2>&1; then
    printf '%s\n' 'Najprej izvedite: bash scripts/setup_latex.sh' >&2
    exit 1
fi
cd -- "$bb84_root/report"
exec latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
    -synctex=1 -outdir=build "$@" editor.tex
