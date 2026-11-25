# `least_prime_in_progression(a, q)`

Return the least prime p ≡ a (mod q), for gcd(a, q) = 1, with a proven ceiling on the search. Companion helpers:
- `ntt_prime(bits, k)`: a prime p ≡ 1 (mod 2^k) of a given size, for number-theoretic transforms.
- `prime_with_residue(a, q, min=…)`: the same search starting from a lower limit.

## Old implementation

Scan a, a+q, a+2q, …, sieving out small factors in blocks and testing the survivors for primality.

- **Expected candidates:** about (φ(q)/q)·ln(p), roughly O(log q) to O(log p). Fast in practice.
- **Unconditional ceiling:** Linnik, p ≪ q^L, with L = 5 (Xylouris 2011). It is effective in principle, but no usable explicit constant is in common use, so implementations run without a ceiling. The search is poly(q), which is exponential in the bit length of q.

## What changes it

**GRH for Dirichlet L-functions** (Alpöge–Claude, `lean-compiled`) makes these unconditional:

    p ≤ 2 · (q · ln q)²              (Bach–Sorenson 1996)
    p ≤ (φ(q) · ln q)²   for q ≥ 4   (Lamzouri–Li–Soundararajan 2015)

Characters mod q are Dirichlet characters, so this is within the claimed scope.

**Second, independent basis:** OpenAI's claimed proof that Siegel zeros don't exist (Oct 2026, `claimed`). If it holds, Linnik-type and Siegel–Walfisz-type constants become computable without assuming GRH. We need to find out whether anyone has produced explicit numbers from it.

## New implementation

1. Validate gcd(a, q) = 1 and reduce a mod q.
2. Set the ceiling C = (φ(q)·ln q)² for q ≥ 4, and 2(q ln q)² otherwise. Use whichever bound the active policy allows.
3. Run a segmented sieve over the progression: for a block of k values, cross off multiples of primes up to some B, then test the survivors with the policy's primality test.
4. If the search passes C, raise `InconsistencyError`.
5. Return p with a certificate: the primality certificate from the chosen test, plus p ≡ a (mod q), which anyone can check.

**Complexity:**
- The ceiling is **O(q · log² q)** terms of the progression. That is polynomial in q but still exponential in the bit length of q. Even GRH doesn't make "least prime in a progression" polynomial in log q.
- What it gives is a proven, explicit termination bound where there used to be none in practice.
- The expected cost does not change.

For NTT primes (q = 2^k, primes p ≈ 2^b with b a little above k), the search is short in practice. The ceiling guarantees it ends before about 2^(2k+2·log k).

## Testing

- Compare against OEIS A038026 (least prime ≡ 1 mod n) and A085420 (the worst-case a for each q) for q ≤ 10⁵.
- Cross-check NTT primes against published tables, such as the moduli used by Kyber and Dilithium (q = 3329, 8 380 417).

## Open questions

- If explicit constants follow from the Siegel-zero result, add that as a basis that doesn't depend on the November proof.
