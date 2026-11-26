"""Integer helpers: sieves, Jacobi symbol, integer roots, trial division, exact pi(x).

Pure functions on Python ints. No basis, no policy. Every function rejects bool and
non-integers with TypeError.
"""

from __future__ import annotations

import operator
import threading
from bisect import bisect_right
from collections.abc import Iterator
from math import gcd, isqrt

SMALL_PRIMES_CAP = 1 << 24
"""Largest bound small_primes will sieve to. Above it, use sieve_segment."""

_lock = threading.Lock()
_cache_limit = 1
_cache: tuple[int, ...] = ()


def _int(x: object, name: str) -> int:
    if isinstance(x, bool):
        raise TypeError(f"{name} must be an int, not bool")
    try:
        return operator.index(x)  # type: ignore[arg-type]
    except TypeError:
        raise TypeError(f"{name} must be an int, not {type(x).__name__}") from None


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def _zero_stride(flags: bytearray, start: int, step: int) -> None:
    """Set flags[start::step] to 0."""
    if start < len(flags):
        flags[start::step] = bytes(len(range(start, len(flags), step)))


def _odd_sieve(n: int) -> bytearray:
    """s[i] == 1 iff 2i+1 is prime, for 2i+1 <= n (index 0 is 1, not prime)."""
    s = bytearray([1]) * (n // 2 + 1)
    s[0] = 0
    for i in range(1, (isqrt(n) - 1) // 2 + 1):
        if s[i]:
            p = 2 * i + 1
            _zero_stride(s, p * p // 2, p)
    return s


def small_primes(bound: int) -> tuple[int, ...]:
    """All primes <= bound, from a cached sieve. bound must not exceed SMALL_PRIMES_CAP."""
    global _cache, _cache_limit
    bound = _int(bound, "bound")
    if bound < 2:
        return ()
    if bound > SMALL_PRIMES_CAP:
        raise ValueError(f"small_primes is capped at {SMALL_PRIMES_CAP}; use sieve_segment")
    if bound > _cache_limit:
        with _lock:
            if bound > _cache_limit:
                n = min(SMALL_PRIMES_CAP, max(bound, 2 * _cache_limit, 1 << 16))
                s = _odd_sieve(n)
                primes = [2]
                primes.extend(2 * i + 1 for i in range(1, len(s)) if s[i] and 2 * i + 1 <= n)
                _cache = tuple(primes)
                _cache_limit = n
    return _cache[: bisect_right(_cache, bound)]


def sieve_segment(lo: int, hi: int) -> bytearray:
    """Primality flags for the half-open interval (lo, hi]: flags[i] is for n = lo + 1 + i.

    1 means prime. Requires isqrt(hi) <= SMALL_PRIMES_CAP. Memory is hi - lo bytes;
    use iter_segments for long intervals.
    """
    lo, hi = _int(lo, "lo"), _int(hi, "hi")
    if hi < lo:
        raise ValueError("sieve_segment requires hi >= lo")
    n0, length = lo + 1, hi - lo
    flags = bytearray([1]) * length
    for n in range(n0, min(n0 + length, 2)):  # 1, 0 and negatives are not prime
        flags[n - n0] = 0
    if hi < 4:
        return flags
    for p in small_primes(isqrt(hi)):
        start = max(p * p, _ceil_div(n0, p) * p)  # never marks p itself
        _zero_stride(flags, start - n0, p)
    return flags


def iter_segments(lo: int, hi: int, chunk: int = 1 << 20) -> Iterator[tuple[int, int, bytearray]]:
    """Yield (seg_lo, seg_hi, flags) covering (lo, hi] in half-open chunks."""
    lo, hi, chunk = _int(lo, "lo"), _int(hi, "hi"), _int(chunk, "chunk")
    if chunk < 1:
        raise ValueError("chunk must be positive")
    while lo < hi:
        seg_hi = min(hi, lo + chunk)
        yield lo, seg_hi, sieve_segment(lo, seg_hi)
        lo = seg_hi


def progression_sieve(a: int, q: int, j0: int, j1: int, bound: int) -> tuple[bytearray, int]:
    """Sieve v_j = a + j*q for j in [j0, j1) by the primes <= bound.

    flags[j - j0] == 1 means v_j has no prime factor <= bound other than itself; in
    particular every sieving prime that lies in the progression survives. Requires
    q >= 1, 0 <= a < q, gcd(a, q) == 1. Also returns (bound + 1)**2: survivors below
    that value are certainly prime.
    """
    a, q = _int(a, "a"), _int(q, "q")
    j0, j1, bound = _int(j0, "j0"), _int(j1, "j1"), _int(bound, "bound")
    if q < 1 or not 0 <= a < q or gcd(a, q) != 1:
        raise ValueError("progression_sieve requires q >= 1, 0 <= a < q, gcd(a, q) = 1")
    if j1 < j0:
        raise ValueError("progression_sieve requires j1 >= j0")
    if bound < 0:
        raise ValueError("progression_sieve requires bound >= 0")
    flags = bytearray([1]) * (j1 - j0)
    # Values below 2 occur only for the first one or two j.
    j = j0
    while j < j1 and a + j * q < 2:
        flags[j - j0] = 0
        j += 1
    for r in small_primes(bound):
        if q % r == 0:
            continue  # r never divides a + jq, since gcd(a, q) = 1
        j_star = (-a) * pow(q, -1, r) % r  # r | a + jq  iff  j = j_star (mod r)
        _zero_stride(flags, (j_star - j0) % r, r)
        if r >= a and (r - a) % q == 0:  # r itself is in the progression: restore it
            jr = (r - a) // q
            if j0 <= jr < j1:
                flags[jr - j0] = 1
    return flags, (bound + 1) ** 2


def jacobi(a: int, n: int) -> int:
    """Jacobi symbol (a/n) for odd n > 0."""
    a, n = _int(a, "a"), _int(n, "n")
    if n <= 0 or n % 2 == 0:
        raise ValueError("jacobi requires an odd positive n")
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


def iroot(n: int, k: int) -> tuple[int, bool]:
    """(floor(n ** (1/k)), whether that root is exact), for n >= 0 and k >= 1."""
    n, k = _int(n, "n"), _int(k, "k")
    if n < 0 or k < 1:
        raise ValueError("iroot requires n >= 0 and k >= 1")
    if n < 2 or k == 1:
        return n, True
    x = 1 << _ceil_div(n.bit_length(), k)  # x >= true root
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x:
            break
        x = y
    return x, x**k == n


def perfect_power(n: int) -> tuple[int, int] | None:
    """(r, e) with n = r**e and e maximal (so r is not a perfect power), or None. n >= 2."""
    n = _int(n, "n")
    if n < 2:
        raise ValueError("perfect_power requires n >= 2")
    for k in small_primes(n.bit_length()):  # n = t^e is a k-th power iff k | e
        r, exact = iroot(n, k)
        if exact:
            sub = perfect_power(r) if r >= 4 else None
            return (sub[0], k * sub[1]) if sub else (r, k)
    return None


def trial_divide(n: int, bound: int) -> tuple[dict[int, int], int]:
    """Divide out the primes <= bound. Returns ({prime: exponent}, cofactor).

    The cofactor has no prime factor <= bound. If 1 < cofactor < (bound + 1)**2 it is prime.
    """
    n, bound = _int(n, "n"), _int(bound, "bound")
    if n < 1:
        raise ValueError("trial_divide requires n >= 1")
    if bound < 0:
        raise ValueError("trial_divide requires bound >= 0")
    factors: dict[int, int] = {}
    for p in small_primes(bound):
        if p * p > n:
            break
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    if 1 < n <= bound:  # a leftover prime below the bound
        factors[n] = factors.get(n, 0) + 1
        n = 1
    return factors, n


def _odd_segment(lo: int, hi: int) -> int:
    """Number of odd primes in (lo, hi], by an odd-only segmented sieve."""
    first = lo + 1 if (lo + 1) % 2 else lo + 2
    first = max(first, 3)
    if hi < first:
        return 0
    length = (hi - first) // 2 + 1  # index i <-> first + 2i
    flags = bytearray([1]) * length
    for p in small_primes(isqrt(hi))[1:]:  # odd primes
        m = _ceil_div(first, p) * p
        if m % 2 == 0:
            m += p
        start = max(p * p, m)
        _zero_stride(flags, (start - first) // 2, p)
    return flags.count(1)


def prime_count_exact(x: int, *, backend: str = "auto") -> int:
    """pi(x), exactly. Pure Python for now; native backends are wired in with M2."""
    x = _int(x, "x")
    if backend not in ("auto", "python"):
        raise ValueError(f"unknown backend {backend!r}")
    if x < 2:
        return 0
    count = 1  # the prime 2
    chunk = 1 << 22
    lo = 0
    while lo < x:
        hi = min(x, lo + chunk)
        count += _odd_segment(lo, hi)
        lo = hi
    return count


__all__ = [
    "SMALL_PRIMES_CAP",
    "iroot",
    "iter_segments",
    "jacobi",
    "perfect_power",
    "prime_count_exact",
    "progression_sieve",
    "sieve_segment",
    "small_primes",
    "trial_divide",
]
