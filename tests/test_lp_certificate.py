"""Hand-built and edge-case tests for check_lp_certificate (testing plan sections 1, 4, 5, 7)."""

import re
import time
from fractions import Fraction as F
from pathlib import Path

import pytest
from _lp_oracle import dual_optima, exact_status, simplex_certificate
from _lp_strategies import (
    BadFloat,
    BadRational,
    Boom,
    LyingFraction,
    LyingInt,
    LyingList,
    NotACertificate,
    OptimalSubclass,
    RaisingList,
)

import corollarykit.registry as registry
from corollarykit.lp import (
    CheckResult,
    Failure,
    Infeasible,
    Optimal,
    SparseMatrix,
    StandardFormLP,
    Unbounded,
    check_lp_certificate,
)


def keys(result):
    return [(f.check, f.field, f.index) for f in result.failures]


# A small LP with all three kinds of certificate available by changing c or b.
#   min c^T x  s.t.  x1 + 2 x2 + x3 = 4,  3 x1 + x2 + x4 = 7,  x >= 0
A = [[1, 2, 1, 0], [3, 1, 0, 1]]
B = [4, 7]


def lp(c=(1, 1, 0, 0), b=B, a=A):
    return StandardFormLP.build(a, b, c)


# ------------------------------------------------------------------ hand-built


def test_valid_optimal():
    # x = (2, 1, 0, 0) with value 3; y = (2/5, 1/5) gives A^T y = (1, 1, 2/5, 1/5) <= c.
    p = lp(c=(1, 1, 1, 1))
    cert = Optimal([2, 1, 0, 0], [F(2, 5), F(1, 5)], 3)
    r = check_lp_certificate(p, cert)
    assert r == CheckResult(True, "optimal", (), F(3))


def test_valid_infeasible():
    # x1 + x2 = -1 with x >= 0 is infeasible: y = (-1,) gives A^T y = (-1, -1) <= 0, b^T y = 1 > 0
    p = StandardFormLP.build([[1, 1]], [-1], [0, 0])
    r = check_lp_certificate(p, Infeasible([-1]))
    assert r.valid and r.claim == "infeasible" and r.objective is None


def test_valid_unbounded():
    # min -x1 s.t. x1 - x2 = 0: x = (0, 0), d = (1, 1)
    p = StandardFormLP.build([[1, -1]], [0], [-1, 0])
    r = check_lp_certificate(p, Unbounded([0, 0], [1, 1]))
    assert r.valid and r.claim == "unbounded" and r.objective == 0


@pytest.mark.parametrize(
    ("cert", "expected"),
    [
        (
            Optimal([2, 1, 0, 1], [F(2, 5), F(1, 5)]),
            [("primal_eq", "x", 1), ("duality_gap", None, None)],
        ),
        (Optimal([2, 1, 0, 0], [F(2, 5), F(1, 5)], 4), [("value", "value", None)]),
        (
            Optimal([2, 1, 0, 0], [F(2, 5), F(2, 5)]),
            [("dual_feas", "y", 0), ("dual_feas", "y", 1), ("duality_gap", None, None)],
        ),
    ],
)
def test_single_broken_optimal(cert, expected):
    assert keys(check_lp_certificate(lp(c=(1, 1, 1, 1)), cert)) == expected


def test_primal_nonneg_failure_alone():
    # x = (3, -1, 3, -1) satisfies both equalities (3 - 2 + 3 = 4, 9 - 1 - 1 = 7) but has
    # two negative entries; with c = 0 and y = 0 every other check holds.
    p = lp(c=(0, 0, 0, 0))
    r = check_lp_certificate(p, Optimal([3, -1, 3, -1], [0, 0]))
    assert keys(r) == [("primal_nonneg", "x", 1), ("primal_nonneg", "x", 3)]


def test_single_broken_infeasible():
    p = StandardFormLP.build([[1, 1]], [-1], [0, 0])
    assert keys(check_lp_certificate(p, Infeasible([1]))) == [
        ("farkas_dual", "y", 0),
        ("farkas_dual", "y", 1),
        ("farkas_obj", "y", None),
    ]
    p2 = StandardFormLP.build([[1, 1]], [0], [0, 0])
    assert keys(check_lp_certificate(p2, Infeasible([-1]))) == [("farkas_obj", "y", None)]


