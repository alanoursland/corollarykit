"""Exact checker for standard-form LP certificates.

Problem: minimize c^T x subject to A x = b, x >= 0.
Spec: planning/specs/lp_certificate_checker.md

This module is trusted code: ``valid=True`` is meant to be a complete proof of the
certificate's claim. It uses only the standard library and does no clever tricks.

Why each check set is sufficient:

* Optimal(x, y): for any feasible x', c^T x' >= (A^T y)^T x' = y^T A x' = b^T y, using
  x' >= 0 and c >= A^T y. So b^T y is a lower bound, and a feasible x with
  c^T x = b^T y attains it: x is optimal with value c^T x.
* Infeasible(y): if A x = b with x >= 0, then b^T y = (A^T y)^T x <= 0, since
  A^T y <= 0 and x >= 0. That contradicts b^T y > 0.
* Unbounded(x, d): x + t d is feasible for all t >= 0, because A(x + t d) = b and
  x + t d >= 0. Its objective c^T x + t c^T d tends to -infinity, since c^T d < 0.
  A ray alone proves nothing, so x is required.
"""

from __future__ import annotations

import math
import numbers
import operator
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

# --------------------------------------------------------------------------- scalars


def _exact_int(v: object) -> int | None:
    """int(v), or None if that raises. int() always returns an exact built-in int: when a
    class's __int__ returns an int subclass, Python warns and copies the value."""
    try:
        return int(v)  # type: ignore[call-overload,no-any-return]
    except Exception:
        return None


def _rational(v: object, *, coerce_float: bool) -> Fraction | None:
    """A base Fraction for an accepted scalar, else None. Never raises.

    Every accepted value, including a plain int or Fraction, is rebuilt from exact-int
    numerator and denominator, so a subclass's own arithmetic can't run inside a check.
    The except clauses wrap only calls into foreign objects, never this module's
    arithmetic.
    """
    if isinstance(v, bool):
        return None
    if isinstance(v, numbers.Rational):  # int, Fraction, their subclasses, mpq, numpy ints
        try:
            num, den = _exact_int(v.numerator), _exact_int(v.denominator)
        except Exception:
            return None
        if num is None or den is None or den == 0:
            return None
        return Fraction(num, den)
    if isinstance(v, float) and coerce_float:
        try:
            f = float(v)
        except Exception:
            return None
        if type(f) is not float or not math.isfinite(f):
            return None
        return Fraction(f)
    return None


def _problem_scalar(v: object, coerce_float: bool, where: str) -> Fraction:
    r = _rational(v, coerce_float=coerce_float)
    if r is None:
        raise TypeError(f"{where}: {type(v).__name__} is not an exact rational")
    return r


def _problem_index(v: object, where: str) -> int:
    if isinstance(v, bool):
        raise TypeError(f"{where}: bool is not an index")
    return operator.index(v)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- problem


