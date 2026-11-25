# `primitive_root(p, factors=None)`

Return the least primitive root g mod p, so that g generates (ℤ/pℤ)^×, deterministically and with a proven search ceiling.

## Old implementation

Given the factorization p − 1 = ∏ qᵢ^eᵢ, with ω = ω(p−1) distinct prime factors:

```
for g = 2, 3, 4, ...:
    if all(pow(g, (p-1)//q, p) != 1 for q in qs): return g
```

- **Per candidate:** ω modular exponentiations, so O(ω · log p · M(log p)).
- **Expected candidates:** (p−1)/φ(p−1) = O(log log p). Fast in practice.
- **Worst-case ceiling:** the least primitive root g(p) is bounded unconditionally only by Burgess and Wang-type bounds, g(p) ≪ p^(1/4+ε), which is exponential in the bit length.
- **Bottleneck:** factoring p − 1. None of this year's results help with that. The API accepts `factors`, or factors p − 1 itself when it can.

## What changes it

**Basis `shoup1992`**, assuming GRH for Dirichlet L-functions (Alpöge–Claude, `lean-compiled`, `statement_match = unchecked`):

    g(p) = O(ω⁴ · (log ω + 1)⁴ · (log p)²) = O((log p)⁶)

**Special case: safe primes p = 2q + 1** (q prime). A primitive root is exactly a quadratic non-residue other than −1. Any such element has order 2q, because order 2 would make it −1. So `primitive_root(p) = least_nonresidue(p)` (excluding p−1) and **Bach's explicit bound 2·ln²p applies directly**. Safe primes are what Diffie–Hellman-style groups use, so this case matters most in practice.

**Contested basis:** an OpenAI manuscript (`claimed`) reportedly proves the existence part of Artin's conjecture unconditionally. That says infinitely many p have a given g as a primitive root. It gives no search bound, so we don't use it here.

## New implementation

1. If p = 2q + 1 with q prime, return `least_nonresidue(p)` from `sqrt_mod_prime`, with ceiling 2·ln²p.
2. Otherwise, run the standard scan with a ceiling from Shoup's bound.
3. Return g with a certificate.

**Certificate scope:**
- **`membership`** (always included): g is a primitive root. The certificate is the factorization of p−1 and the list `[(q, pow(g,(p-1)/q,p))]`, with every value ≠ 1. Checking the factorization needs primality certificates for each q (Pratt-style), included optionally.
- **`full`** (optional): g is the *least* primitive root. For each g′ < g, give one q with g′^((p−1)/q) ≡ 1 (mod p). That costs one modular exponentiation per smaller candidate to check, and needs no basis.
- In the safe-prime case, the `full` certificate is just the Legendre symbol (g′/p) = +1 for each 2 ≤ g′ < g, excluding −1.

**Complexity:**
- Deterministic worst case **O(log⁶ p) candidates × O(ω·log p·M(log p))**, which is polynomial in log p given the factorization. For safe primes, O(log² p) candidates. Previously the worst case was exponential.
- The expected cost does not change.

## Testing

- Compare against `sympy.primitive_root` and PARI `znprimroot` on random primes up to 512 bits and on safe primes up to 4096 bits.
- Check the record table of least primitive roots (OEIS A001918 maxima) against the ceiling.

## Open questions

- **Blocker:** Shoup's bound has an O(); we need an explicit constant or another explicit GRH bound for g(p). Until we have one, the general-p ceiling is reported as "polynomial, constant unknown" and the code raises nothing. Search the literature (Martin; Bach's later work) for explicit constants.
- Should we also provide a generator for prime-order subgroups (finding an element of order q)? That is the same Bach argument.
