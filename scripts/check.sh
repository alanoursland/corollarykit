#!/usr/bin/env bash
# Local replacement for CI. This project runs no GitHub Actions.
#
# Builds the wheel and sdist, checks the package metadata, installs the wheel into a
# fresh virtual environment, and runs lint, type checks and the tests against the
# installed wheel (never the source tree). Missing oracle libraries fail the run.
#
#   scripts/check.sh                     # quick: default tests on python3
#   scripts/check.sh --full              # also slow tests, thorough property tests
#   scripts/check.sh --python python3.11 --python python3.13
#
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)
FULL=0
PYTHONS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --full) FULL=1 ;;
    --python) shift; PYTHONS+=("$1") ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
[ ${#PYTHONS[@]} -eq 0 ] && PYTHONS=(python3)

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

for PY in "${PYTHONS[@]}"; do
  echo "==> $PY ($("$PY" --version))"
  VENV="$WORK/venv-$(basename "$PY")"
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q build twine ruff mypy

  rm -rf "$WORK/dist"
  "$VENV/bin/python" -m build -q -o "$WORK/dist" >/dev/null
  "$VENV/bin/twine" check --strict "$WORK"/dist/*
  "$VENV/bin/pip" install -q "$(ls "$WORK"/dist/*.whl)[test,arb,oracles,fast]"

  "$VENV/bin/ruff" check "$ROOT"
  "$VENV/bin/ruff" format --check "$ROOT"
  (cd "$ROOT" && "$VENV/bin/mypy")
  (cd "$ROOT" && "$VENV/bin/python" tests/data/regen.py --check)

  export COROLLARYKIT_REQUIRE_ORACLES=1
  if [ "$FULL" -eq 1 ]; then
    (cd "$ROOT" && HYPOTHESIS_PROFILE=thorough "$VENV/bin/pytest" -m "slow or not slow")
  else
    (cd "$ROOT" && HYPOTHESIS_PROFILE=ci "$VENV/bin/pytest")
  fi
done
echo "==> all checks passed"