@dataclass(frozen=True)
class SparseMatrix:
    """m x n matrix; rows[i] = ((j, a_ij), ...) with j strictly ascending, a_ij != 0."""

    m: int
    n: int
    rows: tuple[tuple[tuple[int, Fraction], ...], ...]

    def __post_init__(self) -> None:
        if type(self.m) is not int or type(self.n) is not int or self.m < 0 or self.n < 0:
            raise ValueError("SparseMatrix: m and n must be ints >= 0")
        if type(self.rows) is not tuple or len(self.rows) != self.m:
            raise ValueError(f"SparseMatrix: rows must be a tuple of exactly m={self.m} rows")
        for i, row in enumerate(self.rows):
            if type(row) is not tuple:
                raise ValueError(f"SparseMatrix: row {i} must be a tuple")
            prev = -1
            for entry in row:
                if type(entry) is not tuple or len(entry) != 2:
                    raise ValueError(f"SparseMatrix: row {i} entries must be (j, value) pairs")
                j, v = entry
                if type(j) is not int or not prev < j < self.n:
                    raise ValueError(
                        f"SparseMatrix: row {i} column indices must be in range and ascending"
                    )
                if type(v) is not Fraction or v == 0:
                    raise ValueError(f"SparseMatrix: row {i} values must be nonzero Fractions")
                prev = j

    @classmethod
    def from_coo(
        cls,
        m: int,
        n: int,
        rows: Sequence[object],
        cols: Sequence[object],
        vals: Sequence[object],
        *,
        coerce_float: bool = False,
    ) -> SparseMatrix:
        """Build from COO triples. Duplicate (i, j) entries are summed; zeros are dropped."""
        m, n = _problem_index(m, "m"), _problem_index(n, "n")  # sign checked by __post_init__
        if not len(rows) == len(cols) == len(vals):
            raise ValueError("rows, cols and vals must have the same length")
        acc: dict[tuple[int, int], Fraction] = {}
        for k in range(len(rows)):
            i, j = _problem_index(rows[k], f"rows[{k}]"), _problem_index(cols[k], f"cols[{k}]")
            if not 0 <= i < m:  # a negative i would otherwise wrap to the last row
                raise ValueError(f"entry {k}: row index {i} out of range for {m} rows")
            # Column indices are checked by SparseMatrix.__post_init__.
            v = _problem_scalar(vals[k], coerce_float, f"vals[{k}]")
            acc[(i, j)] = acc.get((i, j), Fraction(0)) + v
        per_row: list[list[tuple[int, Fraction]]] = [[] for _ in range(m)]
        for (i, j), v in sorted(acc.items()):
            if v != 0:
                per_row[i].append((j, v))
        return cls(m, n, tuple(tuple(r) for r in per_row))

    @classmethod
    def from_dense(
        cls, dense: Sequence[Sequence[object]], *, n: int | None = None, coerce_float: bool = False
    ) -> SparseMatrix:
        m = len(dense)
        if m == 0:
            if n is None:
                raise ValueError("from_dense: n is required when there are no rows")
        else:
            width = len(dense[0])
            if n is not None and n != width:
                raise ValueError(f"from_dense: rows have {width} columns, expected {n}")
            n = width
        rows, cols, vals = [], [], []
        for i, row in enumerate(dense):
            if len(row) != n:
                raise ValueError(f"from_dense: row {i} has length {len(row)}, expected {n}")
            for j, v in enumerate(row):
                rows.append(i)
                cols.append(j)
                vals.append(v)
        return cls.from_coo(m, n, rows, cols, vals, coerce_float=coerce_float)

    @property
    def nnz(self) -> int:
        return sum(len(r) for r in self.rows)

    def to_dense(self) -> list[list[Fraction]]:
        out = [[Fraction(0)] * self.n for _ in range(self.m)]
        for i, row in enumerate(self.rows):
            for j, v in row:
                out[i][j] = v
        return out


@dataclass(frozen=True)
class StandardFormLP:
    """minimize c^T x subject to A x = b, x >= 0."""

    A: SparseMatrix
    b: tuple[Fraction, ...]
    c: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if type(self.A) is not SparseMatrix:
            raise TypeError("StandardFormLP: A must be a SparseMatrix")
        for name, vec, want in (("b", self.b, self.A.m), ("c", self.c, self.A.n)):
            if type(vec) is not tuple or len(vec) != want:
                raise ValueError(f"StandardFormLP: {name} must be a tuple of length {want}")
            if any(type(v) is not Fraction for v in vec):
                raise TypeError(f"StandardFormLP: {name} entries must be Fractions")

    @classmethod
    def build(
        cls,
        A: SparseMatrix | Sequence[Sequence[object]],
        b: Iterable[object],
        c: Iterable[object],
        *,
        coerce_float: bool = False,
    ) -> StandardFormLP:
        b_t = tuple(_problem_scalar(v, coerce_float, f"b[{i}]") for i, v in enumerate(b))
        c_t = tuple(_problem_scalar(v, coerce_float, f"c[{j}]") for j, v in enumerate(c))
        if type(A) is not SparseMatrix:
            A = SparseMatrix.from_dense(A, n=len(c_t), coerce_float=coerce_float)  # type: ignore[arg-type]
        return cls(A, b_t, c_t)

    @property
    def m(self) -> int:
        return self.A.m

    @property
    def n(self) -> int:
        return self.A.n


