# `factor_with_phi(n, phi)`

Return the complete prime factorization of n, given φ(n) or any multiple of λ(n), the Carmichael function. Deterministic, with a factorization anyone can check by multiplying it out.

This is mostly of teaching and completeness value. It shows concretely that computing φ is as hard as factoring. Few production callers have φ(n) without already knowing the factors.

## Old implementation

Write m = φ(n) = 2^s · t with t odd. For a base a, compute a^t, a^(2t), …, a^(2^s·t) mod n. If some a^(2^i·t) ≢ ±1 but its square ≡ 1, then gcd(a^(2^i·t) − 1, n) is a nontrivial factor. This is the Miller-Rabin computation with m in place of n − 1.

- **Randomized (unconditional):** for odd n that is not a prime power, a random a splits n with probability ≥ 1/2. Expected O(1) bases per split, each costing O(log n · M(log n)). A complete factorization needs at most log₂ n splits.
- **Deterministic (unconditional):**
  - n = pq is trivial: p + q = n − φ(n) + 1, then solve a quadratic.
  - For general n with three or more prime factors, the known deterministic reductions need GRH: Miller 1976.
- **Prime powers:** detect p^k with an integer k-th root, before or after splitting.

## What changes it

**Basis `miller1976.phi`:** given a multiple m of λ(n), a base a < B splits n, for odd n with at least two distinct prime factors. Miller (1976) proved this under ERH. The bad bases lie in a proper subgroup of (ℤ/nℤ)^×, so Bach's explicit subgroup bound applies:

**Basis `bach1990.subgroup`:** every proper subgroup of (ℤ/nℤ)^× misses some a < 2·(ln n)². This assumes GRH for Dirichlet L-functions (characters mod n), so it is within the claimed scope of Alpöge–Claude (`lean-compiled`, `statement_match = unchecked`).

⚠ To check: that the set of non-splitting bases is contained in a proper subgroup **for every multiple of λ(n)**, not only for m = n − 1. Miller's paper states the φ result. We need to confirm how the explicit Bach constant carries over.

## New implementation

1. Validate n ≥ 2 and m ≥ 1, and check that m is a multiple of λ(n): a^m ≡ 1 must hold for every base tried. A base where it fails proves m is invalid, and we raise `ValueError` with that base as the witness.
2. Strip factors of 2. Handle a perfect power n = r^k by recursing on r.
3. **n = pq shortcut:** if the quadratic x² − (n − m + 1)x + n has integer roots, done.
4. Otherwise try prime bases a = 2, 3, 5, … up to 2·ln²n. Prime bases suffice, since a subgroup containing every prime below B contains every integer below B. On a split n = d·(n/d), recurse on both parts with the **same m**, which is a multiple of λ of every divisor.
5. **Termination:** a part that no base below the ceiling splits is a prime or a prime power, under the basis. Confirm with the primality policy, then return it.
6. If the ceiling is passed on a composite that isn't a prime power, raise `InconsistencyError`.

**Strict policy:** randomized bases with an iteration budget, plus the n = pq shortcut. The output is still a checkable factorization. Only the guaranteed running time is lost.

**Certificate:** the list of prime factors, with exponents. Multiplying them back gives n (`full` for the product), and each factor carries a primality certificate under the active policy.

**Complexity:**
- Deterministic: at most log₂ n splits × O(log² n / log log n) bases × O(log n · M(log n)), so **Õ(log⁴ n)**.
- Before, this was expected Õ(log² n) with randomness, or deterministic only for n = pq.
- As with Miller's test, measured speed should be the same, since a = 2 or 3 almost always splits. The change is the guarantee.

## Testing

- Carmichael numbers and products of many primes, with m = φ(n), m = λ(n) and m = k·λ(n).
- Cross-check against `sympy.factorint` on random n up to 200 bits built from known primes.
- Invalid m (not a multiple of λ(n)) must be rejected, with a witness.
