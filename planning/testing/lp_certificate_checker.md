# Testing: `check_lp_certificate(problem, cert)`

Spec: [../specs/lp_certificate_checker.md](../specs/lp_certificate_checker.md)

The checker is a trusted component, so it gets the heaviest testing.

## 1. Reference values

- **Hand-built cases:** one valid certificate of each type (optimal, infeasible, unbounded), with the expected objective.
- **Netlib, with exact optima** (Koch 2004, "The final NETLIB-LP results"): once an MPS reader and rational repair exist, every instance's certificate built from exact SoPlex output must validate, and the objective must match Koch's value exactly. Until then, full runs only.

## 2. Oracle comparison

- Random LPs (m, n ≤ 6; integer entries in [−5, 5]) solved exactly by brute-force vertex enumeration in Fractions. That gives a correct status and certificate, which the checker must accept.
- The same LPs solved with HiGHS (`oracle_highs`). Where its float status disagrees with the exact one, the checker's verdict on any certificate built from the float solution must agree with the exact status.

## 3. Properties

- **Soundness:** for any certificate, `valid=True` implies the claim is true, judged by brute-force exact solving on small LPs. Hypothesis generates certificates directly, including random nonsense, not only near-correct ones.
- **Completeness:** every true claim has a certificate the checker accepts. Build it by exact solving.
- **Perturbation:** change one coordinate of a valid certificate by ±1/7. The result must be invalid unless it is still genuinely correct, confirmed independently.
- **Failure reporting:** for a certificate breaking exactly one check, `failures` has exactly that `check` and `index`.

## 4. Edge cases

- **Ray without a feasible point:** min −x₂ subject to x₁ = −1, with `Unbounded(x=(−1,0), d=(0,1))`. It must fail `primal_nonneg`.
- m = 0, n = 0, an empty A, a zero row, a zero column, duplicate COO entries (summed), explicit zeros.
- A degenerate optimum with multiple dual solutions: every one is accepted.
- Huge rationals: entries with 10⁴-digit numerators. Checks the bit-cost path, and must finish within budget.
- **Wrong lengths** in the certificate: a `shape` failure, not an exception. Wrong lengths in the problem: `ValueError`.
- **Types:** a float raises `TypeError`; `coerce_float=True` accepts it exactly; a bool is rejected; `gmpy2.mpq` is accepted when installed.

## 5. Bases and policy

Not applicable: the checker uses no basis. A test asserts that it never consults the registry.

## 6. Certificates

The checker *is* the verifier. To check the checker:
- **Second implementation:** a deliberately naive second checker in `tests/verify/` (dense matrices, no early exits). The two must agree on every generated case.
- **Mutation testing:** `mutmut`, run by hand before each release. No surviving mutants in `certificate.py`.

## 7. Failure paths

- `max_failures` caps the list; `max_failures=0` behaves as specified.
- The checker never raises on a malformed certificate. Fuzz it with arbitrary objects in every field.

## 8. Performance

- Check time against nnz(A), from 10³ to 10⁶, with small and with large rationals. It should be linear in nnz for fixed entry size.
