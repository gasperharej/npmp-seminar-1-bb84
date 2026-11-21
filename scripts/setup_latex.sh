#!/usr/bin/env bash
# Lokalni TeX Live (TinyTeX); ne potrebuje sudo in ne spreminja profila lupine.
set -euo pipefail

bb84_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
bb84_tools="$bb84_root/.tools"
bb84_tex_bin="$bb84_tools/.TinyTeX/bin/x86_64-linux"

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    printf '%s\n' 'Ta lokalni namestitveni skript je za Linux x86_64.' >&2
    exit 1
fi
mkdir -p -- "$bb84_tools"
if [[ ! -x "$bb84_tex_bin/tlmgr" ]]; then
    bb84_archive="$bb84_tools/TinyTeX-1-linux-x86_64.tar.xz"
    curl --fail --location --silent --show-error --retry 2 \
        --connect-timeout 20 --max-time 600 \
        --output "$bb84_archive" \
        https://github.com/rstudio/tinytex-releases/releases/download/daily/TinyTeX-1-linux-x86_64.tar.xz
    tar --extract --xz --no-same-owner --file "$bb84_archive" --directory "$bb84_tools"
fi
export PATH="$bb84_tex_bin:$PATH"
"$bb84_tex_bin/tlmgr" install \
    babel-slovenian hyphen-slovenian psnfss times helvetic courier \
    physics quantikz caption float booktabs multirow tools siunitx pgf \
    listings footmisc comment csquotes import natbib xurl hyperref \
    amsmath amsfonts mathtools rsfs latexmk makeindex chktex \
    xargs environ trimspaces tikz-cd etoolbox xstring
"$bb84_tex_bin/pdflatex" --version
"$bb84_tex_bin/latexmk" -version
printf '%s\n' 'Okolje je pripravljeno. Prevod: bash scripts/build_report.sh'
