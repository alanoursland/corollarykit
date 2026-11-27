#!/usr/bin/env bash
# Mutation testing of the trusted LP checker, run by hand (see planning/implementation/m1.md).
#
# mutmut mutates the source, but the normal tests import the installed wheel, so this
# uses a separate venv with an editable install. Configuration is in [tool.mutmut] in
# pyproject.toml. Exit criterion for M1: no surviving mutants.
#
#   scripts/mutmut.sh            # run, then list survivors
#   scripts/mutmut.sh --python python3.12
set -euo pipefail

cd "$(dirname "$0")/.."
PY=python3
if [ "${1:-}" = "--python" ]; then PY="$2"; fi

VENV=$(mktemp -d)/venv
trap 'rm -rf "$(dirname "$VENV")" mutants' EXIT
"$PY" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -e ".[test,oracles]" gmpy2 "mutmut==3.8.1"

rm -rf mutants
"$VENV/bin/mutmut" run --max-children "$(nproc 2>/dev/null || echo 2)" >/dev/null 2>&1 || true
survivors=$("$VENV/bin/mutmut" results 2>/dev/null | grep -c survived || true)
"$VENV/bin/mutmut" results 2>/dev/null | grep -v killed || true
echo "==> surviving mutants: $survivors"
[ "$survivors" -eq 0 ]
