"""_intmath against deliberately naive reference implementations."""

import random
from math import gcd, isqrt

import pytest
from _data import load_data
from hypothesis import given
from hypothesis import strategies as st

from corollarykit import _intmath as im

# ---------------------------------------------------------------- naive versions


def naive_is_prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, isqrt(n) + 1))


def naive_jacobi(a: int, n: int) -> int:
    result, m, p = 1, n, 3
    while m > 1:
        while m % p == 0:
            x = a % p
            result *= 0 if x == 0 else (1 if pow(x, (p - 1) // 2, p) == 1 else -1)
            m //= p
        p += 2
    return result


def naive_perfect_power(n: int):
    for e in range(n.bit_length(), 1, -1):
        r = round(n ** (1 / e))
        for c in (r - 1, r, r + 1):
            if c >= 2 and c**e == n:
                return c, e
    return None


PRIMES_TO_3000 = [n for n in range(3001) if naive_is_prime(n)]

# -------------------------------------------------------------------- small_primes


def test_small_primes_matches_naive():
    for bound in range(0, 3001, 7):
        assert list(im.small_primes(bound)) == [p for p in PRIMES_TO_3000 if p <= bound]


def test_small_primes_against_generated_data():
    assert list(im.small_primes(99_999)) == [int(x) for x in load_data("primes_below_100000.txt")]


def test_small_primes_cap():
    with pytest.raises(ValueError, match="capped"):
        im.small_primes(im.SMALL_PRIMES_CAP + 1)


def test_small_primes_consistent_across_resieve(monkeypatch):
    monkeypatch.setattr(im, "_cache_limit", 1)
    monkeypatch.setattr(im, "_cache", ())
    first = im.small_primes(100)
    grown = im.small_primes(200_000)
    assert grown[: len(first)] == first
    assert im.small_primes(100) == first


# ------------------------------------------------------------------- sieve_segment


def test_sieve_segment_all_small_windows():
    for lo in range(-3, 300):
        for hi in range(lo, min(lo + 60, 320)):
            flags = im.sieve_segment(lo, hi)
            assert [lo + 1 + i for i, f in enumerate(flags) if f] == [
                n for n in range(lo + 1, hi + 1) if naive_is_prime(n)
            ]


def test_sieve_segment_random_large_windows():
    rng = random.Random(1)
    for _ in range(20):
        lo = rng.randrange(10**9)
        hi = lo + rng.randrange(1, 400)
        flags = im.sieve_segment(lo, hi)
        assert [lo + 1 + i for i, f in enumerate(flags) if f] == [
            n for n in range(lo + 1, hi + 1) if naive_is_prime(n)
        ]


def test_iter_segments_covers_interval():
    got = []
    for seg_lo, _, flags in im.iter_segments(10, 1000, chunk=97):
        got.extend(seg_lo + 1 + i for i, f in enumerate(flags) if f)
    assert got == [p for p in PRIMES_TO_3000 if 10 < p <= 1000]


@pytest.mark.parametrize(("lo", "hi"), [(-10, -3), (-(10**6), -(10**6) + 50), (-5, 0), (-5, 3)])
def test_sieve_segment_negative_windows(lo, hi):
    flags = im.sieve_segment(lo, hi)
    assert [lo + 1 + i for i, f in enumerate(flags) if f] == [
        n for n in range(lo + 1, hi + 1) if naive_is_prime(n)
    ]


def test_sieve_segment_rejects_reversed():
    with pytest.raises(ValueError):
        im.sieve_segment(10, 5)


# --------------------------------------------------------------- progression_sieve


@pytest.mark.parametrize(("a", "q", "answer"), [(2, 3, 2), (3, 4, 3), (5, 6, 5), (0, 1, 2)])
def test_progression_sieve_keeps_sieving_primes(a, q, answer):
    flags, _ = im.progression_sieve(a, q, 0, 50, 100)
    first = next(a + j * q for j, f in enumerate(flags) if f)
    assert first == answer


def test_progression_sieve_matches_naive():
    for q in range(1, 61):
        for a in range(q):
            if gcd(a, q) != 1:
                continue
            for bound in (2, 10, 100):
                for j0 in (0, 3):
                    flags, certain = im.progression_sieve(a, q, j0, j0 + 200, bound)
                    small = [p for p in PRIMES_TO_3000 if p <= bound]
                    for j in range(j0, j0 + 200):
                        v = a + j * q
                        expect = v >= 2 and all(v % r or v == r for r in small)
                        assert flags[j - j0] == expect, (a, q, j, bound)
                        if flags[j - j0] and v < certain:
                            assert naive_is_prime(v)


def test_negative_bounds_are_rejected():
    # A negative bound would make the "certainly prime below (bound+1)^2" rule accept 4.
    with pytest.raises(ValueError, match="bound >= 0"):
        im.progression_sieve(0, 1, 4, 5, -4)
    with pytest.raises(ValueError, match="bound >= 0"):
        im.trial_divide(4, -4)


@pytest.mark.parametrize("bound", [0, 1])
def test_tiny_bounds_keep_the_certainty_rule_sound(bound):
    flags, certain = im.progression_sieve(0, 1, 0, 20, bound)
    for j, f in enumerate(flags):
        if f and j < certain:
            assert naive_is_prime(j)
    for n in range(1, 50):
        _, cof = im.trial_divide(n, bound)
        if 1 < cof < (bound + 1) ** 2:
            assert naive_is_prime(cof)


def test_progression_sieve_validates():
    for args in [(2, 4, 0, 5, 10), (5, 3, 0, 5, 10), (1, 0, 0, 5, 10), (1, 3, 5, 2, 10)]:
        with pytest.raises(ValueError):
            im.progression_sieve(*args)


# -------------------------------------------------------------------------- jacobi


def test_jacobi_matches_naive():
    for n in range(1, 500, 2):
        for a in range(-5, n + 5):
            assert im.jacobi(a, n) == naive_jacobi(a, n), (a, n)


@pytest.mark.parametrize("n", [0, -3, 4, 10])
def test_jacobi_rejects_bad_modulus(n):
    with pytest.raises(ValueError):
        im.jacobi(1, n)


# ------------------------------------------------------------- iroot, perfect_power


def test_iroot_small():
    for n in range(0, 20_000):
        for k in range(1, 6):
            r, exact = im.iroot(n, k)
            assert r**k <= n < (r + 1) ** k
            assert exact == (r**k == n)


@given(st.integers(min_value=2, max_value=10**40), st.integers(min_value=2, max_value=40))
def test_iroot_powers_and_neighbours(r, k):
    n = r**k
    assert im.iroot(n, k) == (r, True)
    assert im.iroot(n - 1, k) == (r - 1, False)
    assert im.iroot(n + 1, k) == (r, False)


def test_perfect_power_matches_naive():
    for n in range(2, 100_000):
        assert im.perfect_power(n) == naive_perfect_power(n), n


@given(st.integers(min_value=2, max_value=10**6), st.integers(min_value=2, max_value=30))
def test_perfect_power_exponent_is_maximal(base, e):
    root = im.perfect_power(base)
    r, f = root if root else (base, 1)
    assert im.perfect_power(base**e) == (r, f * e)


# --------------------------------------------------------------------- trial_divide


def test_trial_divide_small():
    for n in range(1, 100_000, 7):
        for bound in (10, 100):
            factors, cof = im.trial_divide(n, bound)
            product = cof
            for p, e in factors.items():
                assert p <= bound and naive_is_prime(p)
                product *= p**e
            assert product == n
            assert all(cof % p for p in PRIMES_TO_3000 if p <= bound)
            if 1 < cof < (bound + 1) ** 2:
                assert naive_is_prime(cof)


# ---------------------------------------------------------------- prime_count_exact


def test_prime_count_exact_small():
    count = 0
    for x in range(0, 3001):
        if naive_is_prime(x):
            count += 1
        assert im.prime_count_exact(x) == count


@pytest.mark.parametrize(
    ("x", "pi"), [(10**4, 1229), (10**5, 9592), (10**6, 78498), (10**7, 664579)]
)
def test_prime_count_exact_powers_of_ten(x, pi):
    # These values are re-derived by test_prime_count_exact_matches_segments below.
    assert im.prime_count_exact(x) == pi


def test_prime_count_exact_matches_segments():
    rng = random.Random(2)
    for _ in range(10):
        x = rng.randrange(10**6)
        assert im.prime_count_exact(x) == sum(im.sieve_segment(0, x))


@pytest.mark.slow
def test_prime_count_exact_1e8():
    assert im.prime_count_exact(10**8) == 5761455


# ------------------------------------------------------------------------- types

FUNCTIONS = [
    (im.small_primes, 1),
    (im.sieve_segment, 2),
    (im.jacobi, 2),
    (im.iroot, 2),
    (im.perfect_power, 1),
    (im.trial_divide, 2),
    (im.prime_count_exact, 1),
    (im.progression_sieve, 5),
]


@pytest.mark.parametrize(("fn", "arity"), FUNCTIONS, ids=lambda f: getattr(f, "__name__", ""))
@pytest.mark.parametrize("bad", [True, 2.0, "3"])
def test_rejects_non_integers(fn, arity, bad):
    args = [bad] + [5] * (arity - 1)
    with pytest.raises(TypeError):
        fn(*args)
