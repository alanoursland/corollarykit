# Testing: `nth_prime_bounds(n)`, `nth_prime(n)`

Plan: [../nth_prime_bounds.md](../nth_prime_bounds.md)

## 1. Reference values

- p_(10^k) for k = 1…24 (OEIS A006988): check lo ≤ p ≤ hi. `nth_prime` is exact for k ≤ 10 in the fast tier and k ≤ 13 in a full run with `primecount`.
- The first 10⁵ primes from a sieve, compared exactly.

## 2. Oracle comparison

- `sympy.prime(n)` for random n ≤ 10⁶ (`oracle_sympy`).
- `primecount.nth_prime` for random n ≤ 10¹² (full run).

## 3. Properties

- lo ≤ p_n ≤ hi for random n ≤ 10⁷ under both policies.
- **Bracket monotonicity:** under `ACCEPT_RH_ALPOGE` the bracket is contained in the classical Dusart bracket. Each side keeps its classical endpoint unless a tighter one is proven.
- Consistency with `prime_count_interval`: π(lo − 1) < n ≤ π(hi), checked with exact π.

## 4. Edge cases

- n ∈ {1, 2, 3, 4, 5, 6}, below Dusart's domains: p₁ = 2, p₂ = 3, and so on.
- **The half-open sieve window:** n = 2 with a forced bracket [2, 3] must return 3. In general, force brackets with `lo` prime and π(lo) = n − 1, and with π(lo) = n, which returns `lo`.
- n = 0, a negative n, a float, a bool: all rejected.
- An injected bracket where `lo` is composite and π(lo) = n must raise an assertion error. That state is impossible with correct bounds.

## 5. Bases and policy

- n = 688 382 versus 688 383, the Dusart upper domain ⚠.
- An RH predicate that never crosses inside the classical bracket (forced with a fake basis): the result falls back to the classical endpoint and reports the classical basis.
- An Arb comparison that can't be decided at the current precision: bisection must stop and keep the last proven endpoint, without guessing.

## 6. Certificates

- `nth_prime_bounds`: the verifier checks the endpoints against `prime_count_interval`'s verifier.
- `nth_prime` returns p with a certificate: exact π(lo) (`full` by recomputation), the sieved window, and the count. The verifier recomputes π(lo) independently and counts primes in (lo, p].

## 7. Failure paths

- A fake basis giving a bracket that excludes p_n must be caught by the exact sieve and raise `InconsistencyError`.

## 8. Performance

- `nth_prime(10⁸)` with and without `primecount`.
- Report sieve work (window length) for RH versus classical brackets. This is the measured gain the plan claims.
