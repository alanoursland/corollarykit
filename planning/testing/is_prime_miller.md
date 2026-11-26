# Testing: `is_prime_miller(n)`

Plan: [../is_prime_miller.md](../is_prime_miller.md)

## 1. Reference values

- Every n < 10⁷, against a sieve.
- **ψ_k, the smallest strong pseudoprime to the first k prime bases** (OEIS A014233), for k ≤ 13. Each must be reported composite, and the witness must be a prime above the k-th.
- **The Sorenson–Webster boundary:** n = 3 317 044 064 679 887 385 961 981 (ψ₁₃) is composite, and 13 bases suffice below it. Test both sides.

## 2. Oracle comparison

- PARI `isprime` (`oracle_pari`, proven) and `gmpy2.is_prime` for 10⁴ random odd n at 82–400 bits, plus random primes and semiprimes at those sizes.
- **Full run (`@slow`):** the Feitsma–Galway list of base-2 strong pseudoprimes below 2⁶⁴, downloaded and hash-pinned. Every entry must be reported composite. That is about 3·10⁷ entries; the fast tier uses a pinned random sample of 10⁴.

## 3. Properties

- A `Composite` witness a really fails the strong test. This is checked independently.
- Products of two primes p·q, Carmichael numbers, and Arnault-style numbers that pass many bases are all reported composite.
- `Prime` above the fixed-base range lists every prime base below 2·ln²n, and nothing else.

## 4. Edge cases

- n ∈ {−7, 0, 1, 2, 3, 4}, even n, and n with small factors: each early exit returns its specified result (prime, composite with a factor, or composite with witness 2).
- **Perfect powers:** 3¹⁰⁰, (2⁶¹ − 1)², and p^k for random primes p and k ∈ {2, 3, 5, 7}. Each is reported composite with the root as its certificate, before Miller's argument, which assumes n is not a prime power.
- The exact integer cutoff between the fixed-base and GRH ranges: ψ₁₃ − 2, ψ₁₃ and ψ₁₃ + 2.

## 5. Bases and policy

- **Separate switches:**
  - with only `sorenson_webster2017` accepted, inputs at or above the cutoff raise `BasisNotAccepted`, or delegate to the policy's proof backend;
  - with `bach1990.miller` accepted, they are answered and labeled.
- `DEFAULT` never reports `bach1990.miller`.

## 6. Certificates

- `Composite(witness)`: `full`. The verifier does one modular exponentiation chain.
- `Composite(factor)`: `full`. The verifier divides.
- `Prime`, fixed-base range: `full` under the classical computation. The verifier reruns the 13 bases.
- `Prime`, GRH range: `basis`. The verifier reruns the full transcript and reports the dependence on `bach1990.miller`.
- **Corruption:** replace the witness with a liar (a base that passes). It must be rejected.

## 7. Failure paths

- None of the injected ceilings apply: there is no "ceiling hit" path, since passing every base means "prime under the basis". Instead, test that a policy demanding an unconditional proof, with no ECPP backend installed, raises `BasisNotAccepted`.

## 8. Performance

- The 128-, 256- and 1024-bit table from the plan, measured against PARI's ECPP-based `isprime`. These measurements decide the advertised useful range.
