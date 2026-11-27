"""Independent LP certificate checker, written from the spec (v1.1), not from the library.

Dense matrices, plain Fraction sums, written-out loops. Shares no code with
corollarykit.lp. Input is plain data:

    {"A": dense rows (list of lists, raw values), "m": int, "n": int,
     "b": [...], "c": [...], "claim": "optimal" | "infeasible" | "unbounded" | "unknown",
     "x": ..., "y": ..., "d": ..., "value": ..., "coerce_float": bool}

The problem values (A, b, c) must be exact rationals already accepted by the caller.
Certificate fields are taken raw.
"""

from __future__ import annotations

import math
import numbers
from fractions import Fraction
from typing import Any

FIELDS = {
    "optimal": [("x", "n"), ("y", "m")],
    "infeasible": [("y", "m")],
    "unbounded": [("x", "n"), ("d", "n")],
}

FailureKey = tuple[str, Any, Any]


def to_fraction(v: Any, coerce_float: bool) -> Fraction | None:
    """Accepted scalars: exact int, exact Fraction, other numbers.Rational with exact-int
    parts (converted), finite floats when coerce_float. Never bool."""
    if v is True or v is False:
        return None
    if type(v) is int or type(v) is Fraction:
        return Fraction(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, numbers.Rational):
        try:
            p = int(v.numerator)
            q = int(v.denominator)
        except Exception:
            return None
        if type(p) is not int or type(q) is not int or q == 0:
            return None
        return Fraction(p, q)
    if coerce_float and isinstance(v, float):
        try:
            f = float(v)
        except Exception:
            return None
        if type(f) is not float or math.isnan(f) or math.isinf(f):
            return None
        return Fraction(f)
    return None


def _problem(plain: dict[str, Any]) -> tuple[list[list[Fraction]], list[Fraction], list[Fraction]]:
    A = [[Fraction(v) for v in row] for row in plain["A"]]
    b = [Fraction(v) for v in plain["b"]]
    c = [Fraction(v) for v in plain["c"]]
    return A, b, c


def check(plain: dict[str, Any]) -> list[FailureKey]:
    """Sorted list of (check, field, index) failures; empty means valid."""
    claim = plain["claim"]
    if claim not in FIELDS:
        return [("claim", None, None)]
    m, n = plain["m"], plain["n"]
    coerce = plain.get("coerce_float", False)
    A, b, c = _problem(plain)

    failures: list[FailureKey] = []
    vectors: dict[str, list[Any]] = {}
    for name, dim in FIELDS[claim]:
        value = plain[name]
        size = m if dim == "m" else n
        if not (type(value) is list or type(value) is tuple) or len(list(value)) != size:
            failures.append(("shape", name, None))
        else:
            vectors[name] = list(value)
    if failures:
        return sorted(failures, key=str)

    exact: dict[str, list[Fraction]] = {}
    for name, entries in vectors.items():
        converted = []
        for k in range(len(entries)):
            f = to_fraction(entries[k], coerce)
            if f is None:
                failures.append(("type", name, k))
            converted.append(f)
        exact[name] = converted
    value = None
    if claim == "optimal" and plain.get("value") is not None:
        value = to_fraction(plain["value"], coerce)
        if value is None:
            failures.append(("type", "value", None))
    if failures:
        return sorted(failures, key=str)

    def row_dot(i: int, v: list[Fraction]) -> Fraction:
        total = Fraction(0)
        for j in range(n):
            total = total + A[i][j] * v[j]
        return total

    def col_dot(j: int, w: list[Fraction]) -> Fraction:
        total = Fraction(0)
        for i in range(m):
            total = total + A[i][j] * w[i]
        return total

    def vec_dot(u: list[Fraction], v: list[Fraction]) -> Fraction:
        total = Fraction(0)
        for k in range(len(u)):
            total = total + u[k] * v[k]
        return total

    if claim == "optimal":
        x, y = exact["x"], exact["y"]
        for i in range(m):
            if row_dot(i, x) != b[i]:
                failures.append(("primal_eq", "x", i))
        for j in range(n):
            if not x[j] >= 0:
                failures.append(("primal_nonneg", "x", j))
        for j in range(n):
            if not col_dot(j, y) <= c[j]:
                failures.append(("dual_feas", "y", j))
        if vec_dot(c, x) != vec_dot(b, y):
            failures.append(("duality_gap", None, None))
        if value is not None and value != vec_dot(c, x):
            failures.append(("value", "value", None))
    elif claim == "infeasible":
        y = exact["y"]
        for j in range(n):
            if not col_dot(j, y) <= 0:
                failures.append(("farkas_dual", "y", j))
        if not vec_dot(b, y) > 0:
            failures.append(("farkas_obj", "y", None))
    else:
        x, d = exact["x"], exact["d"]
        for i in range(m):
            if row_dot(i, x) != b[i]:
                failures.append(("primal_eq", "x", i))
        for j in range(n):
            if not x[j] >= 0:
                failures.append(("primal_nonneg", "x", j))
        for i in range(m):
            if row_dot(i, d) != 0:
                failures.append(("ray_eq", "d", i))
        for j in range(n):
            if not d[j] >= 0:
                failures.append(("ray_nonneg", "d", j))
        if not vec_dot(c, d) < 0:
            failures.append(("ray_obj", "d", None))
    return sorted(failures, key=str)
