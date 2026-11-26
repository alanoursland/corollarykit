# Testing: `prime_count_interval(x)`

Spec: [../specs/prime_count_interval.md](../specs/prime_count_interval.md). The analytic tests force `exact_limit=0`.

## 1. Reference values

- π(10^k) for k = 1…29 (OEIS A006880), stored in `tests/data/pi_powers_of_ten.txt`. Check lo ≤ π ≤ hi under both policies.
- Exact values at non-round points: π(2^k) for k ≤ 80 (published tables, or `primecount` in the nightly run).

## 2. Oracle comparison

- **Exact branch:** the pure-Python sieve against `primecount` (`oracle_primecount`) for 10⁴ random x ≤ 10⁸, plus every x in [0, 10⁵].
- **li evaluation:** Arb `li(x)` against `mpmath.li` at twice the precision, for 10³ random x up to 10³⁰⁰. The mpmath value must lie inside the Arb ball.

## 3. Properties

For x ≤ 10⁸ the exact π is known by sieving, and the analytic interval must contain it:
- lo ≤ π(x) ≤ hi for random x in [2657, 10⁸] and both policies.
- lo ≤ hi always.
- Rounding is outward, at every precision: lowering `prec_bits` must never shrink [lo, hi].
- Monotone envelope: for x < y, π(x) ≤ π(y) means `hi(y) ≥ lo(x)` must hold.

## 4. Edge cases

- x ∈ {−5, 0, 1, 2, 3}, and x a float (`TypeError`).
- `bool` input must be rejected. `True` is an int in Python, so check this explicitly.
- x exactly at `exact_limit` and one past it.
- Very large x near the supported cap 2^(2^20): finishes within budget, and the endpoints are integers.
- li must be the principal value: li(2) ≈ 1.04516. An offset Li would give 0 at 2.

## 5. Bases and policy

- Basis switching at x = 2656 and 2657 (Schoenfeld); 88 788 and 88 789 (Dusart lower bound, ⚠ domain); 2 953 652 286 and 2 953 652 287 (Dusart upper bound); 16 and 17 (Rosser–Schoenfeld lower bound).
- Under `DEFAULT`, `schoenfeld1976` never appears in the result.
- Under `ACCEPT_RH_ALPOGE` with x ≥ 10¹², it is the narrower basis and must be reported on both endpoints.
- `lo_basis` and `hi_basis` can differ. Construct an x where they do.

## 6. Certificates

- `scope="full"` (exact): `tests/verify/` recomputes π(x) with an independent sieve.
- `scope="basis"`: the verifier re-evaluates the named formula with `mpmath` interval arithmetic (not Arb) and checks outward rounding. This is the independent route for the analytic branch.

## 7. Failure paths

- A fake registry basis claiming |π − li| < 1 must trigger `InconsistencyError` that names both bases.

## 8. Performance

- Exact branch: π(10⁸) ≤ 1 s in pure Python. This test fixes the default `exact_limit`.
- Analytic branch: x = 10¹⁰, 10¹⁰⁰ and 10¹⁰⁰⁰ under 10 ms each. Record the times; a regression of more than 2× fails the nightly run.