# ---------------------------------------------------------------------- certificates


@dataclass(frozen=True)
class Optimal:
    x: Any
    y: Any
    value: Any = None


@dataclass(frozen=True)
class Infeasible:
    y: Any


@dataclass(frozen=True)
class Unbounded:
    x: Any
    d: Any


# --------------------------------------------------------------------------- output


@dataclass(frozen=True)
class Failure:
    check: str
    field: str | None
    index: int | None
    lhs: Fraction | None
    op: str | None
    rhs: Fraction | None
    detail: str = ""

    def __str__(self) -> str:
        where = "" if self.index is None else f"[{self.index}]"
        head = f"{self.check}{where}" + (f" ({self.field})" if self.field else "")
        if self.op is None:
            return f"{head}: {self.detail}"
        return f"{head}: {self.lhs} {self.op} {self.rhs} is false"


@dataclass(frozen=True)
class CheckResult:
    valid: bool
    claim: str
    failures: tuple[Failure, ...]
    objective: Fraction | None
    truncated: bool = False


class _Collector:
    def __init__(self, cap: int | None) -> None:
        self.cap = cap
        self.found: list[Failure] = []
        self.count = 0

    def add(self, f: Failure) -> None:
        self.count += 1
        if self.cap is None or len(self.found) < self.cap:
            self.found.append(f)

    def result(self, claim: str, objective: Fraction | None) -> CheckResult:
        return CheckResult(
            valid=self.count == 0,
            claim=claim,
            failures=tuple(self.found),
            objective=objective,
            truncated=self.count > len(self.found),
        )


# ------------------------------------------------------------------- exact algebra


