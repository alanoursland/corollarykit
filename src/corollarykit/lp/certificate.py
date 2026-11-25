"""Exact checker for standard-form LP certificates.

Spec: planning/specs/lp_certificate_checker.md
"""

from __future__ import annotations

from typing import Any


def check_lp_certificate(problem: Any, cert: Any, *, max_failures: int = 10) -> Any:
    """Check an Optimal / Infeasible / Unbounded certificate for min c^T x, Ax = b, x >= 0."""
    raise NotImplementedError("see planning/specs/lp_certificate_checker.md")