def test_single_broken_unbounded():
    p = StandardFormLP.build([[1, -1]], [0], [-1, 0])
    assert keys(check_lp_certificate(p, Unbounded([0, 0], [1, 2]))) == [("ray_eq", "d", 0)]
    assert keys(check_lp_certificate(p, Unbounded([0, 0], [-1, -1]))) == [
        ("ray_nonneg", "d", 0),
        ("ray_nonneg", "d", 1),
        ("ray_obj", "d", None),
    ]
    assert keys(check_lp_certificate(p, Unbounded([1, 0], [1, 1]))) == [("primal_eq", "x", 0)]


def test_failure_records_relation():
    p = StandardFormLP.build([[1, 1]], [0], [0, 0])
    (f,) = check_lp_certificate(p, Infeasible([-1])).failures
    assert (f.lhs, f.op, f.rhs) == (F(0), ">", F(0))
    assert str(f) == "farkas_obj (y): 0 > 0 is false"


# ------------------------------------------------ ray without a feasible point


RAY_LP = StandardFormLP.build([[1, 0]], [-1], [0, -1])  # min -x2 s.t. x1 = -1: infeasible


def test_ray_without_feasible_point_is_rejected():
    r = check_lp_certificate(RAY_LP, Unbounded([-1, 0], [0, 1]))
    assert not r.valid
    assert keys(r) == [("primal_nonneg", "x", 0)]


def test_ray_case_shape_failure_skips_numeric_checks():
    r = check_lp_certificate(RAY_LP, Unbounded([-1], [0, 1]))
    assert keys(r) == [("shape", "x", None)]


def test_ray_case_infeasibility_certificate():
    assert check_lp_certificate(RAY_LP, Infeasible([-1])).valid


# ----------------------------------------------------------- degenerate shapes


def test_no_constraints_bounded_and_unbounded():
    bounded = StandardFormLP.build([], [], [1])
    assert (bounded.m, bounded.n) == (0, 1)
    assert check_lp_certificate(bounded, Optimal([0], [])).valid
    unbounded = StandardFormLP.build([], [], [-1])
    assert check_lp_certificate(unbounded, Unbounded([0], [1])).valid
    assert not check_lp_certificate(unbounded, Optimal([0], [])).valid  # dual infeasible


def test_no_variables():
    feasible = StandardFormLP.build(SparseMatrix.from_coo(2, 0, [], [], []), [0, 0], [])
    assert check_lp_certificate(feasible, Optimal([], [0, 0])).valid
    infeasible = StandardFormLP.build(SparseMatrix.from_coo(1, 0, [], [], []), [3], [])
    assert check_lp_certificate(infeasible, Infeasible([1])).valid


def test_empty_problem():
    p = StandardFormLP.build([], [], [])
    assert check_lp_certificate(p, Optimal([], [])).valid


def test_zero_row_and_zero_column():
    # row 2 is all zero with b = 5: infeasible via y = e_2
    p = StandardFormLP.build([[1, 0, 0], [0, 0, 0]], [1, 5], [1, 0, 0])
    assert check_lp_certificate(p, Infeasible([0, 1])).valid
    # zero column 3 with negative cost: unbounded along that column alone
    q = StandardFormLP.build([[1, 1, 0]], [1], [0, 0, -1])
    assert check_lp_certificate(q, Unbounded([1, 0, 0], [0, 0, 1])).valid


# --------------------------------------------------------- matrix construction


def test_coo_canonicalization():
    m1 = SparseMatrix.from_coo(2, 3, [1, 0, 1, 0, 0], [2, 1, 2, 1, 0], [4, 3, -4, 2, 0])
    assert m1.rows == (((1, F(5)),), ())
    assert m1 == SparseMatrix.from_dense([[0, 5, 0], [0, 0, 0]])
    assert m1.nnz == 1
    assert m1.to_dense() == [[0, 5, 0], [0, 0, 0]]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"m": 1, "n": 1, "rows": ()},  # too few rows
        {"m": 1, "n": 1, "rows": (((1, F(1)),),)},  # column out of range
        {"m": 1, "n": 3, "rows": (((2, F(1)), (1, F(1))),)},  # descending
        {"m": 1, "n": 3, "rows": (((1, F(1)), (1, F(2))),)},  # duplicate column
        {"m": 1, "n": 2, "rows": (((0, F(0)),),)},  # explicit zero
        {"m": 1, "n": 2, "rows": (((0, 1),),)},  # int, not Fraction
        {"m": 1, "n": 2, "rows": (((0, LyingFraction(1, 2)),),)},  # Fraction subclass
        {"m": 1, "n": 2, "rows": ([(0, F(1))],)},  # row is a list
        {"m": 1, "n": 2, "rows": (((0,),),)},  # malformed entry
        {"m": True, "n": 2, "rows": ((),)},  # bool dimension
        {"m": -1, "n": 2, "rows": ()},
    ],
)
def test_direct_sparse_matrix_construction_is_validated(kwargs):
    with pytest.raises(ValueError):
        SparseMatrix(**kwargs)


