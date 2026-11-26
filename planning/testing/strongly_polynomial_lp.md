# Testing: `solve_lp_exact(A, b, c)`

Plan: [../strongly_polynomial_lp.md](../strongly_polynomial_lp.md). Stage: research. This plan applies once the algorithm's phases are specified.

## 1. Reference values

- Netlib instances small enough to run, with exact optima (Koch 2004).
- **Hand-built families:**
  - Klee–Minty cubes (bad for simplex);
  - the Hirsch-violating polytopes from the companion OpenAI paper, once they are extracted;
  - LPs that are infeasible, unbounded, or have degenerate optima.

## 2. Oracle comparison

- Exact SoPlex and our vertex-enumeration solver, on random small LPs. The status must match; optimal values must match exactly.

## 3. Properties

- **Every output passes `check_lp_certificate`.** This is the primary correctness test, and it needs no trust in the solver.
- The certificate forms are those the paper states:
  - a strictly complementary pair (s + y > 0 checked);
  - a feasible point plus a ray;
  - a Farkas vector with |supp y| ≤ 1 + rank A.

  The checker's base checks are not enough here, so extra assertions cover these.

## 4. Edge cases

- Rank-deficient A, redundant constraints, m ≫ n, n ≫ m, all-zero c.
- Equal-dimension LPs with coefficient bit lengths from 4 to 4096 bits. This is the axis the algorithm claims not to depend on.

## 5. Bases and policy

- The result reports basis `openai-strongly-poly-lp-2026` (`claimed`) for the operation-count guarantee only. Correctness never depends on it, since the certificate is checked.

## 6. Certificates

- See section 3. The solver's certificate is always run through the checker before it's returned. A failure is an `InconsistencyError`, never a returned answer.

## 7. Failure paths

- Fault injection: corrupt the output of an internal phase (calibration basis, witness recovery). The final checker must catch it, or the solver must recover. It must never return an invalid certificate.

## 8. Performance: the actual scientific test

Count **arithmetic operations** with an instrumented rational type, separately from wall time.

1. Fix (m, n) and vary the bit length of A, b and c from 4 to 4096. The claim is a flat operation count. Plot it.
2. Fix bit length and vary (m, n). Fit the exponent and compare it with the paper once the paper's exponent is found.
3. Track the largest intermediate bit length. It must stay polynomial in the input length.
4. Compare wall time with HiGHS and exact SoPlex across the same grid, and report the crossover, if there is one.
