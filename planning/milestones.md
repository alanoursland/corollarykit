# Milestones

Each milestone ends in a git tag (`m0`, `m1`, …) and has explicit **exit criteria**. **Nothing is published to PyPI until the very end** (see [Publishing](#publishing-at-the-end)). A milestone is done only when every criterion holds under `scripts/check.sh`, which tests the built wheel. The project runs no GitHub Actions.

The order follows [architecture.md](architecture.md). The test requirements come from [testing/](testing/README.md).

The version in `__init__.py` stays at `0.0.x.devN` until publishing. API changes between milestones are allowed, but every change goes into `CHANGELOG.md`.

## Overview

| Milestone | Tag | Theme | Depends on |
|---|---|---|---|
| M0 | `m0` | Foundations: result types, base helpers, verifier skeleton | scaffold (done) |
| M1 | `m1` | LP certificate checker | M0 |
| M2 | `m2` | `prime_count_interval` | M0, T1 (partial) |
| M3 | `m3` | Primality core: `is_prime_miller`, `prove_prime` | M0, T1 (partial) |
| M4 | `m4` | Modular roots | M3 |
| M5 | `m5` | Prime search: `next_prime`, `least_prime_in_progression` | M3 |
| M6 | `m6` | `nth_prime_bounds`, `nth_prime` | M2 |
| M7 | `m7` | `factor_with_phi`, `primitive_root`, `irreducible_polynomial` | M3, M4 |
| M8 | `m8` | Hardening: downgrade drill, benchmarks, docs site | M1–M7 |
| R1 | `experimental` | Strongly polynomial LP solver | M1, research reads |
| R2 | `experimental` | Subexponential #SAT, unit-distance grid | M0, research reads |

There are also two **side tracks** that run alongside the code milestones (see below):
- **T1** transcribes the registry entries from their sources.
- **T2** reads the research papers.

M1 and M2 can proceed in parallel, and so can M3 and M6 once their dependencies are in.

## M0: Foundations

**Scope:**
- `results.py`: `Result`, `Claim`, `Scope`, and `Result.weakest()`.
- `_bases.py`: `select_bases`, `ceiling_upper`, and ceiling formulas declared alongside their basis ids.
- `_intmath.py`: `small_primes`, `sieve_segment`, `progression_sieve`, `jacobi`, `iroot`, `perfect_power`, `trial_divide`, `prime_count_exact`.
- `tests/verify/` skeleton, with its own naive arithmetic.
- Test infrastructure: pytest markers (`slow`, `bench`, `oracle_*`), Hypothesis settings, and `tests/data/` with provenance headers. No scheduled workflow: slow tests are run by hand.
- Registry schema: add the `checked_against` field and the formula field.

**Exit criteria:**
- `testing/registry.md` sections 1, 2 and 4 pass, including the exhaustive policy truth table.
- `_intmath` is tested against naive implementations: every function on all inputs up to 10⁵, plus property tests.
- The **verifier import lint** is in the test suite and fails on a deliberate violation.
- `ceiling_upper` is tested against Arb (where installed) at 10⁴ points and is never below the true value.
- The default `pytest` run takes under 60 s.

## M1: LP certificate checker

**Scope:**
- `check_lp_certificate` for standard form, per [specs/lp_certificate_checker.md](specs/lp_certificate_checker.md).
- The second, naive checker in `tests/verify/`.

**Exit criteria:**
- Every item in `testing/lp_certificate_checker.md`, except Netlib (which needs MPS and repair, so it comes later).
- The ray-without-a-feasible-point case is rejected.
- No surviving mutants in `certificate.py` in a manual `mutmut` run.
- The README shows a working checker example.

**Why it comes first:** it needs no 2026 result and no registry transcription, and it is useful straight away.

## M2: `prime_count_interval`

**Scope:**
- The spec [specs/prime_count_interval.md](specs/prime_count_interval.md), updated to the multi-claim result type (`bound_lo` and `bound_hi` claims).
- `_balls.py`.
- The `arb` extra.

**Needs from T1:** `rosser_schoenfeld1962.*`, `dusart2010.*` and `schoenfeld1976` transcribed and marked `transcription_checked = true`, each with `checked_against`.

**Exit criteria:**
- Everything in `testing/prime_count_interval.md`, including the basis-switching boundaries and the fake-basis `InconsistencyError` path.
- π(10⁸) in under 1 s in pure Python, and analytic x = 10¹⁰⁰⁰ in under 10 ms. Both are measured with a manual `pytest -m bench` run.
- Under `DEFAULT`, results never cite `schoenfeld1976`. Under `ACCEPT_RH_ALPOGE` they do for x ≥ 10¹².

## M3: Primality core

**Scope:**
- `_miller.miller_sequence`.
- `_search.bach_scan`.
- `is_prime_miller`, with separate policy switches for the fixed-base and GRH ranges.
- `prove_prime`: trial division, then BPSW as a reject-only filter, then fixed bases, then Miller under GRH. `BasisNotAccepted` when nothing applies.
- PARI for the tests: install PARI/GP locally (for example from apt) before `pip install`, then add `cypari2` back to the `oracles` extra. M0 removed it because pip falls back to a source build that fails on Python 3.11 without PARI.

**Needs from T1:** `sorenson_webster2017`, `bach1990.miller` and `bach1990.subgroup`.

**Exit criteria:**
- Everything in `testing/is_prime_miller.md`:
  - ψ₁ to ψ₁₃ reported composite, with witnesses;
  - a sample of the Feitsma–Galway list in the fast tier, and the full list in a manual full run;
  - perfect powers caught before the Miller step;
  - agreement with PARI `isprime` on 10⁴ random 82–400-bit inputs.
- The stub-BPSW test: a BPSW that wrongly accepts a composite never produces a `Prime` result.
- The benchmark table (128, 256 and 1024 bits, against PARI) is published in the docs. **It decides the advertised useful range.**

**Risk:** this is the riskiest milestone, since five later functions depend on `prove_prime`. Plan for a review by someone other than the author before tagging.

## M4: Modular roots

**Scope:**
- `least_nonresidue(p, ℓ)`.
- `sqrt_mod_prime`, including p = 2, Atkin's method for p ≡ 5 (mod 8), and the input contract `verify_prime`.
- `nth_root_mod_prime`. Its spec must first define the algorithm:
  - test a^((p−1)/d) with d = gcd(r, p−1);
  - factor d;
  - handle prime powers;
  - assemble the root.

**Needs from T1:** `bach1990.nonresidue`.

**Exit criteria:**
- Everything in `testing/modular_roots.md`, including the A000229 least-non-residue records below the ceiling.
- A test shows that only prime candidates are scanned.

## M5: Prime search

**Scope:**
- `_search.bounded_search`.
- `next_prime` and `prime_exists_between`.
- `least_prime_in_progression`, `ntt_prime` and `prime_with_residue`. The companion functions get explicit budgets and a no-result value, since the least-prime theorem gives them no ceiling.

**Needs from T1:** `cms2019`, `lls2015` and `bach_sorenson1996`, each with its exact domain of q. Also the Dusart 2018 gap bound, as the classical fallback.

**Exit criteria:**
- Everything in `testing/next_prime.md` and `testing/least_prime_in_progression.md`:
  - record prime gaps through 2⁶⁴ below the ceiling;
  - the edge cases (2, 3) → 2, (5, 6) → 5 and q = 1 → 2;
  - `full` minimality certificates checked by the independent verifier.
- Results carry separate `primality`, `minimality` and `termination` claims, and the composition test passes.

## M6: n-th prime

**Scope:**
- `nth_prime_bounds`, with integer tightening predicates where each side keeps its classical endpoint until a tighter one is proven.
- `nth_prime`, sieving the half-open interval (lo, hi].
- Choose the exact-counting backend: the pure-Python fallback up to 10¹², or `primecount` when installed.

**Exit criteria:**
- Everything in `testing/nth_prime.md`, including n = 2 with bracket [2, 3] returning 3, and an undecidable Arb comparison that keeps the proven endpoint.
- The measured sieve window under the RH bracket against the classical one is measured with a manual `pytest -m bench` run. That is the gain this milestone claims.

## M7: Factoring and finite fields

**Scope:**
- `factor_with_phi`.
- `_factor.factor_small`, and `primitive_root`. Validate supplied factorizations, handle p = 2, and use no numeric Shoup ceiling.
- `_polyfp` and `irreducible_polynomial`: the binomial route, the Artin–Schreier route, composed products, and the fallback scan.

**Needs from T1:** `miller1976.phi` (including the check that non-splitting bases lie in a proper subgroup) and `lidl_niederreiter.binomial`.

**Exit criteria:**
- Everything in `testing/factor_with_phi.md`, `testing/primitive_root.md` and `testing/irreducible_polynomial.md`.
- Every `irreducible_polynomial` output is confirmed irreducible by PARI and by the independent verifier's Rabin transcript.

## M8: Hardening

**Scope:**
- The **downgrade drill**, done for real: mark `alpoge-claude-2026` as `claimed` in a test registry, then run the entire suite under `ACCEPT_RH_ALPOGE`. Every answer must stay correct, and every reported basis must change accordingly.
- Benchmark results recorded per milestone tag, from manual `pytest -m bench` runs.
- Documentation site:
  - a page per function, with its bases table, the inputs covered, its claims and their scopes, and the measured performance (Astra's per-API table);
  - a "which hypothesis does this need" page, covering the Dirichlet, Dedekind and Hecke distinctions and the out-of-scope list.
- Public API review, ahead of 1.0.

**Exit criteria:**
- The drill passes.
- Every public function has a docs page with a bases table.
- No `transcription_checked = false` basis is reachable from a public function under `DEFAULT`.
- An API freeze candidate is written down.

## Side track T1: Registry transcription

This is not code. It runs ahead of the milestone that needs each basis.

For each basis:
1. Read the cited source.
2. Copy the statement, constants and domain exactly.
3. Record `checked_against`: the page, theorem or equation, plus the checker's name.
4. Flip `transcription_checked = true` **in a commit of its own**, with the citation in the message.

A second person checks it in review.

| Needed by | Bases |
|---|---|
| M2 | `rosser_schoenfeld1962.lower`, `.upper`; `dusart2010.lower`, `.upper`; `schoenfeld1976` |
| M3 | `sorenson_webster2017`; `bach1990.miller`; `bach1990.subgroup` |
| M4 | `bach1990.nonresidue` |
| M5 | `cms2019`; `lls2015`; `bach_sorenson1996` (domain); Dusart 2018 gap bound (add to registry) |
| M7 | `miller1976.phi`; `lidl_niederreiter.binomial` |

Separately, the **statement match for `alpoge-claude-2026`**, which is a mathematical review task, beyond transcription:
- **RH: done externally.** The Lean FRO and Mathlib Initiative (Nov 21) confirmed with two independent tools that the theorem is exactly Mathlib's vetted `RiemannHypothesis`. Recorded as `statement_match = "checked"` with the citation. Still open: the shortened editions were checked against a newer Mathlib version than the original, and that equivalence hasn't been checked formally.
- **Dirichlet GRH: partial.** It was checked only against custom definitions in the challenge file's `Statements.lean`, and Mathlib has no vetted GRH definition. Remaining task: review those definitions against the statements our bases use (all moduli, all characters, zeros with Re s > 1/2 excluded). Until then `statement_match = "partial"` and the proof counts as `claimed` for every Dirichlet-GRH basis.
- In either case the proof stays `lean-compiled`, not `peer-verified`, until a human audit of the argument is published.

## Side track T2: Research reads

These gate the research milestones and some open questions. Each one produces a short note in `planning/notes/`.

| Read | Unblocks |
|---|---|
| OpenAI strongly polynomial LP paper (full PDF): operation-count exponent, inner-LP subroutine, calibration, and whether N in H = 2^(100N²) is the dimension or the input size | R1 |
| One #SAT paper (pick Anthropic's or OpenAI's), with its recurrences and base cases | R2 |
| Cogentic 1/5-approximate Nash paper: algorithm, complexity, and whether it is practical | a possible plan file (see planning README, Candidates) |
| Bach (with co-author), FOCS 1985: the hypothesis behind Adleman–Lenstra Proposition 3 | `irreducible_polynomial` fallback options |
| Buchmann–Shoup, full text: confirm the ERH it assumes | `irreducible_polynomial`, registry note |
| Shoup 1992: an explicit constant for the least-primitive-root bound | a numeric `primitive_root` ceiling |
| OpenAI quasi-GRH paper: re-derive the non-residue exponent for σ₀ = 11/12 | the quasi-GRH basis in M4 |
| Small-n maximum unit-distance counts: a source | R2 tests |

## R1, R2: Research milestones

These ship only under `corollarykit.experimental`, and only after their T2 reads produce a spec.
- **R1 exit:** every output passes `check_lp_certificate`, and the operation-count-against-bit-length experiment from `testing/strongly_polynomial_lp.md` section 8 is published.
- **R2 exit:**
  - `erdos_grid` and `unit_distance_count` meet `testing/unit_distance.md`;
  - the #SAT prototype meets the phase-coverage gate in `testing/sat_count_subexp.md`;
  - the crossover measurements are published.

## Toward 1.0

1.0 requires:
1. M1–M8 done.
2. The API unchanged across one full milestone, with no breaking changes.
3. At least one outside review of `prove_prime` and the registry policy logic.

1.0 doesn't require any 2026 result to be confirmed. The default policy is correct either way. A confirmation changes only which bases `DEFAULT` accepts, through a registry update in a later minor release.

## Publishing (at the end)

The first PyPI upload is 1.0, once the requirements above are met. There are no intermediate PyPI releases. Until then, people who want to try it install from a git checkout.

Procedure, run locally (the project uses no GitHub Actions):
1. Check that the name `corollarykit` is still free on PyPI. If it has been taken, pick a new name. Nothing is reserved early.
2. `scripts/check.sh --full --python python3.11 --python python3.12 --python python3.13`.
3. Set the version to `1.0.0` and finalize `CHANGELOG.md`.
4. `python -m build`, then upload to TestPyPI and install from there into a fresh venv as a smoke test.
5. `twine upload` to PyPI, using a project-scoped API token kept in the maintainer's keyring, never in the repository.
6. Tag the commit `v1.0.0`.
