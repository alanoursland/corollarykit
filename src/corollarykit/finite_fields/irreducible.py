"""Deterministic irreducible polynomials over F_p.

Plan: planning/irreducible_polynomial.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def irreducible_polynomial(p: int, d: int, *, policy: Policy | None = None) -> Any:
    """Monic irreducible polynomial of degree d over F_p, with an irreducibility certificate."""
    raise NotImplementedError("see planning/irreducible_polynomial.md")
