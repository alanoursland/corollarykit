"""Deterministic square and r-th roots modulo a prime.

Plan: planning/sqrt_mod_prime.md
"""

from __future__ import annotations

from typing import Any

from corollarykit.registry import Policy


def sqrt_mod_prime(a: int, p: int, *, policy: Policy | None = None) -> Any:
    """Root(x) with x*x = a (mod p), or NoRoot(certificate)."""
    raise NotImplementedError("see planning/sqrt_mod_prime.md")


def nth_root_mod_prime(a: int, r: int, p: int, *, policy: Policy | None = None) -> Any:
    """Root(x) with x**r = a (mod p), or NoRoot(certificate)."""
    raise NotImplementedError("see planning/sqrt_mod_prime.md")