def test_standard_form_rejects_bad_parts():
    good = SparseMatrix.from_dense([[1]])

    class Sub(SparseMatrix):
        pass

    with pytest.raises(TypeError):
        StandardFormLP(Sub(1, 1, (((0, F(1)),),)), (F(1),), (F(0),))
    with pytest.raises(ValueError):
        StandardFormLP(good, (F(1), F(2)), (F(0),))
    with pytest.raises(ValueError):
        StandardFormLP(good, [F(1)], (F(0),))
    with pytest.raises(TypeError):
        StandardFormLP(good, (1,), (F(0),))
    with pytest.raises(ValueError):
        StandardFormLP.build([[1, 2]], [1], [0])  # c too short for the dense width
    with pytest.raises(ValueError):
        SparseMatrix.from_dense([])  # no rows and no n
    with pytest.raises(ValueError):
        SparseMatrix.from_dense([[1, 2], [3]])
    with pytest.raises(ValueError):
        SparseMatrix.from_coo(1, 1, [0], [1], [1])
    with pytest.raises(ValueError):
        SparseMatrix.from_coo(1, 1, [0], [0, 0], [1])
    with pytest.raises(TypeError):
        SparseMatrix.from_coo(1, 1, [True], [0], [1])


# ------------------------------------------------------------------------ types


def test_float_in_problem_raises_unless_coerced():
    with pytest.raises(TypeError, match="float"):
        StandardFormLP.build([[0.5]], [1], [0])
    p = StandardFormLP.build([[0.1]], [1], [0], coerce_float=True)
    (((_, v),),) = p.A.rows
    assert v == F(0.1) != F(1, 10)
    for bad in (float("nan"), float("inf")):
        with pytest.raises(TypeError):
            StandardFormLP.build([[bad]], [1], [0], coerce_float=True)
    with pytest.raises(TypeError):
        StandardFormLP.build([[True]], [1], [0])


def test_float_in_certificate_is_a_type_failure():
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, Optimal([1.0], [1]))
    assert keys(r) == [("type", "x", 0)]
    assert check_lp_certificate(p, Optimal([1.0], [1]), coerce_float=True).valid
    for bad in (float("nan"), float("inf"), True, "1", None, [1]):
        assert keys(check_lp_certificate(p, Optimal([bad], [1]), coerce_float=True)) == [
            ("type", "x", 0)
        ]
    assert keys(check_lp_certificate(p, Optimal([1], [1], value=1.0))) == [("type", "value", None)]


def test_gmpy2_mpq_accepted():
    gmpy2 = pytest.importorskip("gmpy2")
    p = StandardFormLP.build([[gmpy2.mpq(1, 2)]], [gmpy2.mpq(1)], [1])
    assert check_lp_certificate(p, Optimal([gmpy2.mpz(2)], [gmpy2.mpq(2)])).valid


def test_numpy_scalars():
    np = pytest.importorskip("numpy")
    p = StandardFormLP.build([[np.int64(2)]], [np.int64(4)], [1])
    assert check_lp_certificate(p, Optimal([np.int64(2)], [F(1, 2)])).valid
    assert keys(check_lp_certificate(p, Optimal([np.float64(2.0)], [F(1, 2)]))) == [
        ("type", "x", 0)
    ]
    assert check_lp_certificate(p, Optimal([np.float64(2.0)], [F(1, 2)]), coerce_float=True).valid


# ------------------------------------------------- hostile certificate inputs


def test_subclass_arithmetic_never_runs():
    p = lp(c=(1, 1, 1, 1))
    cert = Optimal(
        [LyingInt(2), LyingInt(1), LyingInt(0), LyingInt(0)],
        [LyingFraction(2, 5), LyingFraction(1, 5)],
        LyingInt(3),
    )
    assert check_lp_certificate(p, cert).valid  # arithmetic would raise Boom


def test_hostile_scalars_become_type_failures():
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, Optimal([BadRational()], [BadFloat(1.0)]), coerce_float=True)
    assert keys(r) == [("type", "x", 0), ("type", "y", 0)]


