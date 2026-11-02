#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$PWD/.cache/pip}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"

if [[ ! -e .venv ]]; then
    bb84_python="${BB84_PYTHON:-}"
    if [[ -z "$bb84_python" ]]; then
        for candidate in python3.12 python3.11 python3.13; do
            if command -v "$candidate" >/dev/null 2>&1; then
                bb84_python="$candidate"
                break
            fi
        done
    fi
    if [[ -z "$bb84_python" ]]; then
        printf '%s\n' 'Potrebujete Python 3.12 (ali 3.11/3.13); nastavite BB84_PYTHON.' >&2
        exit 1
    fi
    "$bb84_python" -m venv .venv
fi

if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' '.venv obstaja, vendar nima Python interpreterja; preverite jo ročno.' >&2
    exit 1
fi

.venv/bin/python - <<'PY'
import sys
if not (3, 11) <= sys.version_info[:2] < (3, 14):
    raise SystemExit('Projekt podpira Python 3.11–3.13; priporočena je različica 3.12.')
if sys.prefix == sys.base_prefix:
    raise SystemExit('Interpreter ni v navideznem okolju.')
print(f'Python: {sys.version.split()[0]} ({sys.executable})')
PY

# All third-party dependencies, including the editable build backend, are locked.
.venv/bin/python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pip check

if [[ ! -e .env ]]; then
    cp -- .env.example .env
fi

.venv/bin/python - <<'PY'
import importlib
from importlib.metadata import version

for package in ('bb84-seminar', 'qiskit', 'qiskit-aer', 'numpy', 'pandas', 'matplotlib',
                'scipy', 'pytest', 'ruff'):
    module = {'bb84-seminar': 'bb84', 'qiskit-aer': 'qiskit_aer'}.get(package, package)
    importlib.import_module(module)
    print(f'{package}: {version(package)}')
print('Uvozi paketov so uspešni; paket bb84 je prazen.')
PY

printf '%s\n' 'Okolje je pripravljeno. Preglejte .envrc in enkrat izvedite: direnv allow .'
