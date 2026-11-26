# Testing: `sqrt_mod_prime(a, p)`, `nth_root_mod_prime(a, r, p)`

Plan: [../sqrt_mod_prime.md](../sqrt_mod_prime.md)

## 1. Reference values

- **Least non-residues:** OEIS A000229 gives the primes at which the least quadratic non-residue reaches each new prime value. For each, the internal `least_nonresidue(p)` must match the record, and stay below 2·ln²p.
- Every a mod p, for every prime p < 2000: square roots against a brute-force table.

## 2. Oracle comparison

- `sympy.ntheory.sqrt_mod` (`oracle_sympy`) and PARI `sqrt(Mod(a,p))` (`oracle_pari`) for random primes up to 2048 bits. Weight the sample toward p ≡ 1 (mod 2^k) with k ≥ 10, since that is the slow Tonelli–Shanks path.
- r-th roots: PARI `ispower` and `sqrtn` for r ∈ {3, 5, 7, 2⁴, 3·5} and random p.

## 3. Properties

- **Root:** x² ≡ a (mod p), and 0 ≤ x < p. Which root is returned is fixed, for example the smaller of x and p − x, so the function is deterministic. Test that.
- **NoRoot:** the Legendre symbol (a/p) = −1, computed independently by Euler's criterion.
- r-th roots: x^r ≡ a. NoRoot exactly when a^((p−1)/d) ≢ 1 with d = gcd(r, p−1).
- The cached and uncached `least_nonresidue` agree.

## 4. Edge cases

- **p = 2:** a ∈ {0, 1}, handled directly.
- a ≡ 0; a ≥ p; a < 0 (reduced first).
- p ≡ 3 (mod 4), p ≡ 5 (mod 8), and p ≡ 1 (mod 8): each path at least 100 times.
- p = 2^k·q + 1 with very large k (Proth-like primes), the worst case for the 2-adic descent.
- **Composite p** with `verify_prime=False`: the result is labeled "input contract violated, unspecified". With `verify_prime=True` it raises `ValueError`. The NoRoot certificate is never issued for an unverified composite.
- r-th roots: gcd(r, p−1) = 1 (unique root, a^(r⁻¹ mod p−1)); repeated prime powers r = ℓ^k with ℓ^k | p − 1; r larger than p.

## 5. Bases and policy

- Non-residue scan ceiling: under the policies that accept it, `bach1990.nonresidue` is reported. Under `DEFAULT`, the scan has no ceiling and reports `bound: none`, with the same answer.
- Only prime candidates are scanned: instrument the scan and assert that no composite z is tested.

## 6. Certificates

- Root: the verifier squares it, or raises it to the r-th power (`full`).
- NoRoot: the verifier computes Euler's criterion independently (`full`, given that p is prime). The certificate records that it assumes p is prime, and the verifier checks that assumption with its own primality test.

## 7. Failure paths

- A fake basis with non-residue ceiling 2: p = 7 has least non-residue 3, so it must raise `InconsistencyError`.

## 8. Performance

- Time per root at 256, 1024 and 4096 bits, for each congruence class of p, against `sympy` and `gmpy2`.