@pytest.mark.parametrize("container", [RaisingList([1]), LyingList([1]), None, 7, "1", {"x": 1}])
def test_hostile_containers_are_shape_failures(container):
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, Optimal(container, [1]))
    assert keys(r) == [("shape", "x", None)]


@pytest.mark.parametrize("cert", [NotACertificate(), None, 3, OptimalSubclass([1], [1])])
def test_non_certificates_are_claim_failures(cert):
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, cert)
    assert (r.valid, r.claim, keys(r)) == (False, "unknown", [("claim", None, None)])


def test_hostile_raising_classes_really_raise():
    # Guard: the fixtures above are only meaningful if they misbehave.
    with pytest.raises(Boom):
        LyingInt(1) + 1
    with pytest.raises(Boom):
        len(RaisingList([1]))
    with pytest.raises(Boom):
        BadRational().numerator  # noqa: B018


# ------------------------------------------------------------- failure limits


def test_max_failures_cap_and_validation():
    p = StandardFormLP.build([[1, 1]], [-1], [0, 0])
    full = check_lp_certificate(p, Infeasible([1]), max_failures=None)
    assert len(full.failures) == 3 and not full.truncated
    capped = check_lp_certificate(p, Infeasible([1]), max_failures=2)
    assert capped.failures == full.failures[:2] and capped.truncated and not capped.valid
    exact = check_lp_certificate(p, Infeasible([1]), max_failures=3)
    assert exact.failures == full.failures and not exact.truncated
    for bad in (0, -1, 1.5, True, "2"):
        with pytest.raises(ValueError):
            check_lp_certificate(p, Infeasible([1]), max_failures=bad)


def test_problem_type_is_checked():
    with pytest.raises(TypeError):
        check_lp_certificate("not a problem", Infeasible([1]))  # type: ignore[arg-type]


# ------------------------------------------------- degenerate optimum, duals


def test_every_dual_optimum_of_a_degenerate_lp_is_accepted():
    # Primal degenerate: x = (1, 0, 0) with basic variable x2 or x3 at zero.
    a = [[1, 1, 0], [1, 0, 1]]
    b = [1, 1]
    c = [1, 1, 1]
    status = exact_status([[F(v) for v in r] for r in a], [F(v) for v in b], [F(v) for v in c])
    assert status == ("optimal", F(1))
    duals = dual_optima([[F(v) for v in r] for r in a], [F(1), F(1)], [F(v) for v in c], F(1))
    assert len(duals) >= 2
    p = StandardFormLP.build(a, b, c)
    for y in duals:
        assert check_lp_certificate(p, Optimal([1, 0, 0], y)).valid


# ---------------------------------------------------------------- huge rationals


def test_huge_rationals_within_budget():
    big = 10**10_000
    a = [
        [F(big + 1, big - 1), F(1, big), F(2)],
        [F(3), F(big, 7), F(-1, big + 3)],
        [F(1), F(1), F(1)],
    ]
    b = [F(big + 11, 3), F(5, big), F(7)]
    c = [F(1, 3), F(big, big + 1), F(2, 9)]
    t = simplex_certificate(a, b, c)
    p = StandardFormLP.build(a, b, c)
    cert = {
        "optimal": lambda: Optimal(t[1], t[2]),
        "infeasible": lambda: Infeasible(t[1]),
        "unbounded": lambda: Unbounded(t[1], t[2]),
    }[t[0]]()
    start = time.perf_counter()
    r = check_lp_certificate(p, cert)
    elapsed = time.perf_counter() - start
    assert r.valid
    assert elapsed < 1.0, elapsed


# ---------------------------------------------------------- independence of policy


