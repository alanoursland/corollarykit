# Testing: `irreducible_polynomial(p, d)`

Plan: [../irreducible_polynomial.md](../irreducible_polynomial.md)

## 1. Reference values

- **Counts:** for small p and d (p ≤ 13, d ≤ 8), enumerate every monic polynomial and confirm the number of irreducibles matches Gauss's formula (1/d)·Σ μ(d/k)·p^k. This validates the test oracle itself. Then confirm our output is one of them.
- Conway polynomials (Lübeck's tables) are *not* expected to match, since we produce binomials. They only serve as an independent irreducibility cross-check of the test oracle.

## 2. Oracle comparison

- PARI `polisirreducible` (`oracle_pari`) on every output, for p < 2⁶⁴ and d ≤ 200.
- `galois` or `sympy` irreducibility as a second oracle, for p < 2¹⁶.

## 3. Properties

- The output is monic, has degree exactly d, and is irreducible.
- The output is deterministic: the same (p, d) gives the same polynomial, across runs and Python versions.
- **Degree routing:**
  - for d whose primes all divide p − 1 (respecting 4 | d ⇒ p ≡ 1 mod 4), the output is a binomial x^d − a;
  - for d = p^k, it comes from an Artin–Schreier tower;
  - for mixed d, it is a composed product.

  The result reports which route it took, and the test asserts the route.

## 4. Edge cases

- d = 1, and d = 2 with p = 2.
- p = 2 in general, where p − 1 = 1 so the binomial route never applies.
- p ≡ 3 (mod 4) with 4 | d: the 2-power part must go to the fallback, and the parts must stay pairwise coprime in degree.
- Prime ℓ dividing d with ℓ ∤ p(p−1): fallback route.
- p composite, p < 2, or d < 1: `ValueError`.

## 5. Bases and policy

- Binomial route under policies accepting `bach1990.subgroup`: reports that basis and the non-residue ceiling.
- Fallback route under `DEFAULT`: `bound: none`.
- Under a test policy that trusts a synthetic proof of `GRH-dedekind`: Adleman–Lenstra Algorithm A, when implemented.
- `lidl_niederreiter.binomial` (classical) is reported for the irreducibility *argument* of the binomial route.

## 6. Certificates

- Rabin's test transcript: x^(p^d) ≡ x (mod f), and gcd(x^(p^(d/ℓ)) − x, f) = 1 for each prime ℓ | d. The verifier recomputes it with its own polynomial arithmetic, not the library's (`full`).
- **Corruption:** substitute a reducible polynomial of the same degree, such as the product of two irreducibles. The verifier must reject it.

## 7. Failure paths

- A fake non-residue ceiling below the actual least ℓ-th non-residue must raise `InconsistencyError`.

## 8. Performance

- Time for d ∈ {2, 3, 2¹⁰, 3⁵·5, 997} at p of 64, 256 and 1024 bits, by route.
