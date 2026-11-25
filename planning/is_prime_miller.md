# `is_prime_miller(n)`

Deterministic primality test: a proven answer for any n, with a compositeness witness when n is composite.

## Old implementation

| Method | Time | Answer | Notes |
|---|---|---|---|
| Miller–Rabin, k random bases | O(k · log n · M(log n)) | probabilistic, error ≤ 4^(−k) | the usual default |
| BPSW | O(log n · M(log n)) | no known counterexample, no proof | the default in SymPy, PARI and GMP |
| Fixed deterministic bases | O(log n · M(log n)) | **proven** for n < 3.317·10²⁴ (first 13 prime bases; Sorenson–Webster) | proven by exhaustive computation; the best choice below about 81 bits |
| AKS (Lenstra–Pomerance variant) | Õ(log⁶ n) | proven, unconditional | far too slow in practice |
| APR-CL | (log n)^O(log log log n) | proven | practical up to a few thousand digits |
| ECPP | heuristic Õ(log⁴ n) to Õ(log⁵ n) | proven, with a certificate that is fast to check | the practical choice for big primes |

## What changes it

**Basis `bach1990.miller`:** Miller (1976) with Bach's (1990) explicit constant, assuming GRH for Dirichlet L-functions (Alpöge–Claude, `lean-compiled`, `statement_match = unchecked`):

    if n is an odd composite, some base a < 2·(ln n)² is a strong-pseudoprime witness

The argument uses characters mod n, which are Dirichlet characters, so this is within the claimed scope.

The second basis is quasi-GRH, Re s > 7/8 (OpenAI, Oct 2026, `claimed`), which gives a polynomial but much larger ceiling. Credit to it: it made Miller's test deterministic first.

## New implementation

1. Handle n < 2 and small n with trial division.
2. If n is a perfect power, return composite. Miller's subgroup argument assumes n is not a prime power.
3. If n < 3.317·10²⁴, use the fixed 13-base set. This is already proven and needs no new mathematics.
4. Otherwise, run the strong test for every **prime** base a < 2·ln²n.
   - Prime bases suffice: the non-witnesses lie in a proper subgroup H. If every prime below B were in H, every integer below B would be, contradicting Bach's bound.
   - Return `Composite(witness=a)` on the first failure. Anyone can recheck the witness with one modular exponentiation.
5. If every base passes, return `Prime(bases=[...])`.

**Certificate scope:**
- `Composite` is `full`: the witness proves compositeness with no basis needed.
- `Prime` from step 4 is `basis`: it is proven only if `bach1990.miller` holds, and checking it means running the test again.
- `Prime` from step 3 is `full` under the classical Sorenson–Webster computation.
- A caller who needs a basis-free proof that n is prime should use ECPP or Pratt certificates.

**Complexity:** about π(2 ln²n) ≈ 2 ln²n / ln(2 ln²n) bases, each costing O(log n · M(log n)). The total is **Õ(log⁴ n)** bit operations, deterministic and proven, against Õ(log⁶ n) for AKS.

**Rough cost in practice (to benchmark):**

| Bits | 2·ln²n | Prime bases | CPython time (guess) | ECPP (PARI) |
|---|---|---|---|---|
| 128 | 15 700 | ~1 700 | ~10 ms | ~ms |
| 256 | 63 000 | ~5 900 | ~0.1 s | ~10 ms |
| 1024 | 1.0 M | ~76 000 | ~1–2 min | ~1 s |

The new test will probably lose to ECPP above a few hundred bits. Its advantages are reproducibility (the answer depends only on n), no certificate to store, and a short trusted code base. It fits as a proven test in the range of about 81 to 300 bits, and as the per-candidate test in `next_prime` and `least_prime_in_progression` under the "proof" policy.

## Testing

- Every composite in the Feitsma–Galway list of base-2 strong pseudoprimes below 2⁶⁴ must be rejected.
- Arnault-style strong pseudoprimes to many bases must be rejected.
- Results must agree with `gmpy2.is_prime` and PARI `isprime` (which is proven) on random 100–400-bit inputs.

## Open questions

- Benchmark for real before advertising any speed range.
- Bach's constant for Miller is 2. Later work (for example Bach–Huelsbeck) suggests the bound needed in practice is far smaller. Only proven constants go in the code.
