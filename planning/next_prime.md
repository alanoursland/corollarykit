# `next_prime(x)` and `prime_exists_between(a, b)`

`next_prime(x)` returns the least prime greater than x, with a proven ceiling on how far it searches. `prime_exists_between(a, b)` decides from a theorem alone, without searching, that a prime lies in (a, b].

## Old implementation

Test x+1, x+2, … for primality, skipping multiples of small primes with a wheel. The expected gap is about ln x, so the expected cost is O(ln x) primality tests.

The worst-case ceiling comes from unconditional gap bounds:
- Baker–Harman–Pintz: g(p) ≪ p^0.525. Not explicit, so it can't serve as a loop bound.
- Explicit: Dusart (2018) shows that for x ≥ 468 991 632 there is a prime in (x, x + x/(5000·ln²x)]. A ceiling of about x/ln²x candidates is exponential in the bit length.

`prime_exists_between(a, b)` is decidable today only by searching, or when b − a exceeds the Dusart width.

## What changes it

**Basis `cms2019`:** Carneiro–Milinovich–Soundararajan (2019), assuming RH. RH is supplied by Alpöge–Claude (`lean-compiled`, `statement_match = unchecked`).

    p_{k+1} − p_k < (22/25) · √p_k · ln p_k        for p_k > 3

Cramér's 1920 form, O(√p·ln p), follows as well.

## New implementation

- **`next_prime(x)`:** the same wheel-plus-test scan, but with a hard ceiling `x + ceil((22/25)·√x·ln x)`. The proof uses p_k ≤ x, so the bound has to be applied to the largest prime ≤ x. Use √x·ln x as an upper bound on √p_k·ln p_k, which holds because the function is increasing.
  - If the ceiling is ever hit, raise `InconsistencyError`. That would mean the theorem is false or there is a bug.
  - The per-candidate primality test is set by policy: BPSW for speed, `is_prime_miller` or ECPP for proof.
- **`prime_exists_between(a, b)`:** return `True` with a certificate naming the theorem when b − a ≥ (22/25)·√b·ln b + 1 and a > 3. Otherwise fall back to searching. This costs O(1) in the theorem case.

**Complexity:**
- Expected cost is unchanged: O(ln x) tests.
- The worst-case ceiling falls from about x/(5000·ln²x) to about 0.88·√x·ln x candidates. That is still exponential in the bit length, since only Cramér's conjecture (O(ln²x)) would make it polynomial, and that remains open.
- The gain is a proven termination bound, and existence answers in O(1) for intervals longer than about √x·ln x.

## Testing

- Check against tables of maximal prime gaps (known through 2⁶⁴): every recorded gap must lie below the bound.
- Brute-force `prime_exists_between` over small ranges.

## Open questions

- Gap bounds conditional on GRH for primes in arithmetic progressions would give the analogous `next_prime_in_progression`. Find explicit forms of them.
