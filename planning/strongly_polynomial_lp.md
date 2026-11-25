# `solve_lp_exact(A, b, c)`

Solve max cᵀx subject to Ax ≤ b exactly, over the rationals, using a number of arithmetic operations that depends only on the dimensions and not on how large the numbers are. The output is always a certificate that `check_lp_certificate` can verify.

## Old implementation

Let m be the number of constraints, n the number of variables, and L the total bit length of the input.

| Method | Arithmetic operations | Strongly polynomial? |
|---|---|---|
| Simplex (any known pivot rule) | exponential worst case (Klee–Minty); polynomial smoothed (Spielman–Teng) | no |
| Ellipsoid (Khachiyan 1979) | O(n⁴ L) | no: depends on L |
| Interior point (Karmarkar 1984 and successors) | O(n^3.5 L) | no |
| Modern interior point (Cohen–Lee–Song 2019; van den Brand 2020) | Õ(n^ω · log(n/δ)), about Õ(n^ω L) for exact solutions | no |
| Tardos (1986) | poly(m, n, size of A), independent of b and c | only when A has small entries |
| Vavasis–Ye (1996), layered least squares | poly(m, n, log χ̄_A) | only for well-conditioned A |
| Dadush et al. (2024) | strongly polynomial | only with at most two non-zeros per column |

Every general method has an operation count that grows with L. Whether LP can be solved in strongly polynomial time was Smale's 9th problem.

## What changes it

**OpenAI, "Strongly polynomial linear programming" (Nov 24 2026, `claimed`)** is in `openai/math` at `preprints/Strongly-polynomial-linear-programming-November-24-2026/`. It works in the real-number (BSS) model with arbitrary real coefficients.

Stated theorem (from `introduction.tex`): a deterministic strongly polynomial algorithm returns one of these certificates:
1. A strictly complementary primal–dual pair (x, y), with slack s + y > 0.
2. An unbounded ray r: Ar ≤ 0 and cᵀr > 0.
3. A Farkas vector y ≥ 0 with Aᵀy = 0, bᵀy < 0, and |supp y| ≤ 1 + rank A.

**Lean:** comparator theorems `OAI.Optimization.LinearProgramming.strongly_polynomial_feasibility` and `..._optimization`. They cover **rational inputs only**: instruction count polynomial in m + d, and stored rationals of bit length polynomial in the input length. The real-coefficient case is not formalized. They use only the standard axioms (propext, Quot.sound, Classical.choice).

The companion paper (same day) gives a Lean-checked family of simple polytopes with superpolynomial diameter, disproving the polynomial Hirsch conjecture. So no simplex pivot rule can be strongly polynomial. The new algorithm is not a simplex method.

## New implementation

This outline is read from `lp.tex` and still has to be checked against the full paper:
1. Homogenize and work in slack space. Split it into a subspace C and its orthogonal complement. At each coordinate, exactly one side has a witness.
2. **Calibration:** reciprocal diagonal scaling D (with D_{i+}·D_{i−} = 1) produces an approximate basis B. Its accuracy is 2^(−P), with at most poly(N, P) restarts.
3. **Labels:** a "short-rational" LP test over {y = ξB : ‖ξ‖∞ ≤ H, −ε ≤ y_s ≤ 2}. This step calls an ordinary weakly polynomial LP solver on inputs whose bit lengths are controlled.
4. **Witness recovery:** zero coordinates one at a time, keeping each restriction that preserves the side test, until a line remains. Linear algebra then recovers the circuit.
5. **Strict complementarity:** one mixed feasibility problem: Ax ≤ b, y ≥ 0, Aᵀy = c, bᵀy = cᵀx, b − Ax + y > 0.

We will implement it in exact rationals (the formalized case), with an interior-point or exact-simplex subroutine for step 3, and run **every output through `check_lp_certificate`**.

**Complexity:**
- The claim is poly(m, n) arithmetic operations, with intermediate bit lengths polynomial in L. We have not found the exponent yet.
- The internal parameters are large: H = 2^(100N²), ε = H^(−10), 2^(−P) = H^(−100). With N = 100 that means numbers about 10⁶ bits long inside the subroutines.
- Expect it to be much slower than HiGHS or Gurobi in practice. Its value is the guarantee that the operation count doesn't depend on the bit length. Benchmarks should vary dimensions and coefficient bit length separately, as Astra suggested.

## Testing

- Every output must pass `check_lp_certificate`.
- Results must agree with exact SoPlex on Netlib, and on families built to have huge coefficients and small dimensions. That is where this algorithm should eventually win.

## Open questions

- Read the full PDF: we need the exact operation-count exponent, the subroutine used in step 3, and the parts not yet read (calibration, compression, prices).
- Is N in H = 2^(100N²) the dimension or the input size? This decides whether it can be implemented at all for n in the hundreds.
- Status: `claimed`. No outside review yet.
