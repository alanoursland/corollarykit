# Spec: `prime_count_interval` (v1)

This spec also sets the pattern for the other number-theory APIs. For each policy it gives:
1. the exact theorem and input range;
2. the computation it enables;
3. the fallback;
4. what an independent verifier can establish.

## API

```python
def prime_count_interval(x: int, *, policy: Policy | None = None,
                         exact_limit: int | None = None) -> PrimeCountInterval
```

- `x` is taken through `operator.index`, so ints and int-likes are accepted; a `float` raises `TypeError`. If x < 2, the result is `lo = hi = 0`. The supported range is 0 ≤ x < 2^(2^20), a cap on precision and time that can be configured.
- `policy` defaults to the library default (below).
- `exact_limit` overrides the exact-count cutoff. **Tests use `exact_limit=0` to force the analytic branch.**

```python
@dataclass(frozen=True)
class PrimeCountInterval:
    x: int
    lo: int
    hi: int
    lo_basis: str        # id of the basis that produced lo
    hi_basis: str        # id of the basis that produced hi; can differ from lo_basis
    method: str          # "exact" | "analytic"
    prec_bits: int | None
    scope: str           # "full" (exact) | "basis" (analytic)
```

## Bases

The constants marked ⚠ must be copied from the cited source and checked against it before merging, through the registry's `statement` field. Do not use these numbers from memory.

| id | Statement | Domain | Hypothesis | Status |
|---|---|---|---|---|
| `exact` | π(x) computed by sieve or `primecount` | x ≤ exact_limit | none | `classical` (trusted code) |
| `rosser_schoenfeld1962.lower` | π(x) > x/ln x | x ≥ 17 | none | `classical` |
| `rosser_schoenfeld1962.upper` | π(x) < 1.25506·x/ln x ⚠ | x > 1 | none | `classical` |
| `dusart2010.lower` | π(x) ≥ x/ln x·(1 + 1/ln x + 2/ln²x) ⚠ | x ≥ 88 789 ⚠ | none | `classical` |
| `dusart2010.upper` | π(x) ≤ x/ln x·(1 + 1/ln x + 2.334/ln²x) ⚠ | x ≥ 2 953 652 287 ⚠ | none | `classical` |
| `schoenfeld1976` | \|π(x) − li(x)\| < √x·ln x/(8π), where **li is the principal value ∫₀ˣ dt/ln t, not the offset Li** | x ≥ 2657 | RH | `lean-compiled`, `statement_match = checked` (Lean FRO / Mathlib, 2026-11-21) |

**Policies:**
- `default`: accepts `classical` only. The RH proof is `lean-compiled` (statement matched, no human audit yet), so `schoenfeld1976` is **off by default**.
- `accept_rh_alpoge`: `default` plus `schoenfeld1976`, enabled explicitly.
- `strict`: the same as `default` here. It differs from `default` only once a `peer-verified` basis exists.

## Computation

1. If x < 2, return (0, 0), with `method="exact"`.
2. **Exact branch:** if x ≤ exact_limit, return `lo = hi = π(x)` from the exact backend, with `scope="full"`.
   - The default limit is the largest x the backend finishes in **≤ 1 s** on the maintainer's reference machine (recorded with the measurement).
   - Measured for the pure-Python odd-only `bytearray` sieve: π(10⁸) = 5 761 455 in 0.66 s, using about 50 MB.
   - So the pure-Python default is **10⁸**. With `primecount` installed the default is **10¹⁶**, to be benchmarked.
3. **Analytic branch:** for each enabled basis whose domain contains x, compute a rigorous interval [Lᵦ, Uᵦ] for π(x).
   - **Arithmetic:** use Arb balls from `python-flint` (≥ 0.9.0 has `arb.li()` with `offset=False` giving principal-value li).
   - **Precision:** prec = bit_length(x)/2 + 64. Then the ball radius for li(x) is about √x·2⁻⁶⁴, negligible next to the RH width. Checked: x = 10¹⁰⁰ at 200 bits gives li(x) = 4.36197…·10⁹⁷ ± 4·10⁴⁰, against a width of 1.8·10⁵¹.
   - **Endpoints:**
     - `schoenfeld1976`: Lᵦ = ⌈lower(li(x) − w)⌉ and Uᵦ = ⌊upper(li(x) + w)⌋, with w = √x·ln x/(8π) computed as a ball.
     - Dusart and Rosser–Schoenfeld: evaluate the formula as a ball, then round outward the same way.
   - **Outward rounding of the ball endpoints is always valid**, whatever the precision. Precision affects only how tight the result is, so there is no undecidable comparison and no retry loop. If an endpoint's ball radius exceeds 1, double the precision once, for tightness only.
4. **Intersect:** take `lo = max Lᵦ` and `hi = min Uᵦ`, recording which basis gave each.
   - If lo > hi, raise `InconsistencyError` naming both bases. That means a bound is false, its statement was transcribed wrong, or there is a bug.
   - The fallback for x with no lower-bound basis cannot arise for x > exact_limit ≥ 17, since Rosser–Schoenfeld covers x ≥ 17. If exact_limit < 17 and no basis applies to an endpoint, use the trivial bounds lo = 0 and hi = x − 1.

## Complexity

- **Exact branch:** O(x log log x) time and O(x) memory for the pure-Python sieve. This is bounded by the 1-second cutoff.
- **Analytic branch:** O(M(P)·log P) for li at P = O(log x) bits, so **O(polylog x)**. Target: under 10 ms up to x = 10¹⁰⁰⁰. Benchmark it.

## What an independent verifier can establish

| method | scope | Verifier needs | Verifier establishes |
|---|---|---|---|
| exact | `full` | recompute π(x) with a different backend, such as `primecount` or a separate sieve | the exact count, with no basis |
| analytic, classical bases only | `basis` (classical) | re-evaluate the named formula with independent interval arithmetic (for example `mpmath` with an explicit error bound) and check the outward rounding | lo ≤ π(x) ≤ hi, given the cited classical theorems |
| analytic with `schoenfeld1976` | `basis` (RH) | as above | lo ≤ π(x) ≤ hi **if RH holds**. The result names the basis so the caller knows exactly which assumption the endpoint rests on |

## Tests

All analytic tests force `exact_limit=0`.

1. **Containment:** for random x in [2657, 10⁸], plus x = 10^k for k ≤ 29 (OEIS A006880), check lo ≤ π(x) ≤ hi under both `default` and `accept_rh_alpoge`.
2. **Basis switching:**
   - At x = 2656, `schoenfeld1976` must not appear in the result. At 2657 it may.
   - At x = 88 788 versus 88 789 (⚠ domain), the `dusart2010.lower` entry turns on.
   - Check that `lo_basis` and `hi_basis` name a basis whose domain contains x.
3. **Width:**
   - Under `accept_rh_alpoge` with x ≥ 10¹², check hi − lo ≤ 2w + 2.
   - Under `default`, check that the width matches the Dusart formula to within 2.
4. **li cross-check:** Arb's li(x) against `mpmath.li` at 2× precision for 10³ random x. Also check that the principal value at x = 2 is li(2) ≈ 1.04516, to catch an offset Li slipping in.
5. **Inconsistency path:** inject a fake basis with a false bound and check that `InconsistencyError` is raised.
6. **Exact backend:** the pure-Python sieve against A006880 up to 10⁸, and against `primecount` when installed.

## Reusing this pattern

Each later number-theory spec uses the same four parts: bases table with domain, hypothesis and status; computation per branch; intersection or fallback rule; verifier table. It also uses the same result fields: per-output basis ids, `method`, and `scope`.
