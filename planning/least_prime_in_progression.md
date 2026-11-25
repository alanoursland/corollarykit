# `least_prime_in_progression(a, q)`

Return the least prime p ≡ a (mod q), for gcd(a, q) = 1, with a proven ceiling on the search. Companion helpers:
- `ntt_prime(bits, k)`: a prime p ≡ 1 (mod 2^k) of a given size, for number-theoretic transforms.
- `prime_with_residue(a, q, min=…)`: the same search starting from a lower limit.

## Old implementation

Scan a, a+q, a+2q, …, sieving out small factors in blocks and testing the survivors for primality.

- **Expected candidates:** about (φ(q)/q)·ln(p), roughly O(log q) to O(log p). Fast in practice.
- **Unconditional ceiling:** Linnik, p ≪ q^L, with L = 5 (Xylouris 2011). It is effective in principle, but no usable explicit constant is in common use, so implementations run without a ceiling. The search is poly(q), which is exponential in the bit length of q.

## What changes it

**Bases `bach_sorenson1996` and `lls2015`**, assuming GRH for Dirichlet L-functions (Alpöge–Claude, `lean-compiled`, `statement_match = unchecked`). Each basis applies only on its stated domain of q. Record the exact domain from the papers before enabling either one.

    p ≤ 2 · (q · ln q)²              (Bach–Sorenson 1996)
    p ≤ (φ(q) · ln q)²   for q ≥ 4   (Lamzouri–Li–Soundararajan 2015)

Characters mod q are Dirichlet characters, so this is within the claimed scope.

**Second, independent basis:** OpenAI's claimed proof that Siegel zeros don't exist (Oct 2026, `claimed`). If it holds, Linnik-type and Siegel–Walfisz-type constants become computable without assuming GRH. We need to find out whether anyone has produced explicit numbers from it.

## New implementation

1. Validate q ≥ 1 and gcd(a, q) = 1, and reduce a mod q.
2. **Small q, handled directly (no basis):** q = 1 returns 2, since every integer is ≡ 0 mod 1 and the formula's ceiling would be 0. q = 2 returns 3, the least odd prime.
3. **Check sieving primes in the progression first:** every prime r ≤ B with r ≡ a (mod q) is itself a candidate. Example: (a, q) = (2, 3) has answer 2. Check these directly, smallest first. Return the least one if any is below the first block's start.
4. Set the ceiling C from the bases the policy accepts, within their stated domains. If none applies, search without a ceiling and label the result `basis = none`.
5. **Segmented sieve:** for each block of the progression and each sieving prime r ∤ q, cross off the candidates a + jq divisible by r, **except r itself**. Start at max(r², first candidate in the block). Test the survivors with the policy's primality test, in increasing order.
6. If the search passes C, raise `InconsistencyError`.
7. Return p with a certificate (below).

**Certificate scope:**
- **`membership`** (always included): p ≡ a (mod q), plus a primality certificate for p from the chosen test. This shows p is a prime in the progression. It does not show p is the least.
- **`full`** (optional, `certificate="full"`): for every earlier candidate a + jq < p, either a nontrivial factor (from the sieve) or a strong-pseudoprime witness (from the failed test). Since this covers every earlier candidate, a checker can confirm minimality with no basis at all. The ceiling only bounds the running time. Size: about (p − a)/q entries, usually small, up to O(q·log² q) in the worst case.

**Complexity:**
- The ceiling is **O(q · log² q)** terms of the progression. That is polynomial in q but still exponential in the bit length of q. Even GRH doesn't make "least prime in a progression" polynomial in log q.
- What it gives is a proven, explicit termination bound where there used to be none in practice.
- The expected cost does not change.

For NTT primes (q = 2^k, primes p ≈ 2^b with b a little above k), the search is short in practice. The ceiling guarantees it ends before about 2^(2k+2·log k).

## Testing

- Compare against OEIS A038026 (least prime ≡ 1 mod n) and A085420 (the worst-case a for each q) for q ≤ 10⁵.
- Edge cases: (a, q) = (0, 1) → 2; (1, 2) → 3; (2, 3) → 2; (3, 4) → 3; (5, 6) → 5. In each, the answer is a small prime that is also a sieving prime.
- For every q ≤ 10³ and every a, check that the `full` certificate passes an independent checker that doesn't import the search code.
- Cross-check NTT primes against published tables, such as the moduli used by Kyber and Dilithium (q = 3329, 8 380 417).

## Open questions

- If explicit constants follow from the Siegel-zero result, add that as a basis that doesn't depend on the November proof.
