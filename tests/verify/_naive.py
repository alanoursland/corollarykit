"""Deliberately simple arithmetic, sharing no code with corollarykit."""

from __future__ import annotations


def powmod(b: int, e: int, m: int) -> int:
    """Square-and-multiply, written out (not the built-in three-argument pow)."""
    if m < 1 or e < 0:
        raise ValueError("powmod requires m >= 1 and e >= 0")
    result = 1 % m
    b %= m
    while e:
        if e & 1:
            result = result * b % m
        b = b * b % m
        e >>= 1
    return result


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def is_prime_small(n: int) -> bool:
    """Trial division by 2 and odd d <= sqrt(n). Only for n < 10**14."""
    if n >= 10**14:
        raise ValueError("is_prime_small is limited to n < 10**14")
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def euler_criterion(a: int, p: int) -> int:
    """Legendre symbol (a/p) for an odd prime p, as 0, 1 or -1."""
    r = powmod(a, (p - 1) // 2, p)
    if r == 0:
        return 0
    return 1 if r == 1 else -1


def primes_upto(n: int) -> list[int]:
    """List-based sieve of Eratosthenes."""
    if n < 2:
        return []
    is_p = [True] * (n + 1)
    is_p[0] = is_p[1] = False
    i = 2
    while i * i <= n:
        if is_p[i]:
            for j in range(i * i, n + 1, i):
                is_p[j] = False
        i += 1
    return [i for i in range(n + 1) if is_p[i]]
