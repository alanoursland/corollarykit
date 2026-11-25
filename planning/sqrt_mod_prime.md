# `sqrt_mod_prime(a, p)` and `nth_root_mod_prime(a, r, p)`

Return x with x² ≡ a (mod p), or a certificate that none exists. Deterministic, with a proven worst-case bound. The extension handles r-th roots.

## Old implementation

Write p − 1 = 2^e · q with q odd.

| Case | Method | Needs a non-residue? | Deterministic today? |
|---|---|---|---|
| p ≡ 3 (mod 4) | x = a^((p+1)/4) | no | yes |
| p ≡ 5 (mod 8) | Atkin's formula | no | yes |
| p ≡ 1 (mod 8) | Tonelli–Shanks or Cipolla | **yes** | only with an exponential-time search |

**Tonelli–Shanks:**
1. Find a quadratic non-residue z. Pick random z until the Legendre symbol (z/p) = −1. Each try succeeds with probability 1/2, so the expected number of tries is 2.
2. Run the 2-adic descent, which costs O(log p + e²) multiplications mod p.

The total is O(log² p · M(log p)) bit operations worst case, given z. It is Las Vegas: always correct, with random running time.

**Deterministic unconditional:** scan z = 2, 3, 5, … The least non-residue n(p) is bounded unconditionally only by Burgess, at n(p) ≪ p^(1/(4√e)+ε) ≈ p^0.152. That makes the deterministic worst case exponential in the bit length. Schoof (1985) gives deterministic polynomial time only for a fixed a.

**Existence check:** Euler's criterion or the Jacobi symbol (a/p) decides whether a root exists, in O(log² p) bit operations, deterministically.

## What changes it

**Basis `bach1990.nonresidue`:** n(p) < 2 · (ln p)², assuming GRH for Dirichlet L-functions. The characters mod p are Dirichlet characters, so this is within the claimed scope of Alpöge–Claude (`lean-compiled`, `statement_match = unchecked`).

The second basis is quasi-GRH, Re s > σ₀ (OpenAI, Oct 2026, `claimed`; σ₀ = 11/12 in the registry). The exposition gives n(p) ≤ C·(ln p)^32, which was derived for 7/8. The exponent has to be re-derived for 11/12 before this basis is enabled. That is polynomial, but useless as a printed ceiling. Credit to OpenAI's October manuscript: it was the first to make this algorithm deterministic polynomial time. November improves the constant.

## New implementation

```
sqrt_mod_prime(a, p):
    a %= p; if a == 0: return 0
    if jacobi(a, p) == -1: return NoRoot(certificate=("jacobi", a, p, -1))
    if p % 4 == 3: return pow(a, (p+1)//4, p)
    if p % 8 == 5: Atkin
    z = least_nonresidue(p)      # scan 2,3,5,7,... (primes suffice), ceiling 2·ln²p
    Tonelli–Shanks with z
    return Root(x, certificate=x)  # verify: x*x % p == a
```

- **Primes are enough:** if every prime ≤ B were a residue, every integer ≤ B would be one too, since products of residues are residues. So the scan only checks prime z. That cuts the ceiling to about π(2 ln²p) candidates.
- **Caching:** z depends only on p. Cache `least_nonresidue(p)` with an LRU for repeated roots modulo the same prime.
- **Ceiling:** if the scan passes 2·ln²p, raise `InconsistencyError`.
- **Input contract:** p must be prime, and the library does not check this by default. With `verify_prime=True`, check it under the active primality policy. If p is composite, the existence certificate is invalid, since a Jacobi symbol of +1 does not imply a residue.

**Complexity:**
- Finding z deterministically: at most O(log² p / log log p) Jacobi evaluations at O(log² p) each, so **O(log⁴ p)** bit operations. Previously this was exponential worst case.
- Tonelli–Shanks: O(log² p · M(log p)).
- Total: **deterministic O(log⁴ p)**, against expected O(log³ p) before. In practice z is almost always 2, 3, 5 or 7 (the average least non-residue is about 3.67), so measured speed should be identical. The change is the guarantee.

### Extension: `nth_root_mod_prime(a, r, p)`

- **Old:** Adleman–Manders–Miller needs an r-th power non-residue mod p for each prime r dividing gcd(r, p−1). It is found randomly, or deterministically in exponential time.
- **Change:** Bach's bound also covers characters of order r mod p, which are Dirichlet characters, so the least r-th non-residue is below 2·ln²p under Dirichlet GRH.
- **New:** a deterministic scan with the same ceiling, then AMM, at O(log⁴ p + r·log³ p)-ish.
- **Certificate:** x^r ≡ a.

## Testing

- Compare against `sympy.ntheory.sqrt_mod` and PARI `Mod(a,p)^(1/2)` on random primes up to 2048 bits, weighted toward p ≡ 1 (mod 2^k) with large k.
- Run the stress list of primes with the largest known least non-residue (OEIS A000229) and check that the ceiling always holds.

## Open questions

- Are there sharper explicit constants for prime p, such as (3/2)·ln²p asymptotically? Collect them as bases.