def test_checker_never_consults_the_registry(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the LP checker must not consult the registry")

    for name in ("get_basis", "list_bases", "get_hypothesis", "_load"):
        monkeypatch.setattr(registry, name, boom)
    test_valid_optimal()
    test_valid_infeasible()
    test_valid_unbounded()
    test_ray_without_feasible_point_is_rejected()


# ---------------------------------------------------------------------- README


def test_readme_example_runs():
    readme = (Path(__file__).parent.parent / "README.md").read_text("utf-8")
    match = re.search(r"## Example\n.*?```python\n(.*?)```", readme, re.S)
    assert match, "README needs an '## Example' section with a python block"
    exec(compile(match.group(1), "README.md", "exec"), {})


def test_failure_type_is_exported():
    assert Failure.__module__ == "corollarykit.lp.certificate"


# ------------------------------------------------- messages (caller-visible text)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"m": 1, "n": 1, "rows": ()}, r"rows must be a tuple of exactly m=1 rows"),
        ({"m": 0, "n": -1, "rows": ()}, r"m and n must be ints >= 0"),
        ({"m": 0, "n": True, "rows": ()}, r"m and n must be ints >= 0"),
        ({"m": 0, "n": 1.0, "rows": ()}, r"m and n must be ints >= 0"),
        ({"m": 1, "n": 2, "rows": ([(0, F(1))],)}, r"row 0 must be a tuple"),
        ({"m": 1, "n": 2, "rows": (([0, F(1)],),)}, r"row 0 entries must be \(j, value\) pairs"),
        ({"m": 1, "n": 2, "rows": (((0, F(1), 3),),)}, r"row 0 entries must be \(j, value\) pairs"),
        ({"m": 1, "n": 2, "rows": (((-1, F(1)),),)}, r"row 0 column indices must be in range"),
        ({"m": 1, "n": 2, "rows": (((0, F(0)),),)}, r"row 0 values must be nonzero Fractions"),
    ],
)
def test_sparse_matrix_messages(kwargs, message):
    with pytest.raises(ValueError, match=rf"^SparseMatrix: {message}"):
        SparseMatrix(**kwargs)


def test_constructor_messages():
    with pytest.raises(ValueError, match=r"^rows, cols and vals must have the same length$"):
        SparseMatrix.from_coo(1, 1, [0], [0], [])
    with pytest.raises(ValueError, match=r"^entry 0: row index 1 out of range for 1 rows$"):
        SparseMatrix.from_coo(1, 1, [1], [0], [1])
    with pytest.raises(ValueError, match=r"^entry 0: row index -1 out of range for 2 rows$"):
        SparseMatrix.from_coo(2, 1, [-1], [0], [1])  # would otherwise wrap to the last row
    with pytest.raises(TypeError, match=r"^rows\[0\]: bool is not an index$"):
        SparseMatrix.from_coo(1, 1, [True], [0], [1])
    with pytest.raises(TypeError, match=r"^cols\[0\]: bool is not an index$"):
        SparseMatrix.from_coo(1, 1, [0], [False], [1])
    with pytest.raises(TypeError, match=r"^m: bool is not an index$"):
        SparseMatrix.from_coo(True, 1, [], [], [])
    with pytest.raises(TypeError, match=r"^n: bool is not an index$"):
        SparseMatrix.from_coo(1, True, [], [], [])
    with pytest.raises(TypeError, match=r"^vals\[0\]: float is not an exact rational$"):
        SparseMatrix.from_coo(1, 1, [0], [0], [0.5])
    assert SparseMatrix.from_coo(1, 1, [0], [0], [0.5], coerce_float=True).rows == (
        ((0, F(1, 2)),),
    )
    with pytest.raises(ValueError, match=r"^from_dense: n is required when there are no rows$"):
        SparseMatrix.from_dense([])
    with pytest.raises(ValueError, match=r"^from_dense: rows have 2 columns, expected 3$"):
        SparseMatrix.from_dense([[1, 2]], n=3)
    with pytest.raises(ValueError, match=r"^from_dense: row 1 has length 1, expected 2$"):
        SparseMatrix.from_dense([[1, 2], [3]])
    with pytest.raises(TypeError, match=r"^vals\[0\]: float is not an exact rational$"):
        SparseMatrix.from_dense([[0.5]])
    assert SparseMatrix.from_dense([[0.5]], coerce_float=True).rows == (((0, F(1, 2)),),)
    good = SparseMatrix.from_dense([[1]])
    with pytest.raises(TypeError, match=r"^StandardFormLP: A must be a SparseMatrix$"):
        StandardFormLP([[1]], (F(1),), (F(0),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"^StandardFormLP: b must be a tuple of length 1$"):
        StandardFormLP(good, (), (F(0),))
    with pytest.raises(ValueError, match=r"^StandardFormLP: c must be a tuple of length 1$"):
        StandardFormLP(good, (F(1),), ())
    with pytest.raises(TypeError, match=r"^StandardFormLP: b entries must be Fractions$"):
        StandardFormLP(good, (1,), (F(0),))
    with pytest.raises(TypeError, match=r"^StandardFormLP: c entries must be Fractions$"):
        StandardFormLP(good, (F(1),), (0,))
    with pytest.raises(TypeError, match=r"^b\[0\]: float is not an exact rational$"):
        StandardFormLP.build([[1]], [0.5], [0])
    with pytest.raises(TypeError, match=r"^c\[1\]: str is not an exact rational$"):
        StandardFormLP.build([[1, 1]], [1], [0, "1"])
    p = StandardFormLP.build([[1]], [0.5], [0.25], coerce_float=True)
    assert (p.b, p.c) == ((F(1, 2),), (F(1, 4),))
    with pytest.raises(TypeError, match=r"^problem must be a StandardFormLP$"):
        check_lp_certificate(None, Infeasible([]))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"^max_failures must be an int >= 1, or None$"):
        check_lp_certificate(p, Infeasible([1]), max_failures=0)