def _dot(pairs: Iterable[tuple[Fraction, Fraction]]) -> Fraction:
    """Sum of a*b over the pairs, normalized once over the lcm of the denominators."""
    prods = [a * b for a, b in pairs]
    if not prods:
        return Fraction(0)
    lcm = math.lcm(*(p.denominator for p in prods))
    return Fraction(sum(p.numerator * (lcm // p.denominator) for p in prods), lcm)


def _vdot(u: Sequence[Fraction], v: Sequence[Fraction]) -> Fraction:
    """u . v for vectors whose equal length the shape stage has already established."""
    return _dot((u[k], v[k]) for k in range(len(u)))


def _a_times(A: SparseMatrix, v: Sequence[Fraction]) -> list[Fraction]:
    return [_dot((a, v[j]) for j, a in row) for row in A.rows]


def _at_times(A: SparseMatrix, w: Sequence[Fraction]) -> list[Fraction]:
    cols: list[list[tuple[Fraction, Fraction]]] = [[] for _ in range(A.n)]
    for i, row in enumerate(A.rows):
        for j, a in row:
            cols[j].append((a, w[i]))
    return [_dot(col) for col in cols]


_OPS = {
    "==": operator.eq,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}


def _check_each(
    out: _Collector,
    check: str,
    field: str,
    lhs: Sequence[Fraction],
    op: str,
    rhs: Sequence[Fraction] | Fraction,
) -> None:
    holds = _OPS[op]
    for idx, left in enumerate(lhs):
        right = rhs if isinstance(rhs, Fraction) else rhs[idx]
        if not holds(left, right):
            out.add(Failure(check, field, idx, left, op, right))


def _check_one(
    out: _Collector, check: str, field: str | None, lhs: Fraction, op: str, rhs: Fraction
) -> None:
    if not _OPS[op](lhs, rhs):
        out.add(Failure(check, field, None, lhs, op, rhs))


# --------------------------------------------------------------------------- checker

_CLAIMS: dict[type, str] = {Optimal: "optimal", Infeasible: "infeasible", Unbounded: "unbounded"}
_FIELDS: dict[type, tuple[tuple[str, str], ...]] = {
    Optimal: (("x", "n"), ("y", "m")),
    Infeasible: (("y", "m"),),
    Unbounded: (("x", "n"), ("d", "n")),
}
_ZERO = Fraction(0)


def check_lp_certificate(
    problem: StandardFormLP,
    cert: object,
    *,
    max_failures: int | None = 10,
    coerce_float: bool = False,
) -> CheckResult:
    """Check an Optimal, Infeasible or Unbounded certificate exactly. Never raises because
    of the certificate; a malformed one yields failures."""
    if type(problem) is not StandardFormLP:
        raise TypeError("problem must be a StandardFormLP")
    if max_failures is not None and (type(max_failures) is not int or max_failures < 1):
        raise ValueError("max_failures must be an int >= 1, or None")
    out = _Collector(max_failures)

    kind = type(cert)
    if kind not in _CLAIMS:
        out.add(
            Failure("claim", None, None, None, None, None, f"not a certificate: {kind.__name__}")
        )
        return out.result("unknown", None)
    claim = _CLAIMS[kind]

    # Stage 1: shape.
    raw: dict[str, tuple[object, ...]] = {}
    for name, dim in _FIELDS[kind]:
        v = getattr(cert, name)
        want = problem.m if dim == "m" else problem.n
        if type(v) is not list and type(v) is not tuple:
            out.add(
                Failure(
                    "shape", name, None, None, None, None, f"not a list/tuple: {type(v).__name__}"
                )
            )
            continue
        snap = tuple(v)
        if len(snap) != want:
            out.add(
                Failure(
                    "shape",
                    name,
                    None,
                    None,
                    None,
                    None,
                    f"expected length {want}, got {len(snap)}",
                )
            )
            continue
        raw[name] = snap
    if out.count:
        return out.result(claim, None)

    # Stage 2: type.
    vec: dict[str, list[Fraction]] = {}
    for name, snap in raw.items():
        conv = [_rational(e, coerce_float=coerce_float) for e in snap]
        for idx, e in enumerate(conv):
            if e is None:
                out.add(Failure("type", name, idx, None, None, None, type(snap[idx]).__name__))
        vec[name] = [e for e in conv if e is not None]
    value: Fraction | None = None
    if kind is Optimal and cert.value is not None:  # type: ignore[attr-defined]
        value = _rational(cert.value, coerce_float=coerce_float)  # type: ignore[attr-defined]
        if value is None:
            out.add(Failure("type", "value", None, None, None, None, type(cert.value).__name__))  # type: ignore[attr-defined]
    if out.count:
        return out.result(claim, None)

    # Stage 3: numeric checks, in the fixed order of the spec.
    A, b, c = problem.A, problem.b, problem.c
    objective: Fraction | None = None
    if kind is Optimal:
        x, y = vec["x"], vec["y"]
        _check_each(out, "primal_eq", "x", _a_times(A, x), "==", b)
        _check_each(out, "primal_nonneg", "x", x, ">=", _ZERO)
        _check_each(out, "dual_feas", "y", _at_times(A, y), "<=", c)
        cx, by = _vdot(c, x), _vdot(b, y)
        _check_one(out, "duality_gap", None, cx, "==", by)
        if value is not None:
            _check_one(out, "value", "value", value, "==", cx)
        objective = cx
    elif kind is Infeasible:
        y = vec["y"]
        _check_each(out, "farkas_dual", "y", _at_times(A, y), "<=", _ZERO)
        _check_one(out, "farkas_obj", "y", _vdot(b, y), ">", _ZERO)
    else:
        x, d = vec["x"], vec["d"]
        _check_each(out, "primal_eq", "x", _a_times(A, x), "==", b)
        _check_each(out, "primal_nonneg", "x", x, ">=", _ZERO)
        _check_each(out, "ray_eq", "d", _a_times(A, d), "==", _ZERO)
        _check_each(out, "ray_nonneg", "d", d, ">=", _ZERO)
        _check_one(out, "ray_obj", "d", _vdot(c, d), "<", _ZERO)
        objective = _vdot(c, x)
    return out.result(claim, objective)


__all__ = [
    "CheckResult",
    "Failure",
    "Infeasible",
    "Optimal",
    "SparseMatrix",
    "StandardFormLP",
    "Unbounded",
    "check_lp_certificate",
]
