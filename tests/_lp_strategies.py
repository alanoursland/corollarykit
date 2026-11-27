"""Hypothesis strategies and helpers for the LP checker tests.

LPs are generated as **raw input** (COO triples with duplicates and explicit zeros, or
dense rows). The independent checker gets a dense matrix assembled here from the raw
input, never the library's normalized SparseMatrix.
"""

from __future__ import annotations

import numbers
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from hypothesis import strategies as st

from corollarykit.lp import Infeasible, Optimal, SparseMatrix, StandardFormLP, Unbounded

# ------------------------------------------------------------------ raw problems


@dataclass(frozen=True)
class RawLP:
    m: int
    n: int
    kind: str  # "coo" or "dense"
    rows: tuple[int, ...]
    cols: tuple[int, ...]
    vals: tuple[int, ...]
    dense: tuple[tuple[int, ...], ...]
    b: tuple[int, ...]
    c: tuple[int, ...]

    def problem(self) -> StandardFormLP:
        if self.kind == "coo":
            A = SparseMatrix.from_coo(self.m, self.n, self.rows, self.cols, self.vals)
            return StandardFormLP.build(A, self.b, self.c)
        return StandardFormLP.build([list(r) for r in self.dense], self.b, self.c)

    def dense_independent(self) -> list[list[Fraction]]:
        """Assembled from the raw input with plain loops; shares no code with SparseMatrix."""
        out = [[Fraction(0) for _ in range(self.n)] for _ in range(self.m)]
        if self.kind == "coo":
            for k in range(len(self.rows)):
                out[self.rows[k]][self.cols[k]] += Fraction(self.vals[k])
        else:
            for i in range(self.m):
                for j in range(self.n):
                    out[i][j] = Fraction(self.dense[i][j])
        return out

    def fractions(self) -> tuple[list[list[Fraction]], list[Fraction], list[Fraction]]:
        return (
            self.dense_independent(),
            [Fraction(v) for v in self.b],
            [Fraction(v) for v in self.c],
        )


entry = st.one_of(st.just(0), st.just(0), st.integers(-5, 5))


@st.composite
def raw_lps(draw: Any, max_m: int = 4, max_n: int = 6) -> RawLP:
    m = draw(st.integers(0, max_m))
    n = draw(st.integers(0, max_n))
    dense = tuple(tuple(draw(entry) for _ in range(n)) for _ in range(m))
    b = tuple(draw(entry) for _ in range(m))
    c = tuple(draw(entry) for _ in range(n))
    kind = draw(st.sampled_from(["coo", "dense"]))
    rows: list[int] = []
    cols: list[int] = []
    vals: list[int] = []
    if kind == "coo":
        # Split each nonzero into one or two summands, add explicit zeros, shuffle.
        triples = []
        for i in range(m):
            for j in range(n):
                v = dense[i][j]
                if v != 0 and draw(st.booleans()):
                    part = draw(st.integers(-3, 3))
                    triples += [(i, j, part), (i, j, v - part)]
                elif v != 0:
                    triples.append((i, j, v))
                elif draw(st.integers(0, 4)) == 0:
                    triples.append((i, j, 0))
        triples = draw(st.permutations(triples)) if triples else []
        rows, cols, vals = [t[0] for t in triples], [t[1] for t in triples], [t[2] for t in triples]
    return RawLP(m, n, kind, tuple(rows), tuple(cols), tuple(vals), dense, b, c)


# --------------------------------------------------------------- hostile values


class Boom(Exception):
    pass


class LyingInt(int):
    """Same value as an int, but its arithmetic raises. Must be normalized away."""

    def __add__(self, o: object) -> Any:
        raise Boom

    __radd__ = __mul__ = __rmul__ = __sub__ = __rsub__ = __add__

    def __eq__(self, o: object) -> bool:
        raise Boom

    __hash__ = int.__hash__


class LyingFraction(Fraction):
    def __add__(self, o: object) -> Any:
        raise Boom

    __radd__ = __mul__ = __rmul__ = __sub__ = __rsub__ = __add__

    def __eq__(self, o: object) -> bool:
        raise Boom

    __hash__ = Fraction.__hash__


class BadRational:
    """Registered as a Rational, but reading numerator raises."""

    @property
    def numerator(self) -> int:
        raise Boom

    denominator = 1


numbers.Rational.register(BadRational)


class ZeroDenRational:
    """A registered Rational claiming denominator 0."""

    numerator = 1
    denominator = 0


class StrNumerator:
    """A registered Rational whose numerator isn't convertible to int."""

    numerator = "x"
    denominator = 1


