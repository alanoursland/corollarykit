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
| OpenAI quasi-GRH (Oct 6) | No zeros with Re s > 7/8 for zeta and all Dirichlet L-functions (the repo copy states 11/12) | `claimed` |
| OpenAI no-Siegel-zeros (Oct 6) | Siegel zeros do not exist for zeta and many Dirichlet L-functions | `claimed` |
| OpenAI strongly polynomial LP (Nov 24) | Smale's 9th problem | `claimed` (Lean covers rational inputs) |
| ETH disproof (Oct) | Subexponential #k-SAT | `claimed` |
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

## Shared design rule

Every function declares its **bases**: the theorems it relies on, each with an explicit bound and a status. A strict policy uses only `classical` bases and falls back to unconditional algorithms. Where possible, output carries a certificate that can be checked without trusting any of the new results.
