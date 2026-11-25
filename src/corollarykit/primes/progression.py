"""Least prime in an arithmetic progression.

Plan: planning/least_prime_in_progression.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def least_prime_in_progression(
    a: int, q: int, *, policy: Policy | None = None, certificate: str = "membership"
) -> Any:
    """Least prime p = a (mod q), gcd(a, q) = 1."""
    raise NotImplementedError("see planning/least_prime_in_progression.md")
