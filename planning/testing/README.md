# Testing plans

There is one file per algorithm. Each follows the same layers. A layer is left out only when it doesn't apply, and the file says why.

| Layer | What it shows | Where it runs |
|---|---|---|
| **1. Reference values** | Answers match published or independently computed values | every push |
| **2. Oracle comparison** | Answers match another implementation on many random inputs | every push (small); full run (large) |
| **3. Properties** | Invariants hold on generated inputs (Hypothesis) | every push |
| **4. Edge and adversarial cases** | Boundaries, degenerate inputs, the worst known inputs | every push |
| **5. Bases and policy** | Each policy uses exactly the bases it should; domain boundaries switch bases correctly; ceilings hold | every push |
| **6. Certificates** | An independent checker accepts every certificate we emit and rejects corrupted ones | every push |
| **7. Failure paths** | `InconsistencyError`, `BasisNotAccepted` and input validation behave as specified | every push |
| **8. Performance** | Cost stays within budget; complexity claims are measured, not assumed | run by hand; recorded, never pass/fail except budget regressions |

## Shared rules

**Independent verifier.**
- `tests/verify/` contains small checkers, one per certificate type.
- They **must not import** `corollarykit` outside `corollarykit.registry`. A lint rule enforces this.
- Certificates cross that boundary as plain data (dicts or tuples), so a bug in the library can't also hide in the checker.

**Oracles are optional dependencies, and the tests say so.**
- Markers: `oracle_sympy`, `oracle_pari` (cypari2), `oracle_flint`, `oracle_primecount`, `oracle_highs`.
- A test with a missing oracle is skipped, never silently passed. CI installs them all.

**Reference data is pinned.**
- Each file in `tests/data/` has a provenance header: source, URL, retrieval date and sha256.
- Large data sets are downloaded by `@slow` tests in a full run and checked against a pinned hash, not committed.

**Policy matrix.**
- Every algorithm test runs under `DEFAULT` and under `ACCEPT_RH_ALPOGE`.
- Until the registry transcriptions are checked, both run with a test-only `allow_unchecked_transcriptions=True` variant, and the test asserts which `basis` the result reports.

**Ceilings.**
- "Ceiling never reached" tests run on the known record inputs (largest least non-residue, largest prime gap, and so on).
- A **fake basis** with a deliberately false, too-small ceiling is injected through a test registry to show the `InconsistencyError` path fires.

**Determinism.**
- Hypothesis runs with a fixed database in CI and prints its seed.
- Any failure becomes a permanent `@example`.

**Mutation testing.**
- `mutmut` runs on the certificate checkers (LP checker and `tests/verify/`), by hand before each release.
- A surviving mutant in a checker is treated as a bug.

**Speed tiers.**
- Default `pytest` finishes in under 60 s.
- `-m slow` belongs to the **full run**, done by hand: `HYPOTHESIS_PROFILE=thorough pytest -m "slow or not slow"`. There is no scheduled automation.
- `-m bench` writes `pytest-benchmark` JSON. **Benchmarks are not run in CI for now**; run them by hand when a milestone needs a measurement.

## Files

| Algorithm | Plan |
|---|---|
| prime_count_interval | [prime_count_interval.md](prime_count_interval.md) |
| nth_prime_bounds, nth_prime | [nth_prime.md](nth_prime.md) |
| next_prime, prime_exists_between | [next_prime.md](next_prime.md) |
| sqrt_mod_prime, nth_root_mod_prime | [modular_roots.md](modular_roots.md) |
| primitive_root | [primitive_root.md](primitive_root.md) |
| least_prime_in_progression | [least_prime_in_progression.md](least_prime_in_progression.md) |
| is_prime_miller | [is_prime_miller.md](is_prime_miller.md) |
| factor_with_phi | [factor_with_phi.md](factor_with_phi.md) |
| irreducible_polynomial | [irreducible_polynomial.md](irreducible_polynomial.md) |
| check_lp_certificate | [lp_certificate_checker.md](lp_certificate_checker.md) |
| solve_lp_exact | [strongly_polynomial_lp.md](strongly_polynomial_lp.md) |
| count_sat_subexp | [sat_count_subexp.md](sat_count_subexp.md) |
| erdos_grid, unit_distance_count | [unit_distance.md](unit_distance.md) |
| registry and policies | [registry.md](registry.md) |
