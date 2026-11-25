# `prime_count_interval(x)`

Return integers `lo, hi` with `lo ≤ π(x) ≤ hi`, guaranteed, for very large `x` and without enumerating primes.

## Old implementation

**Exact counting**

| Method | Time | Space | Practical reach |
|---|---|---|---|
| Sieve of Eratosthenes (segmented) | O(x log log x) | O(√x) | about 10¹² |
| Meissel–Lehmer / Lagarias–Miller–Odlyzko | O(x^(2/3) / log x) | O(x^(1/3) log² x) | about 10²⁰ in C |
| Deléglise–Rivat, Gourdon refinements | O(x^(2/3) / log² x) | O(x^(1/3) log³ x) | record π(10²⁹) or so, on clusters |
| Lagarias–Odlyzko analytic | O(x^(1/2+ε)) | O(x^(1/4+ε)) | competitive only at extreme x |

All of these are exponential in the bit length of `x`. No exact method reaches a 100-digit `x`.

**Unconditional bounds (no RH)**

- Dusart (2010) type bounds, for example
  `x/ln x · (1 + 1/ln x + 2/ln²x) ≤ π(x)` for x ≥ 88 783 and
  `π(x) ≤ x/ln x · (1 + 1/ln x + 2.334/ln²x)` for x ≥ 2 953 652 287.
  The relative width is about 0.33/ln³x.
- Explicit versions of the de la Vallée Poussin error term, |π(x) − li(x)| ≤ C·x·exp(−c·√(ln x)) with explicit C and c (Platt–Trudgian, Johnston–Yang). These are much better asymptotically but have large constants.

The cost is O(polylog x), since they are closed formulas. For x = 10¹⁰⁰ the unconditional interval is about 10⁹² wide, against π(x) ≈ 4.3·10⁹⁷.

## What changes it

**Basis `schoenfeld1976`:** |π(x) − li(x)| < √x · ln x / (8π) for x ≥ 2657, assuming RH. RH is supplied by Alpöge–Claude (Nov 2026, `lean-compiled`, `statement_match = unchecked`). Under the default policy this basis is treated as `claimed`. Results based on it are labeled "RH (Alpöge–Claude)". They are not called unconditional.

A weaker basis is the claimed quasi-RH zero-free region Re s > σ₀ (OpenAI, Oct 2026, `claimed`). It gives |π(x) − li(x)| = O(x^σ₀ · log² x), using σ₀ = 11/12 as stated in the repository paper (7/8 per the catalog). We have not located explicit constants for it, so it cannot produce a printed interval yet. Track it, but don't implement it.

## New implementation

1. If x < X_exact (configurable; default about 10¹² in pure Python, about 10¹⁴ with the optional `primesieve`), return the exact count: `lo = hi = π(x)`.
2. Otherwise:
   - Evaluate li(x) as a rigorous ball (midpoint and radius) using Arb through `python-flint`, at a working precision of about `log2(x)/2 + 64` bits. That is enough to resolve the integer interval.
   - Compute `w = √x · ln x / (8π)` as a ball.
   - Set `lo = ceil(lower(li(x) − w))` and `hi = floor(upper(li(x) + w))`, rounding outward.
   - Also intersect with the Dusart interval. It is never wider, and it acts as a check.
3. Return a result object with `lo`, `hi`, `bases` (Schoenfeld under RH, plus Dusart as the unconditional fallback), and the precision used.

**Strict policy:** use only the Dusart and other unconditional intervals.

**Complexity:** li(x) to d = O(log x) digits costs O(M(d) log d) with Arb, where M(d) is the cost of multiplying d-digit numbers. The total is **O(polylog x)**, the same order as before. What changes is the width: from about x/ln⁴x down to about √x·ln x, so roughly half the digits of π(x) are now certified.

| x | π(x) ≈ | Unconditional width ≈ | RH width ≈ |
|---|---|---|---|
| 10²⁰ | 2.2·10¹⁸ | 2·10¹⁴ | 1.8·10⁹ |
| 10¹⁰⁰ | 4.3·10⁹⁷ | 10⁹² | 1.8·10⁵¹ |

These are rough figures. The tests will pin the exact ones.

## Testing

- Compare against known exact values of π(10^k) for k ≤ 29 (OEIS A006880): `lo ≤ π ≤ hi` must hold every time.
- Run an exact sieve over random x below 10⁹ and check containment.
- Check interval width against the formula. Check behavior at the 2657 boundary.

## Open questions

- Does `python-flint` expose a rigorous `li`? If not, use Ei(ln x) or `arb_hypgeom_li` through a small C extension.
- Büthe (2016) and others give sharper RH-conditional bounds over some ranges. Collect them as extra bases.
