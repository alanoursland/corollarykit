# Testing: `count_sat_subexp(cnf)`

Plan: [../sat_count_subexp.md](../sat_count_subexp.md). Stage: research. One algorithm must be chosen and its recurrences extracted first.

## 1. Reference values

- Small formulas with known counts: SATLIB uf20/uf50 (satisfiable random 3-SAT), uuf (unsatisfiable, count 0), and model-counting competition instances small enough to run.
- **Closed forms:** the empty formula (2ⁿ), single clauses (2ⁿ − 2^(n−k)), contradictory unit clauses (0), and pigeonhole formulas (0).

## 2. Oracle comparison

- Brute-force enumeration for n ≤ 20.
- sharpSAT-TD or d4 for n ≤ 200, where installed.

## 3. Properties

- Count invariance under variable renaming, clause reordering and literal reordering.
- Inclusion–exclusion: count(F) = count(F ∧ x) + count(F ∧ ¬x).
- Adding a clause never increases the count.

## 4. Edge cases

- Empty clauses, duplicate literals, tautological clauses, variables that never appear, k = 1 and k = 2.

## 5. Bases and policy

- The running-time claim reports a basis (`claimed`). The count itself is exact arithmetic and is checked against oracles.

## 6. Certificates

- No compact certificate exists for #SAT. The tests rely on oracles and on the properties in section 3.

## 7. Testing the algorithm's own steps (not the fallbacks)

On small inputs the algorithm may take its brute-force fallback branches. So:
- Expose each phase through internal APIs. For the Anthropic route: tensor-network construction, the signed-sum rewrite and contraction. For the OpenAI route: sparsification, bounded occurrences, spectral replacement and rational interpolation.
- Test each phase on its own, against a direct computation: contraction value against brute-force summation; interpolation against known polynomial values.
- **Coverage gate:** `scripts/check.sh` fails if the main (non-fallback) branch of each phase isn't executed by some test.

## 8. Performance

- Measured operation counts against n, compared with the predicted cost model. The goal is to validate the crossover analysis (Majdoddin's estimates), not to be fast.
