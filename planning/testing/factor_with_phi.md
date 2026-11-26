# Testing: `factor_with_phi(n, phi)`

Plan: [../factor_with_phi.md](../factor_with_phi.md)

## 1. Reference values

- Every n < 10⁵ with m = φ(n), against `sympy.factorint`.
- Carmichael numbers below 10¹⁸, from Pinch's tables, with m = φ(n) and m = λ(n).

## 2. Oracle comparison

- Random n up to 512 bits built from known primes (2 to 12 factors, mixed exponents), with m ∈ {φ(n), λ(n), k·λ(n)} for random k.

## 3. Properties

- The product of the output equals n. Every factor is prime under the active policy. The output is sorted and canonical, so it is deterministic.
- The same m is valid for every divisor, so recursion never needs a new m. Test this by asserting no further m is computed.

## 4. Edge cases

- n prime, n = p^k, n even, n = 1, n = 2.
- n = pq takes the quadratic shortcut, and the test checks the path taken.
- **Invalid m:** m not a multiple of λ(n) (for example φ(n) + 2, or λ(n)/2 where that is an integer) raises `ValueError` with a witness base a where a^m ≢ 1.
- m = 0, negative m, and non-integer input.

## 5. Bases and policy

- `DEFAULT`: the strict path, with randomized bases, a budget and the pq shortcut. The answer is correct, and the result reports that no running-time basis was used.
- With `miller1976.phi` and `bach1990.subgroup` accepted: deterministic. The number of bases tried per split must stay below 2·ln²n.
- Only prime bases are tried. Instrument this, as in `sqrt_mod_prime`.

## 6. Certificates

- The verifier multiplies the factors back together and checks each factor's primality certificate (`full`).

## 7. Failure paths

- A fake ceiling of 1 on a Carmichael number whose base 2 doesn't split it: `InconsistencyError`. First, find such an n by search during test setup.

## 8. Performance

- Time against `sympy.factorint` given φ, at 128 to 512 bits. Expect them to be equal. This is a guarantee, not a speed-up.
