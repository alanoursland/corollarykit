"""Exact LP oracles for tests. Not trusted code: they are cross-checked against each other.

(a) exact_status: the truth about an LP by enumerating vertices and rays.
(b) simplex_certificate: certificates from an exact simplex method with Bland's rule.

Problems are given densely: A (list of rows), b, c, with Fraction entries.
"""

from __future__ import annotations

import itertools
from fractions import Fraction

Vec = list[Fraction]
Mat = list[list[Fraction]]


def dot(u: Vec, v: Vec) -> Fraction:
    return sum((a * b for a, b in zip(u, v, strict=True)), Fraction(0))


def matvec(A: Mat, x: Vec) -> Vec:
    return [dot(row, x) for row in A]


def tmatvec(A: Mat, y: Vec, n: int) -> Vec:
    return [sum((A[i][j] * y[i] for i in range(len(A))), Fraction(0)) for j in range(n)]


# ----------------------------------------------------------- (a) enumeration


def solve_subset(A: Mat, b: Vec, S: tuple[int, ...]) -> Vec | None:
    """The unique x_S with A[:, S] x_S = b if the columns are independent and the system
    is consistent; otherwise None."""
    m, k = len(A), len(S)
    M = [[A[i][j] for j in S] + [b[i]] for i in range(m)]
    r = 0
    for col in range(k):
        p = next((i for i in range(r, m) if M[i][col] != 0), None)
        if p is None:
            return None
        M[r], M[p] = M[p], M[r]
        pv = M[r][col]
        M[r] = [v / pv for v in M[r]]
        for i in range(m):
            if i != r and M[i][col] != 0:
                f = M[i][col]
                M[i] = [a - f * bb for a, bb in zip(M[i], M[r], strict=True)]
        r += 1
    if any(M[i][k] != 0 for i in range(r, m)):
        return None
    return [M[i][k] for i in range(k)]


def bfs_list(A: Mat, b: Vec, n: int) -> list[tuple[Fraction, ...]]:
    found: set[tuple[Fraction, ...]] = set()
    for size in range(min(len(A), n) + 1):
        for S in itertools.combinations(range(n), size):
            xs = solve_subset(A, b, S)
            if xs is not None and all(v >= 0 for v in xs):
                x = [Fraction(0)] * n
                for j, v in zip(S, xs, strict=True):
                    x[j] = v
                found.add(tuple(x))
    return sorted(found)


def exact_status(A: Mat, b: Vec, c: Vec) -> tuple:
    """("infeasible",) | ("unbounded",) | ("optimal", value)."""
    n = len(c)
    verts = bfs_list(A, b, n)
    if not verts:
        return ("infeasible",)
    rays = bfs_list(
        [list(r) for r in A] + [[Fraction(1)] * n], [Fraction(0)] * len(A) + [Fraction(1)], n
    )
    if any(dot(c, list(d)) < 0 for d in rays):
        return ("unbounded",)
    return ("optimal", min(dot(c, list(v)) for v in verts))


def dual_optima(A: Mat, b: Vec, c: Vec, opt: Fraction) -> list[Vec]:
    """Vertices y of {y : A^T y <= c} with b^T y = opt. A must have full row rank."""
    m, n = len(A), len(c)
    out: set[tuple[Fraction, ...]] = set()
    cols = [[A[i][j] for i in range(m)] for j in range(n)]  # cols[j] = A_j as a row
    for S in itertools.combinations(range(n), m):
        M = [cols[j] for j in S]  # A_S^T, square
        if _rank(M) < m:
            continue
        y = _solve_square(M, [c[j] for j in S])
        if all(dot(cols[j], y) <= c[j] for j in range(n)) and dot(b, y) == opt:
            out.add(tuple(y))
    return [list(y) for y in sorted(out)]


# ---------------------------------------------------------- (b) exact simplex


