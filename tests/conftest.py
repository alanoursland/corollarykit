"""Shared test configuration: oracle markers, Hypothesis profiles, time budget."""

from __future__ import annotations

import importlib.util
import os
import time

import pytest
from hypothesis import settings

ORACLE_MODULES = {
    "oracle_sympy": "sympy",
    "oracle_pari": "cypari2",
    "oracle_flint": "flint",
    "oracle_primecount": "primecount",
    "oracle_highs": "highspy",
}

# Under scripts/check.sh a missing oracle is a failure, never a silent skip.
REQUIRE_ORACLES = os.environ.get("COROLLARYKIT_REQUIRE_ORACLES") == "1"

DEFAULT_MARKEXPR = "not slow and not bench"
TIME_BUDGET_SECONDS = float(os.environ.get("COROLLARYKIT_TIME_BUDGET", "60"))

settings.register_profile("dev", max_examples=100)
settings.register_profile("ci", max_examples=200, derandomize=True, print_blob=True)
settings.register_profile("thorough", max_examples=5000, print_blob=True)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


def _importable(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        for marker, module in ORACLE_MODULES.items():
            missing = item.get_closest_marker(marker) and not _importable(module)
            if missing and not REQUIRE_ORACLES:
                item.add_marker(pytest.mark.skip(reason=f"oracle {module} not installed"))


def pytest_runtest_setup(item: pytest.Item) -> None:
    if not REQUIRE_ORACLES:
        return
    for marker, module in ORACLE_MODULES.items():
        if item.get_closest_marker(marker) and not _importable(module):
            pytest.fail(f"oracle {module} missing (COROLLARYKIT_REQUIRE_ORACLES=1)")


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config._ck_start = time.monotonic()  # type: ignore[attr-defined]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    start = getattr(session.config, "_ck_start", None)
    if start is None or session.config.option.markexpr != DEFAULT_MARKEXPR:
        return
    if os.environ.get("COROLLARYKIT_NO_TIME_BUDGET") == "1":
        return
    elapsed = time.monotonic() - start
    if elapsed > TIME_BUDGET_SECONDS:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_line(
                f"default test run took {elapsed:.1f}s, over the {TIME_BUDGET_SECONDS:.0f}s "
                "budget; move slow tests behind @pytest.mark.slow",
                red=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
