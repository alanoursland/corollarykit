# `check_lp_certificate(problem, certificate)`

Check with exact rational arithmetic that a claimed LP outcome is correct: optimal, infeasible, or unbounded. This works for output from any solver: HiGHS, Gurobi, SciPy, SoPlex, or our own `strongly_polynomial_lp`.

## Old implementation

Most solvers work in floating point and report a status with tolerances. They don't give an exact proof. Exact options exist but are niche:
- SoPlex and QSopt_ex use iterative refinement or exact rational simplex.
- VIPR is a certificate format for mixed-integer programs.
- In practice users trust the float status, or re-solve with a second solver.

## What changes it

**No new mathematics.** This is infrastructure. It comes first because:
1. It is useful right now, whatever happens to the 2026 claims.
2. It is how we will validate the claimed strongly polynomial solver. Any output that solver produces must pass this checker.

## New implementation

The problem is in standard form, min cᵀx subject to Ax = b, x ≥ 0, after converting general forms. Everything uses `fractions.Fraction`, or `gmpy2.mpq` when installed.

| Claim | Certificate | Checks |
|---|---|---|
| Optimal, value v | primal x, dual y | Ax = b; x ≥ 0; Aᵀy ≤ c; cᵀx = bᵀy = v |
| Infeasible | Farkas vector y | Aᵀy ≤ 0 and bᵀy > 0 |
| Unbounded | feasible x, ray d | Ax = b, x ≥ 0; Ad = 0, d ≥ 0; cᵀd < 0 |

Extra pieces:
- **Rational repair:** given float x and y from a solver plus the optimal basis, solve the basis system exactly to recover rational x and y, then check them. That turns any solver's float answer into a proof when its basis is right.
- **Reporting:** for each failed check, report which constraint failed and by how much.

**Complexity:** O(nnz(A)) rational operations per check. The bit cost grows with the size of the entries. Rational repair adds one exact m×m solve: O(m³) operations with fraction-free Bareiss elimination, with polynomially bounded bit growth.

## Testing

- Netlib LP set with known exact optima (exact values published by Koch, 2004).
- Hand-built infeasible and unbounded cases.
- **A ray without a feasible point must be rejected.** In inequality form: maximize y subject to x ≤ 0 and −x ≤ −1. The ray (0, 1) passes the ray checks, but no feasible point exists, so an "unbounded" claim must fail. Claims that omit x₀, or give an x₀ that breaks a constraint, must fail.
- Both forms, standard (Ax = b, x ≥ 0) and inequality (Ax ≤ b), with their own certificate checks, so solver output never needs an untested conversion.
- Fuzzing: random LPs, solved with HiGHS through SciPy, repaired, then checked.

## Open questions

- What input format: MPS files, a NumPy or SciPy-sparse API, or both? Suggestion: an MPS reader plus a plain Python API.
