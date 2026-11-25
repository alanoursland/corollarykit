# Planning

One file per algorithm. Each file covers:

1. **Old implementation**: what people do today and what it costs.
2. **What changes it**: the exact mathematical result, which hypothesis it settles, and its status.
3. **New implementation**: what we will write and what it costs.
4. **Testing** and **open questions**.

## Status vocabulary

Every 2026 result is tracked with one of these statuses. The library's assumption registry uses the same words.

| Status | Meaning |
|---|---|
| `classical` | Established, peer-reviewed mathematics. |
| `peer-verified` | Checked by named outside experts, not yet through journal review. |
| `lean-compiled` | A Lean formalization compiles against standard axioms, but nobody has yet confirmed that the formal statements match the claimed theorems. |
| `claimed` | Announced or posted, with no independent check yet. |

As of 2026-11-25:

| Result | Hypothesis settled | Status |
|---|---|---|
| Alpöge–Claude (Nov 20) | RH, and GRH for **Dirichlet** L-functions only (not Dedekind, Hecke or Artin) | `lean-compiled` |
| OpenAI quasi-GRH (Oct 6) | No zeros with Re s > σ₀ for zeta and all Dirichlet L-functions. The registry uses σ₀ = 11/12, as stated in the repository paper; the catalog says 7/8 | `claimed` |
| OpenAI no-Siegel-zeros (Oct 6) | Siegel zeros do not exist for zeta and many Dirichlet L-functions | `claimed` |
| OpenAI strongly polynomial LP (Nov 24) | Smale's 9th problem | `claimed` (Lean covers rational inputs) |
| ETH disproof (Oct; separate OpenAI and Anthropic claims) | Subexponential #k-SAT | `claimed` (under review by Impagliazzo, Paturi and Williams) |
| Unit distance disproof (May 20) | Erdős unit distance conjecture is false | `peer-verified` |

## Algorithms

### Number theory (core, Python first)

| File | API | Depends on |
|---|---|---|
| [prime_count_interval.md](prime_count_interval.md) | `prime_count_interval(x)` | RH |
| [nth_prime_bounds.md](nth_prime_bounds.md) | `nth_prime_bounds(n)` | RH |
| [next_prime.md](next_prime.md) | `next_prime(x)`, `prime_exists_between(a, b)` | RH |
| [sqrt_mod_prime.md](sqrt_mod_prime.md) | `sqrt_mod_prime(a, p)`, `nth_root_mod_prime(a, r, p)` | Dirichlet GRH |
| [primitive_root.md](primitive_root.md) | `primitive_root(p, factors)` | Dirichlet GRH |
| [least_prime_in_progression.md](least_prime_in_progression.md) | `least_prime_in_progression(a, q)` | Dirichlet GRH; no Siegel zeros |
| [is_prime_miller.md](is_prime_miller.md) | `is_prime_miller(n)` | Dirichlet GRH |

### Optimization

| File | API | Depends on |
|---|---|---|
| [lp_certificate_checker.md](lp_certificate_checker.md) | `check_lp_certificate(...)` | Nothing new. It checks the solver below and any other solver. |
| [strongly_polynomial_lp.md](strongly_polynomial_lp.md) | `solve_lp_exact(...)` | Strongly polynomial LP (Smale's 9th) |

### Experimental (`corollarykit.experimental`)

These are reference implementations of results whose gains only show up at sizes no one will ever compute. They are for researchers, not production use.

| File | API | Depends on |
|---|---|---|
| [sat_count_subexp.md](sat_count_subexp.md) | `count_sat_subexp(cnf)` | ETH disproof |
| [unit_distance_construction.md](unit_distance_construction.md) | `unit_distance_points(...)` | Unit distance disproof |

## Considered and dropped

- **Matrix multiplication (ω = 9/4).** Practical matrix multiplication uses the O(n³) algorithm, sometimes Strassen, tuned to the hardware. Exponent improvements below about 2.8 come with constants so large they never beat that at real sizes. A new exponent does not make `A @ B` faster.
- **Navier–Stokes, Sogge local smoothing, Kakeya, non-sofic groups, Connes rigidity, Hodge, Fermat's Last Theorem in Lean.** These are existence or analysis results with nothing to compute that is faster or better guaranteed. We could revisit Navier–Stokes as a solver stress test later.
- **General number-field class groups, units, and polynomial factoring over finite fields.** These need GRH for Dedekind, Hecke or Artin L-functions, which the November proof does not cover. They stay conditional.

## Shared design rules

### Bases

A **basis** is a single theorem that an algorithm relies on. Every function declares its bases, and every result reports the **one basis it actually used**. "Unconditional" in these plans means only "proved by a basis whose status the active policy accepts." No plan should call a bound unconditional without saying which basis it rests on.

Each basis record holds:

| Field | Example |
|---|---|
| `id` | `bach1990.miller` |
| `statement` | exact text of the bound, with its constant and domain: "if n is an odd composite, not a prime power, some a < 2(ln n)² is a strong witness" |
| `hypothesis` | the exact hypothesis, by L-function family: `GRH-dirichlet`, `RH`, `zero-free(Re s > σ₀, dirichlet)`, `no-siegel-zeros`, or `none` |
| `hypothesis_source` | paper, version or date, and for Lean the theorem name and commit: Alpöge, alpo.ge/remark.pdf + Lean archive, 2026-11-20 |
| `status` | from the vocabulary above |
| `statement_match` | whether anyone has checked that the formal or claimed statement implies `statement`: `unchecked`, `checked-by:<who>` |

**Rules:**
- A `lean-compiled` basis with `statement_match = unchecked` is treated as `claimed` by the default policy. It is accepted only when the user turns it on explicitly.
- When sources disagree on a statement, the registry uses the **weaker** one. Quasi-GRH is recorded as σ₀ = 11/12, which is what the paper in OpenAI's repository states. 7/8 appears only in OpenAI's catalog and press coverage, and is noted as an alternative statement.

### Certificate scope

Every certificate declares what an independent checker can establish from it:

- **`membership`:** the output has the required property: it is prime, it lies in the progression, or it is a primitive root. Checking this needs no 2026 result.
- **`full`:** the whole claim, including minimality ("least ..."). This needs a witness that rules out every smaller candidate.
- **`basis`:** the claim depends on a theorem (a search ceiling or a no-witness-exists bound), so a checker must trust the named basis.

Where it's affordable, an output carries a certificate that can be checked without trusting any of the new results.
