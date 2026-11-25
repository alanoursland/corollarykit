"""Claimed strongly polynomial LP solver (research stage).

Plan: planning/strongly_polynomial_lp.md
"""

from __future__ import annotations

from typing import Any


def solve_lp_exact(A: Any, b: Any, c: Any) -> Any:
    """max c^T x subject to Ax <= b, returning a checkable certificate."""
    raise NotImplementedError("research stage; see planning/strongly_polynomial_lp.md")
