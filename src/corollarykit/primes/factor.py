"""Factoring given phi(n) or a multiple of lambda(n).

Plan: planning/factor_with_phi.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def factor_with_phi(n: int, phi: int, *, policy: Policy | None = None) -> Any:
    """Complete factorization of n, given phi(n) or any multiple of lambda(n)."""
    raise NotImplementedError("see planning/factor_with_phi.md")
