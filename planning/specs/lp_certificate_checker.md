# Spec: standard-form LP certificate checker (v1)

Scope: check exact certificates for **min cᵀx subject to Ax = b, x ≥ 0**.

Out of scope for v1, each to get its own spec later:
- inequality form (Ax ≤ b);
- general-form conversion, with its mapping back to the original variables and constraints;
- rational repair (it needs the solver's basis, not just float vectors);
- MPS input.

The checker must stay small, around 200 lines, and use only the standard library, so it can be audited on its own. It is the trusted part of the LP work.

## Module and API

`corollarykit/lp/certificate.py`

```python
def check_lp_certificate(problem: StandardFormLP, cert: Certificate, *, max_failures: int = 10) -> CheckResult
```

## Input types

**Scalars:** `int` or `fractions.Fraction`. `gmpy2.mpq` is accepted if installed, and is converted to `Fraction` on entry.
- A `float` raises `TypeError`, because the binary value is rarely what the caller meant. `coerce_float=True` converts floats exactly with `Fraction(f)`.
- `bool` is rejected.

**`StandardFormLP(m, n, A, b, c)`:**
- `A` is a sparse matrix given as COO triples: `rows: Sequence[int]`, `cols: Sequence[int]`, `vals: Sequence[scalar]`.
- `A.from_dense(list[list[scalar]])` is offered for convenience.
- Duplicate (i, j) entries are summed. Explicit zeros are allowed.
- `b` has length m. `c` has length n.

Validation when constructing the problem: indices must be in range, lengths must match, and m, n ≥ 0. Any violation raises `ValueError`. **A malformed problem is a caller error.**

## Certificates

Plain dataclasses. A certificate usually comes from an untrusted solver, so **a malformed certificate produces failures, not exceptions.**

| Claim | Fields | Checks, each exact |
|---|---|---|
| `Optimal` | `x` (length n), `y` (length m), `value` (optional) | (1) Ax = b, row by row. (2) xⱼ ≥ 0. (3) Reduced costs cⱼ − (Aᵀy)ⱼ ≥ 0. (4) cᵀx = bᵀy. (5) If `value` is given, it equals cᵀx. |
| `Infeasible` | `y` (length m) | (1) (Aᵀy)ⱼ ≤ 0 for all j. (2) bᵀy > 0. |
| `Unbounded` | `x` (length n), `d` (length n) | (1) Ax = b. (2) x ≥ 0. (3) Ad = 0. (4) d ≥ 0. (5) cᵀd < 0. |

Why each one is sufficient, so reviewers can check the logic:
- **Optimal:** weak duality gives cᵀx′ ≥ bᵀy for every feasible x′. Equality means x is optimal and y is dual-optimal.
- **Infeasible:** a feasible x would give bᵀy = (Aᵀy)ᵀx ≤ 0.
- **Unbounded:** x + t·d stays feasible for every t ≥ 0, and its objective goes to −∞. **x is required.** A ray alone proves nothing.

Wrong vector lengths produce a `shape` failure, and the remaining checks for that certificate are skipped.

## Output

```python
@dataclass(frozen=True)
class Failure:
    check: str                          # "primal_eq", "primal_nonneg", "dual_feas", "duality_gap", "value",
                                        # "farkas_dual", "farkas_obj", "ray_eq", "ray_nonneg", "ray_obj", "shape"
    index: int | None                   # row or column involved, if any
    lhs: Fraction
    rhs: Fraction                       # the failed relation is lhs <op> rhs

@dataclass(frozen=True)
class CheckResult:
    valid: bool
    claim: str                          # "optimal" | "infeasible" | "unbounded"
    failures: tuple[Failure, ...]       # empty iff valid; capped at max_failures
    objective: Fraction | None          # cᵀx when the claim is optimal or unbounded and the shapes are OK
```

Every check runs, until `max_failures` is reached, so a caller sees all the problems at once.

## Complexity

**Rational operations:** one pass over A for Ax, another for Aᵀy or Ad, and O(m + n) for the rest. That is **O(nnz(A) + m + n)** rational operations.

**Bit cost:** grows with the entry sizes, since Fraction normalizes with a gcd at each step. For large rationals, accumulate each row sum over a common denominator, then reduce once.

## Tests

1. **Hand-built cases:** one valid certificate of each type. For each, change one entry so that exactly one check fails, and assert that check and index are reported.
2. **Ray without a feasible point:** min −x₂ subject to x₁ = −1. A = [[1, 0]], b = [−1], c = [0, −1]; this LP is infeasible.
   - `Unbounded(x=(−1, 0), d=(0, 1))` passes every ray check but must fail `primal_nonneg`.
   - `Unbounded` with a wrongly sized x must fail `shape`.
   - `Infeasible(y=(−1,))` must pass: Aᵀy = (−1, 0) ≤ 0 and bᵀy = 1 > 0.
3. **Degenerate shapes:** m = 0 (no constraints), n = 0, empty A.
4. **Property test:** generate random small LPs (m, n ≤ 4, small integers). Solve them exactly by enumerating vertices with Fractions, construct the matching certificate, and check that it is valid. Then perturb one coordinate at random and check that the result becomes invalid, or stays valid only when the perturbed certificate is still genuinely correct (confirmed by re-solving).
5. **Type tests:** a float raises `TypeError`; with `coerce_float=True` it is accepted exactly; `bool` is rejected.

## What an independent verifier gets

The checker *is* the verifier. A `valid=True` result is a complete proof of the claim, with no basis, assuming only that this code and Python's `Fraction` are correct. Nothing in it depends on any 2026 result.
