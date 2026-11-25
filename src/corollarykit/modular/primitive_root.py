"""Least primitive root modulo a prime.

Plan: planning/primitive_root.md
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from corollarykit.registry import Policy


def primitive_root(
    p: int,
    factors: Mapping[int, int] | None = None,
    *,
    policy: Policy | None = None,
    certificate: str = "membership",
) -> Any:
    """Least primitive root mod p, given (optionally) the factorization of p - 1."""
    raise NotImplementedError("see planning/primitive_root.md")
