"""The test infrastructure itself: time budget hook."""

import os
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).parent


def _run_pytest(env_extra, target):
    env = {**os.environ, **env_extra}
    env.pop("PYTEST_ADDOPTS", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TESTS / target)],
        capture_output=True,
        text=True,
        env=env,
        cwd=TESTS.parent,
    )


def test_time_budget_fails_the_run():
    out = _run_pytest({"COROLLARYKIT_TIME_BUDGET": "0.000001"}, "test_verify_naive.py")
    assert out.returncode == 1, out.stdout
    assert "over the" in out.stdout


def test_time_budget_can_be_disabled():
    out = _run_pytest(
        {"COROLLARYKIT_TIME_BUDGET": "0.000001", "COROLLARYKIT_NO_TIME_BUDGET": "1"},
        "test_verify_naive.py",
    )
    assert out.returncode == 0, out.stdout
