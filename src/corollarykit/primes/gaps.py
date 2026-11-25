"""Prime search with proven ceilings.

Plan: planning/next_prime.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def next_prime(x: int, *, policy: Policy | None = None) -> Any:
    """Least prime > x."""
    raise NotImplementedError("see planning/next_prime.md")


def prime_exists_between(a: int, b: int, *, policy: Policy | None = None) -> Any:
    """Decide whether (a, b] contains a prime, by theorem where possible."""
    raise NotImplementedError("see planning/next_prime.md")