class _IntReturnsSubclass:
    def __int__(self) -> int:
        return LyingInt(1)


class SubclassIntNumerator:
    """A registered Rational whose numerator's __int__ returns an int subclass."""

    numerator = _IntReturnsSubclass()
    denominator = 1


for _cls in (ZeroDenRational, StrNumerator, SubclassIntNumerator):
    numbers.Rational.register(_cls)


class BadFloat(float):
    def __float__(self) -> float:
        raise Boom


class RaisingList(list):  # type: ignore[type-arg]
    def __len__(self) -> int:
        raise Boom

    def __iter__(self) -> Any:
        raise Boom


class LyingList(list):  # type: ignore[type-arg]
    def __len__(self) -> int:
        return 0


class NotACertificate:
    x = y = d = ()


class OptimalSubclass(Optimal):
    pass


garbage_scalar = st.one_of(
    st.integers(-5, 5),
    st.fractions(max_denominator=7).filter(lambda f: abs(f) < 10),
    st.floats(allow_nan=True, allow_infinity=True),
    st.none(),
    st.text(max_size=3),
    st.booleans(),
    st.lists(st.integers(), max_size=2),
    st.sampled_from(
        [
            LyingInt(2),
            LyingFraction(1, 3),
            BadRational(),
            BadFloat(1.5),
            ZeroDenRational(),
            StrNumerator(),
            SubclassIntNumerator(),
            float("nan"),
            float("-inf"),
        ]
    ),
)


def garbage_vector(size: int) -> Any:
    sizes = st.sampled_from(sorted({0, max(size - 1, 0), size, size + 1}))
    lists = sizes.flatmap(lambda k: st.lists(garbage_scalar, min_size=k, max_size=k))
    return st.one_of(
        lists,
        lists.map(tuple),
        lists.map(RaisingList),
        lists.map(LyingList),
        st.sampled_from([None, 3, "xyz", {"a": 1}]),
    )


@st.composite
def garbage_certs(draw: Any, raw: RawLP) -> object:
    which = draw(st.sampled_from(["optimal", "infeasible", "unbounded", "other", "subclass"]))
    if which == "optimal":
        return Optimal(
            draw(garbage_vector(raw.n)), draw(garbage_vector(raw.m)), draw(garbage_scalar)
        )
    if which == "infeasible":
        return Infeasible(draw(garbage_vector(raw.m)))
    if which == "unbounded":
        return Unbounded(draw(garbage_vector(raw.n)), draw(garbage_vector(raw.n)))
    if which == "subclass":
        return OptimalSubclass(draw(garbage_vector(raw.n)), draw(garbage_vector(raw.m)))
    return draw(st.sampled_from([NotACertificate(), None, 42, ("optimal",)]))


# ------------------------------------------------------------------ conversions


def to_cert(t: tuple) -> object:
    """Oracle tuple -> library certificate object."""
    if t[0] == "optimal":
        return Optimal(list(t[1]), list(t[2]))
    if t[0] == "infeasible":
        return Infeasible(list(t[1]))
    return Unbounded(list(t[1]), list(t[2]))


CLAIM_OF = {Optimal: "optimal", Infeasible: "infeasible", Unbounded: "unbounded"}


def to_plain(raw: RawLP, cert: object, coerce_float: bool = False) -> dict[str, Any]:
    """Raw problem (independently assembled) plus the certificate fields, unconverted."""
    claim = CLAIM_OF.get(type(cert), "unknown")
    plain: dict[str, Any] = {
        "A": raw.dense_independent(),
        "m": raw.m,
        "n": raw.n,
        "b": list(raw.b),
        "c": list(raw.c),
        "claim": claim,
        "coerce_float": coerce_float,
    }
    for name in ("x", "y", "d", "value"):
        if claim != "unknown" and hasattr(cert, name):
            plain[name] = getattr(cert, name)
    return plain


def failure_keys(result: Any) -> list[tuple[str, Any, Any]]:
    return sorted(((f.check, f.field, f.index) for f in result.failures), key=str)


def perturb(cert: object, which: int, delta: Fraction) -> object:
    """Change one coordinate of a certificate's concatenated vectors by delta."""
    names = [n for n in ("x", "y", "d") if hasattr(cert, n)]
    flat = [(n, k) for n in names for k in range(len(getattr(cert, n)))]
    if not flat:
        return cert
    name, k = flat[which % len(flat)]
    vec = list(getattr(cert, name))
    vec[k] = vec[k] + delta
    fields = {n: list(getattr(cert, n)) for n in names}
    fields[name] = vec
    return type(cert)(**fields)