def test_failure_details_and_claims():
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, NotACertificate())
    assert r.failures[0].detail == "not a certificate: NotACertificate"
    r = check_lp_certificate(p, Optimal(None, [1, 2]))
    assert r.claim == "optimal" and r.objective is None
    assert [f.detail for f in r.failures] == [
        "not a list/tuple: NoneType",
        "expected length 1, got 2",
    ]
    r = check_lp_certificate(p, Unbounded([0.5], ["1"]))
    assert r.claim == "unbounded" and r.objective is None
    assert [(f.detail, f.lhs, f.op, f.rhs) for f in r.failures] == [
        ("float", None, None, None),
        ("str", None, None, None),
    ]
    r = check_lp_certificate(p, Optimal([1], [1], value="3"))
    assert r.claim == "optimal" and r.failures[0].detail == "str"
    assert check_lp_certificate(p, Optimal([1], [1], value=1.0), coerce_float=True).valid


def test_failure_str_forms():
    p = lp(c=(1, 1, 1, 1))
    r = check_lp_certificate(p, Optimal([2, 1, 0, 1], [F(2, 5), F(1, 5)]))
    assert [str(f) for f in r.failures] == [
        "primal_eq[1] (x): 8 == 7 is false",
        "duality_gap: 4 == 3 is false",
    ]
    (f, _) = r.failures
    assert (f.lhs, f.op, f.rhs) == (F(8), "==", F(7))
    s = check_lp_certificate(StandardFormLP.build([[1]], [1], [1]), Optimal([1, 2], [1]))
    assert str(s.failures[0]) == "shape (x): expected length 1, got 2"
    assert str(Failure("claim", None, None, None, None, None, "x")) == "claim: x"


def test_default_cap_is_ten():
    n = 12
    p = StandardFormLP.build(SparseMatrix.from_coo(0, n, [], [], []), [], [0] * n)
    r = check_lp_certificate(p, Optimal([-1] * n, []))
    assert len(r.failures) == 10 and r.truncated and not r.valid
    assert len(check_lp_certificate(p, Optimal([-1] * n, []), max_failures=None).failures) == 12


def test_rational_edge_cases_never_raise():
    from _lp_strategies import StrNumerator, SubclassIntNumerator, ZeroDenRational

    p = StandardFormLP.build([[1]], [1], [1])
    for bad in (ZeroDenRational(), StrNumerator()):
        r = check_lp_certificate(p, Optimal([bad], [1]))
        assert [(f.check, f.field, f.index) for f in r.failures] == [("type", "x", 0)], bad
        with pytest.raises(TypeError):
            StandardFormLP.build([[bad]], [1], [1])
    # int() turns an __int__ that returns an int subclass into an exact int (with a
    # DeprecationWarning), so this one is accepted as the exact value 1.
    with pytest.warns(DeprecationWarning):
        assert check_lp_certificate(p, Optimal([SubclassIntNumerator()], [1])).valid


def test_tuple_certificates_are_accepted():
    p = lp(c=(1, 1, 1, 1))
    assert check_lp_certificate(p, Optimal((2, 1, 0, 0), (F(2, 5), F(1, 5)))).valid
    q = StandardFormLP.build([[1, -1]], [0], [-1, 0])
    assert check_lp_certificate(q, Unbounded((0, 0), (1, 1))).valid
    assert check_lp_certificate(
        StandardFormLP.build([[1, 1]], [-1], [0, 0]), Infeasible((-1,))
    ).valid


def test_shape_detail_names_the_actual_type():
    p = StandardFormLP.build([[1]], [1], [1])
    r = check_lp_certificate(p, Optimal(7, {"a": 1}))
    assert [f.detail for f in r.failures] == ["not a list/tuple: int", "not a list/tuple: dict"]
