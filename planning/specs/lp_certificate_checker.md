# Spec: standard-form LP certificate checker (v1.1)

Scope: check exact certificates for **min cᵀx subject to Ax = b, x ≥ 0**.

v1.1 folds in the nine amendments from [../implementation/m1.md](../implementation/m1.md#spec-amendments-made-in-pr-1).

Out of scope for v1, each to get its own spec later:
- inequality form (Ax ≤ b);
- general-form conversion, with its mapping back to the original variables and constraints;
- rational repair (it needs the solver's basis, not just float vectors);
- MPS input.

The checker must stay small and use only the standard library, so it can be audited on its own. It is the trusted part of the LP work.

## Module and API

`corollarykit/lp/certificate.py`, also available as `corollarykit.check_lp_certificate`:

```python
def check_lp_certificate(problem: StandardFormLP, cert: object, *,
                         max_failures: int | None = 10, coerce_float: bool = False) -> CheckResult
```

- `problem` must be a `StandardFormLP`. Anything else raises `TypeError`, since that is a caller error.
- `max_failures` must be an int ≥ 1, or None for no limit. Anything else raises `ValueError`.
- **`cert` can be anything.** The function never raises because of the certificate.

## Input types

**Accepted scalars:** `int`, `fractions.Fraction`, and any `numbers.Rational` (for example `gmpy2.mpq` or `numpy.int64`). Every accepted scalar is normalized to a base `Fraction` before any arithmetic. Subclasses of int and Fraction are converted too, so their own arithmetic never runs.
- `bool` is rejected.
- A finite `float`, or a float subclass, is accepted only with `coerce_float=True`, and is converted exactly with `Fraction(f)`. So `0.1` becomes 3602879701896397/36028797018963968, not 1/10.
- NaN and ±inf are always rejected.

**Rejected scalars:**
- In the **problem**, a rejected scalar raises `TypeError`.
- In a **certificate**, it is a `type` failure.

**`SparseMatrix(m, n, rows)`:** `rows[i]` is a tuple of `(j, a_ij)` pairs. Invariants, enforced on **every** construction path, including a direct call:
- `rows` has exactly m entries;
- column indices are ints, in range, and strictly ascending;
- values are nonzero base `Fraction`s.

Two factories are provided:
- `SparseMatrix.from_coo(m, n, rows, cols, vals)`: duplicate (i, j) entries are summed, and explicit zeros are allowed and dropped.
- `SparseMatrix.from_dense(rows, n=None)`: `n` is required when there are no rows.

**`StandardFormLP(A, b, c)`:** `A` must be an exact `SparseMatrix`, not a subclass. `b` and `c` are tuples of base `Fraction`s of lengths m and n. `StandardFormLP.build(A, b, c)` also accepts a dense `A` and passes `n = len(c)`, so `build([], [], [1])` is one variable with no constraints.

Any invalid problem raises `ValueError` or `TypeError`. **A malformed problem is a caller error.**

## Certificates

Plain dataclasses, with no validation when they are built:

| Claim | Fields |
|---|---|
| `Optimal` | `x` (length n), `y` (length m), `value` (optional) |
| `Infeasible` | `y` (length m) |
| `Unbounded` | `x` (length n), `d` (length n) |

The check type is decided by the exact class. A subclass, or any other object, gives a single `claim` failure.

## Check stages

A failure in one stage skips the stages after it.

1. **Shape.** Each vector field must be exactly a `list` or `tuple`, not a subclass, of the right length. It is copied before use. The fields are checked in the order listed in the table above.
2. **Type.** Every entry, and `value` when given, must be an accepted scalar.
3. **Numeric.** Exact checks, in this fixed order:

| Claim | Checks |
|---|---|
| `Optimal` | `primal_eq` (Ax)ᵢ = bᵢ for each row i · `primal_nonneg` xⱼ ≥ 0 · `dual_feas` (Aᵀy)ⱼ ≤ cⱼ · `duality_gap` cᵀx = bᵀy · `value` = cᵀx, if given |
| `Infeasible` | `farkas_dual` (Aᵀy)ⱼ ≤ 0 · `farkas_obj` bᵀy > 0 |
| `Unbounded` | `primal_eq` · `primal_nonneg` · `ray_eq` (Ad)ᵢ = 0 · `ray_nonneg` dⱼ ≥ 0 · `ray_obj` cᵀd < 0 |

Why each set is sufficient:
- **Optimal:** for any feasible x′, cᵀx′ ≥ (Aᵀy)ᵀx′ = bᵀy. A feasible x with cᵀx = bᵀy attains that lower bound, so it is optimal.
- **Infeasible:** a feasible x would give bᵀy = (Aᵀy)ᵀx ≤ 0, contradicting bᵀy > 0.
- **Unbounded:** x + t·d is feasible for every t ≥ 0, and its objective goes to −∞. **x is required.** A ray alone proves nothing.

## Output

```python
@dataclass(frozen=True)
class Failure:
    check: str            # shape | type | claim | primal_eq | primal_nonneg | dual_feas | duality_gap
                          # | value | farkas_dual | farkas_obj | ray_eq | ray_nonneg | ray_obj
    field: str | None     # "x" | "y" | "d" | "value" | None
    index: int | None     # row or column, for per-row or per-column checks
    lhs: Fraction | None
    op: str | None        # the relation that should hold: "==" | "<=" | ">=" | "<" | ">"
    rhs: Fraction | None
    detail: str = ""

@dataclass(frozen=True)
class CheckResult:
    valid: bool
    claim: str                       # "optimal" | "infeasible" | "unbounded" | "unknown"
    failures: tuple[Failure, ...]    # empty iff valid; the first max_failures failures
    objective: Fraction | None       # cᵀx for optimal/unbounded once the numeric stage runs
    truncated: bool = False          # more failures existed than max_failures
```

`CheckResult` is not a `corollarykit.results.Result`. It is a verdict on someone else's claim, and the checker never consults the registry. Validity doesn't depend on `max_failures`.

## Complexity

**O(nnz(A) + m + n) rational operations.** Each row sum is put over the lcm of its terms' denominators and reduced once.

## What an independent verifier gets

The checker *is* the verifier. A `valid=True` result is a complete proof of the claim, with no basis, assuming only that this code and Python's `Fraction` are correct. Nothing in it depends on any 2026 result.
