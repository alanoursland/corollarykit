"""Rigorous intervals for pi(x) and p_n.

Spec: planning/specs/prime_count_interval.md
Plan: planning/nth_prime_bounds.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def prime_count_interval(
    x: int, *, policy: Policy | None = None, exact_limit: int | None = None
) -> Any:
    """Integers lo <= pi(x) <= hi, each endpoint labeled with the basis that produced it."""
    raise NotImplementedError("see planning/specs/prime_count_interval.md")


def nth_prime_bounds(n: int, *, policy: Policy | None = None) -> Any:
    """Integers lo <= p_n <= hi."""
    raise NotImplementedError("see planning/nth_prime_bounds.md")


def nth_prime(n: int, *, policy: Policy | None = None) -> int:
    """The exact n-th prime, sieving only (lo, hi]."""
    raise NotImplementedError("see planning/nth_prime_bounds.md")