def _rank(M: Mat) -> int:
    M = [list(r) for r in M]
    r = 0
    cols = len(M[0]) if M else 0
    for col in range(cols):
        p = next((i for i in range(r, len(M)) if M[i][col] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        for i in range(r + 1, len(M)):
            f = M[i][col] / M[r][col]
            M[i] = [a - f * bb for a, bb in zip(M[i], M[r], strict=True)]
        r += 1
    return r


def _solve_square(M: Mat, v: Vec) -> Vec:
    k = len(M)
    aug = [[*list(M[i]), v[i]] for i in range(k)]
    for col in range(k):
        p = next(i for i in range(col, k) if aug[i][col] != 0)
        aug[col], aug[p] = aug[p], aug[col]
        pv = aug[col][col]
        aug[col] = [a / pv for a in aug[col]]
        for i in range(k):
            if i != col and aug[i][col] != 0:
                f = aug[i][col]
                aug[i] = [a - f * bb for a, bb in zip(aug[i], aug[col], strict=True)]
    return [aug[i][k] for i in range(k)]


def simplex_certificate(A0: Mat, b0: Vec, c: Vec) -> tuple:
    """("optimal", x, y) | ("infeasible", y) | ("unbounded", x, d)."""
    m0, n = len(A0), len(c)
    # 0. Inconsistent dependent rows give a Farkas vector from the row multipliers.
    R = [[*list(A0[i]), b0[i]] for i in range(m0)]
    T = [[Fraction(int(i == k)) for k in range(m0)] for i in range(m0)]
    r = 0
    for col in range(n):
        p = next((i for i in range(r, m0) if R[i][col] != 0), None)
        if p is None:
            continue
        R[r], R[p] = R[p], R[r]
        T[r], T[p] = T[p], T[r]
        for i in range(r + 1, m0):
            if R[i][col] != 0:
                f = R[i][col] / R[r][col]
                R[i] = [a - f * bb for a, bb in zip(R[i], R[r], strict=True)]
                T[i] = [a - f * bb for a, bb in zip(T[i], T[r], strict=True)]
        r += 1
    for i in range(r, m0):
        if R[i][n] != 0:
            return ("infeasible", T[i] if R[i][n] > 0 else [-v for v in T[i]])
    # Keep a maximal set of independent rows.
    idx: list[int] = []
    kept: Mat = []
    for i in range(m0):
        if _rank([*kept, list(A0[i])]) > len(kept):
            kept.append(list(A0[i]))
            idx.append(i)
    m = len(idx)
    flip = [1 if b0[i] >= 0 else -1 for i in idx]
    A = [[v * flip[k] for v in A0[i]] for k, i in enumerate(idx)]
    b = [b0[i] * flip[k] for k, i in enumerate(idx)]
    N = n + m
    tab = [A[i] + [Fraction(int(k == i)) for k in range(m)] + [b[i]] for i in range(m)]
    basis = [n + i for i in range(m)]

    def pivot(row: int, col: int) -> None:
        pv = tab[row][col]
        tab[row] = [v / pv for v in tab[row]]
        for i in range(m):
            if i != row and tab[i][col] != 0:
                f = tab[i][col]
                tab[i] = [a - f * bb for a, bb in zip(tab[i], tab[row], strict=True)]
        basis[row] = col

    def run(cost: Vec, allowed) -> int | None:  # type: ignore[no-untyped-def]
        while True:
            cb = [cost[j] for j in basis]
            red = [
                cost[j] - sum((cb[i] * tab[i][j] for i in range(m)), Fraction(0)) for j in range(N)
            ]
            enter = next((j for j in range(N) if allowed(j) and red[j] < 0), None)
            if enter is None:
                return None
            rows = [i for i in range(m) if tab[i][enter] > 0]
            if not rows:
                return enter
            best = min(tab[i][N] / tab[i][enter] for i in rows)
            leave = min(
                (i for i in rows if tab[i][N] / tab[i][enter] == best), key=lambda i: basis[i]
            )
            pivot(leave, enter)

    def duals(cost: Vec) -> Vec:
        B = [[(A[i][j] if j < n else Fraction(int(j - n == i))) for j in basis] for i in range(m)]
        return _solve_square([list(col) for col in zip(*B, strict=True)], [cost[j] for j in basis])

    def lift(y: Vec) -> Vec:
        full = [Fraction(0)] * m0
        for k, i in enumerate(idx):
            full[i] = y[k] * flip[k]
        return full

    phase1 = [Fraction(0)] * n + [Fraction(1)] * m
    run(phase1, lambda j: True)
    if sum((tab[i][N] for i in range(m) if basis[i] >= n), Fraction(0)) > 0:
        return ("infeasible", lift(duals(phase1)))
    for i in range(m):
        if basis[i] >= n:
            j = next((j for j in range(n) if tab[i][j] != 0), None)
            if j is not None:
                pivot(i, j)
    cost = list(c) + [Fraction(0)] * m
    enter = run(cost, lambda j: j < n)
    x = [Fraction(0)] * n
    for i in range(m):
        if basis[i] < n:
            x[basis[i]] = tab[i][N]
    if enter is not None:
        d = [Fraction(0)] * n
        d[enter] = Fraction(1)
        for i in range(m):
            if basis[i] < n:
                d[basis[i]] = -tab[i][enter]
        return ("unbounded", x, d)
    return ("optimal", x, lift(duals(cost)))
