"""Deterministic Miller primality testing.

Plan: planning/is_prime_miller.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def is_prime_miller(n: int, *, policy: Policy | None = None) -> Any:
    """Prime(...) or Composite(witness=...), labeled with the basis used."""
    raise NotImplementedError("see planning/is_prime_miller.md")
