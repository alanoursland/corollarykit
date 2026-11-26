# Testing: `next_prime(x)`, `prime_exists_between(a, b)`

Plan: [../next_prime.md](../next_prime.md)

## 1. Reference values

- **Record prime gaps:** OEIS A002386 (primes before maximal gaps) and A005250 (the gap sizes), through 2⁶⁴. For each record prime p with gap g, `next_prime(p)` = p + g. The gap must also be below the `cms2019` ceiling at p. This is the strongest available test of that ceiling.
- `next_prime` over every x in [0, 10⁶], against a sieve.

## 2. Oracle comparison

- `sympy.nextprime` (`oracle_sympy`) and PARI `nextprime` (`oracle_pari`) for random x up to 512 bits.
- Every returned value is also checked for primality under a **different** primality backend from the one `next_prime` used.

## 3. Properties

- `next_prime(x)` > x and is prime. No prime lies in (x, `next_prime(x)`): checked by sieving for x ≤ 10¹², and by the verifier's witnesses above that.
- `prime_exists_between(a, b)` agrees with sieving for all 0 ≤ a < b ≤ 10⁵.
- Theorem answers: when b − a ≥ (22/25)·√b·ln b + 1 and a > 3, the result has `method="theorem"`, and every sampled case agrees with search.

## 4. Edge cases

- x ∈ {−10, 0, 1, 2, 3}: `next_prime(2)` = 3, `next_prime(−10)` = 2.
- a ≥ b, a < 0, and a ≤ 3 (outside the theorem's domain, so it searches).
- x just below a large known prime.

## 5. Bases and policy

- **Proven answers per policy:**
  - Under "proof", every accepted candidate is certified by `is_prime_miller` or ECPP.
  - BPSW may only reject candidates. Test it with a stub BPSW that wrongly accepts a composite: the "proof" policy must not return it.
- Under `DEFAULT`, `cms2019` is not used. The ceiling reported is Dusart's, or none below its domain.
- **Companion bounds:** `next_prime` from an arbitrary x uses the gap bound at x, and the test checks the bound is applied to √x·ln x with x itself, not to p_k (the monotonicity argument in the plan).

## 6. Certificates

- `next_prime` returns p, a primality certificate, and **`full` scope:** for each composite candidate in (x, p), a small factor or a compositeness witness. The verifier rechecks all of them without importing the library.
- `prime_exists_between` with `method="theorem"` is `basis` scope: the verifier checks the inequality and names the basis.

## 7. Failure paths

- A fake gap basis with ceiling 1: `next_prime(7)` must raise `InconsistencyError`, because the gap from 7 to 11 is 4.

## 8. Performance

- Average and worst-case candidates per call for x ≈ 2⁶⁴, 2²⁵⁶, 2¹⁰²⁴, under each primality policy.
