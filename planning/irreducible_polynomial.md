# `irreducible_polynomial(p, d)`

Return a monic irreducible polynomial of degree d over F_p, deterministically. This gives a reproducible representation of F_(p^d), the same output for the same (p, d), which is useful for test vectors, interoperable parameters and proofs.

## Old implementation

| Method | Time | Deterministic? | Hypothesis |
|---|---|---|---|
| Random monic polynomials plus Ben-Or / Rabin irreducibility test | expected Õ(d²·log p) field ops; about 1/d of candidates are irreducible | no | none |
| Lexicographic scan with the same test | the same in practice; no proven worst case | yes | none (no bound) |
| Shoup (1990) | polynomial in d and **p**, which is exponential in the bit length of p | yes | none |
| Adleman–Lenstra Algorithm B (1986) | polynomial in d·log p, but the degree is only approximately d: d/(c·log p) < deg ≤ d | yes | none |
| Adleman–Lenstra Algorithm A (1986) | (d·log p)^c | yes | ERH (see below) |

Special degrees that are already deterministic and unconditional:
- **deg p:** Artin–Schreier, x^p − x − 1.
- **Compositum:** if f and g are irreducible of coprime degrees m and n, their composed product is irreducible of degree mn.

## What changes it, and what doesn't

**Adleman–Lenstra Algorithm A is not covered by the November proof (inferred).**
- **What the paper says:** its Proposition 3 assumes ERH to find "a prime q ≡ 1 (mod n) with q < c·n⁴(log(np))² such that p is inert in the (unique) subfield K ⊆ ℚ(ζ_q) with [K:ℚ] = n". It cites a variant of a theorem from Bach and a co-author (FOCS 1985, pp. 443–450).
- **Our inference:** as q varies, "p inert in K" is a splitting condition in the Kummer fields ℚ(ζ_ℓ, p^(1/ℓ)) for the primes ℓ dividing n. Those are non-abelian, so the effective Chebotarev theorem needed uses GRH for their Dedekind zeta functions, which is beyond Dirichlet L-functions.
- **Status:** registered as `GRH-dedekind`, `transcription_checked = false`, until the cited theorem's hypothesis is read directly.

**What Dirichlet GRH does give:** irreducible binomials. By Lidl–Niederreiter, Theorem 3.75, x^t − a is irreducible over F_p if and only if every prime factor of t divides ord(a) but not (p − 1)/ord(a), and also p ≡ 1 (mod 4) when 4 | t.

For a degree d whose prime factors ℓ all divide p − 1:
1. For each such ℓ, find an ℓ-th power non-residue b_ℓ mod p. **Basis `bach1990.subgroup`:** one exists below 2·ln²p, applied to the subgroup of ℓ-th powers. This is Dirichlet GRH, so within the claimed scope.
2. Set c_ℓ = b_ℓ^((p−1)/ℓ^(e_ℓ)), where ℓ^(e_ℓ) is the exact power of ℓ dividing p − 1. Then c_ℓ has order exactly ℓ^(e_ℓ). Let a = ∏ c_ℓ, so ord(a) = ∏ ℓ^(e_ℓ).
3. Then x^d − a is irreducible, provided p ≡ 1 (mod 4) whenever 4 | d.

## New implementation

```
irreducible_polynomial(p, d):
    split d = d_good · d_p · d_other, where
        d_good  : primes ℓ | p−1   (and the 4 | d ⇒ p ≡ 1 mod 4 condition)
        d_p     : power of p
        d_other : remaining primes
    f_good  = x^d_good − a            (Dirichlet GRH: bach1990.subgroup)
    f_p     = Artin–Schreier tower    (unconditional)
    f_other = fallback                (see below)
    return composed product of f_good, f_p, f_other  (degrees pairwise coprime)
```

**Fallback for d_other:**
- With the default policy: a deterministic lexicographic scan with Ben-Or's test. This is correct, but with no proven ceiling, so the result is labeled `bound: none`.
- With the opt-in `GRH-dedekind` policy, which no proof currently supports: Adleman–Lenstra Algorithm A.
- With `allow_random=True`: Rabin's randomized search.

**Certificate:** Rabin's irreducibility test transcript: x^(p^d) ≡ x mod f, and gcd(x^(p^(d/ℓ)) − x, f) = 1 for each prime ℓ | d. Anyone can recompute it, and it needs no basis. Irreducibility is always `full`. Only the running-time guarantee depends on the basis.

**Complexity:**
- Covered degrees: O(log² p) non-residue candidates per ℓ, then O(1) polynomial construction, so deterministic poly(log p) + O(d) to write out the binomial. Before, there was no deterministic polynomial-time guarantee for large p.
- Composed products cost Õ(d²) field operations with resultant methods.
- Uncovered degrees: as before.

## Open questions

- Read the cited Bach FOCS 1985 theorem and confirm the hypothesis behind Adleman–Lenstra Proposition 3.
- Composed products of three or more factors: check the coprimality bookkeeping and cost.
- Is binomial form acceptable to callers? Some protocols want a sparse or low-weight polynomial, and binomials are as sparse as possible.
