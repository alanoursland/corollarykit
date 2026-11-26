# Testing: `primitive_root(p, factors)`

Plan: [../primitive_root.md](../primitive_root.md)

## 1. Reference values

- The least primitive root of the nth prime (OEIS A001918), for the first 10⁴ primes.
- Record values: primes whose least primitive root is unusually large, extracted from A001918. These test the ceiling.

## 2. Oracle comparison

- `sympy.primitive_root` (`oracle_sympy`) and PARI `znprimroot` (`oracle_pari`) for random primes up to 512 bits, and for safe primes up to 4096 bits.
- Note that PARI returns *a* generator, not necessarily the least. Compare by checking that its answer is a generator and that ours is ≤ PARI's, then confirm minimality with the `full` certificate.

## 3. Properties

- g^((p−1)/q) ≢ 1 for every prime q | p − 1.
- **Minimality:** every g′ < g fails for some q.
- Safe primes: the result equals the least non-residue ≠ −1.

## 4. Edge cases

- **p = 2:** returns 1. **p = 3:** returns 2.
- **Supplied factorizations:** wrong primes, missing primes, wrong exponents, composite "primes", and non-dict input must all raise `ValueError`, with the product checked against p − 1 and each factor checked for primality.
- No factorization supplied, and p − 1 not factorable within the budget: raise `BasisNotAccepted` or a clear "cannot factor" error. Never return an unverified answer.

## 5. Bases and policy

- No numeric Shoup ceiling is advertised. The result reports `bound: none` for general p, and `bach1990.nonresidue` for safe primes under accepting policies.

## 6. Certificates

- `membership`: the verifier checks the factorization (product and primality) and each g^((p−1)/q) ≠ 1.
- `full`: the verifier also checks, for each g′ < g, the listed q with g′^((p−1)/q) ≡ 1.
- **Corruption tests:** drop one entry from `full`, change a q, or swap g for a non-generator. Each must be rejected.

## 7. Failure paths

- A fake ceiling of 2 on p = 7, whose least primitive root is 3, must raise `InconsistencyError`, but only for the safe-prime path where a ceiling is applied.

## 8. Performance

- Time with factors supplied, for p up to 4096 bits. Factoring time is reported separately.
