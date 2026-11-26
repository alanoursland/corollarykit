"""Basis selection and rigorous search ceilings.

Ceiling formulas are declared in bases.toml as a named kind with exact rational
parameters. This module implements the kinds. Every kind is increasing in its
inputs, and ``ceiling_upper`` returns an integer that is never below the true
value: a ceiling that is too big only makes a search run longer, one that is too
small would be a bug.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from fractions import Fraction
from math import isqrt

from corollarykit.registry import Basis, Policy, get_basis, list_bases

LN2_UP = Fraction(69314718056, 10**11)
"""A rational upper bound on ln 2 = 0.693147180559945..."""

_TERMS = 8
_ROUND = 1 << 64


def _round_up(x: Fraction) -> Fraction:
    """Smallest multiple of 2^-64 that is >= x, keeping denominators small."""
    return Fraction(-((-x.numerator * _ROUND) // x.denominator), _ROUND)


def ln1p_upper(t: Fraction) -> Fraction:
    """Rational upper bound on ln(1 + t) for 0 <= t < 1.

    ln(1+t) = 2 artanh(u) = 2 sum u^(2i+1)/(2i+1), with u = t/(2+t) <= 1/3. The first
    _TERMS terms are summed and the tail is bounded by a geometric series:
    tail <= 2 u^(2K+1) / ((2K+1)(1 - u^2)). Everything is rounded up, and u is rounded
    up first, which is safe because the bound increases with u.
    """
    if not 0 <= t < 1:
        raise ValueError("ln1p_upper requires 0 <= t < 1")
    u = _round_up(t / (2 + t))
    total = Fraction(0)
    power = u
    u2 = _round_up(u * u)
    for i in range(_TERMS):
        total += _round_up(Fraction(2, 2 * i + 1) * power)
        power = _round_up(power * u2)
    # `power` is now >= u^(2*_TERMS+1)
    tail = _round_up(2 * power / ((2 * _TERMS + 1) * (1 - u2)))
    return total + tail


def ln_upper(n: int) -> Fraction:
    """A rational U >= ln n, for integers n >= 1. Overshoot is below about 1e-9."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("ln_upper requires an integer n >= 1")
    b = n.bit_length()  # 2^(b-1) <= n < 2^b
    base = 1 << (b - 1)
    return (b - 1) * LN2_UP + ln1p_upper(Fraction(n - base, base))


def sqrt_upper(x: int) -> int:
    """ceil(sqrt(x)) for x >= 0."""
    if x < 0:
        raise ValueError("sqrt_upper requires x >= 0")
    return isqrt(x - 1) + 1 if x > 0 else 0


def sqrt_upper_fraction(x: int) -> Fraction:
    """A rational U >= sqrt(x) with U - sqrt(x) <= 2^-64, for x >= 0."""
    if x < 0:
        raise ValueError("sqrt_upper_fraction requires x >= 0")
    s = isqrt(x << 128)  # s <= 2^64 sqrt(x) < s + 1
    return Fraction(s if s * s == x << 128 else s + 1, _ROUND)


def _log_pow(p: Mapping[str, Fraction], *, n: int) -> Fraction:
    return p["c"] * ln_upper(n) ** int(p["k"])


def _sqrt_log(p: Mapping[str, Fraction], *, x: int) -> Fraction:
    return p["c"] * sqrt_upper_fraction(x) * ln_upper(x)


def _qlogq_sq(p: Mapping[str, Fraction], *, q: int) -> Fraction:
    return p["c"] * (q * ln_upper(q)) ** 2


def _phiqlogq_sq(p: Mapping[str, Fraction], *, q: int, phi: int | None = None) -> Fraction:
    if q < 2:
        raise ValueError("phiqlogq_sq requires q >= 2")
    # phi(q) <= q - 1 for q >= 2, so q - 1 gives a valid upper bound when phi is unknown.
    if phi is not None and not 1 <= phi <= q - 1:
        raise ValueError("phi must satisfy 1 <= phi <= q - 1")
    return p["c"] * ((phi if phi is not None else q - 1) * ln_upper(q)) ** 2


CEILING_KINDS: dict[str, tuple[Callable[..., Fraction], frozenset[str]]] = {
    "log_pow": (_log_pow, frozenset({"c", "k"})),  # c (ln n)^k
    "sqrt_log": (_sqrt_log, frozenset({"c"})),  # c sqrt(x) ln x
    "qlogq_sq": (_qlogq_sq, frozenset({"c"})),  # c (q ln q)^2
    "phiqlogq_sq": (_phiqlogq_sq, frozenset({"c"})),  # c (phi(q) ln q)^2
}


def validate_registry_ceilings(bases: Iterable[Basis] | None = None) -> None:
    """Every ceiling in the registry must name a known kind with exactly its parameters."""
    for b in list_bases() if bases is None else bases:
        if b.ceiling is None:
            continue
        if b.ceiling.kind not in CEILING_KINDS:
            raise ValueError(f"basis {b.id!r}: unknown ceiling kind {b.ceiling.kind!r}")
        needed = CEILING_KINDS[b.ceiling.kind][1]
        if set(b.ceiling.params) != needed:
            raise ValueError(
                f"basis {b.id!r}: ceiling {b.ceiling.kind!r} needs parameters {sorted(needed)}"
            )
        if "k" in needed and b.ceiling.params["k"].denominator != 1:
            raise ValueError(f"basis {b.id!r}: exponent k must be an integer")
        if b.ceiling.params["c"] <= 0:
            raise ValueError(f"basis {b.id!r}: constant c must be positive")


def ceiling_upper(basis: Basis | str, **inputs: int | None) -> int:
    """An integer >= the basis's ceiling formula evaluated at ``inputs``."""
    b = get_basis(basis) if isinstance(basis, str) else basis
    if b.ceiling is None:
        raise ValueError(f"basis {b.id!r} has no ceiling")
    fn, _ = CEILING_KINDS[b.ceiling.kind]
    value = fn(b.ceiling.params, **inputs)
    return -((-value.numerator) // value.denominator)


def select_bases(policy: Policy, candidate_ids: Iterable[str], x: int) -> list[Basis]:
    """Bases among ``candidate_ids`` that ``policy`` accepts and whose numeric domain
    contains x, in the caller's preference order. Preconditions in ``requires`` are the
    caller's responsibility. An unknown id raises KeyError: that is a bug, not policy."""
    out = []
    for bid in candidate_ids:
        b = get_basis(bid)
        if policy.accepts(b) and b.domain.contains(x):
            out.append(b)
    return out


validate_registry_ceilings()

__all__ = [
    "CEILING_KINDS",
    "LN2_UP",
    "ceiling_upper",
    "ln1p_upper",
    "ln_upper",
    "select_bases",
    "sqrt_upper",
    "sqrt_upper_fraction",
    "validate_registry_ceilings",
]
