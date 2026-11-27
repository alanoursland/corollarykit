"""Property tests for check_lp_certificate (testing plan sections 2, 3, 6, 7)."""

from fractions import Fraction

import pytest
from _lp_oracle import exact_status, simplex_certificate
from _lp_strategies import (
    failure_keys,
    garbage_certs,
    perturb,
    raw_lps,
    to_cert,
    to_plain,
)
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from verify import lp as verify_lp

from corollarykit.lp import CheckResult, Optimal, SparseMatrix, check_lp_certificate

SETTINGS = settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)


def truth(raw):
    return exact_status(*raw.fractions())


# ------------------------------------------------------------- oracle sanity


@SETTINGS
@given(raw_lps())
def test_oracles_agree(raw):
    status = truth(raw)
    cert = simplex_certificate(*raw.fractions())
    assert cert[0] == status[0]
    if status[0] == "optimal":
        _, x, _ = cert
        assert sum(Fraction(c) * v for c, v in zip(raw.c, x, strict=True)) == status[1]


@SETTINGS
@given(raw_lps())
def test_coo_canonicalization_matches_independent_assembly(raw):
    p = raw.problem()
    assert p.A.to_dense() == raw.dense_independent()
    if raw.kind == "coo":
        assert SparseMatrix.from_dense(raw.dense_independent(), n=raw.n) == p.A


# ------------------------------------------------------------ completeness


@SETTINGS
@given(raw_lps())
def test_completeness(raw):
    cert = to_cert(simplex_certificate(*raw.fractions()))
    r = check_lp_certificate(raw.problem(), cert)
    assert r.valid, r.failures
    status = truth(raw)
    assert r.claim == status[0]
    if status[0] == "optimal":
        assert r.objective == status[1]


# ---------------------------------------------------------- soundness, agreement


def _assert_sound(raw, result):
    if result.valid:
        status = truth(raw)
        assert result.claim == status[0]
        if status[0] == "optimal":
            assert result.objective == status[1]


@SETTINGS
@given(st.data())
def test_soundness_and_agreement_on_garbage(data):
    raw = data.draw(raw_lps())
    cert = data.draw(garbage_certs(raw))
    coerce = data.draw(st.booleans())
    result = check_lp_certificate(raw.problem(), cert, max_failures=None, coerce_float=coerce)
    assert isinstance(result, CheckResult)  # never raises
    assert result.valid == (not result.failures)
    assert failure_keys(result) == verify_lp.check(to_plain(raw, cert, coerce))
    _assert_sound(raw, result)


@SETTINGS
@given(raw_lps(), st.integers(0, 50), st.sampled_from([Fraction(1, 7), Fraction(-1, 7), 1, -1]))
def test_perturbation(raw, which, delta):
    cert = perturb(to_cert(simplex_certificate(*raw.fractions())), which, Fraction(delta))
    result = check_lp_certificate(raw.problem(), cert, max_failures=None)
    expected = verify_lp.check(to_plain(raw, cert))
    assert failure_keys(result) == expected
    # A perturbation may land on another genuine certificate; it must then be sound.
    _assert_sound(raw, result)


@SETTINGS
@given(raw_lps())
def test_agreement_on_valid_and_value_variants(raw):
    t = simplex_certificate(*raw.fractions())
    cert = to_cert(t)
    variants = [cert]
    if t[0] == "optimal":
        value = sum(Fraction(c) * v for c, v in zip(raw.c, t[1], strict=True))
        variants += [Optimal(t[1], t[2], value), Optimal(t[1], t[2], value + 1)]
    for v in variants:
        result = check_lp_certificate(raw.problem(), v, max_failures=None)
        assert failure_keys(result) == verify_lp.check(to_plain(raw, v))


# -------------------------------------------------------------------- the cap


@SETTINGS
@given(st.data(), st.integers(1, 4))
def test_cap_is_a_prefix_and_validity_unchanged(data, k):
    raw = data.draw(raw_lps())
    cert = data.draw(garbage_certs(raw))
    full = check_lp_certificate(raw.problem(), cert, max_failures=None)
    capped = check_lp_certificate(raw.problem(), cert, max_failures=k)
    assert capped.failures == full.failures[:k]
    assert capped.truncated == (len(full.failures) > k)
    assert capped.valid == full.valid
    assert capped.objective == full.objective


# ------------------------------------------------------------ SciPy / HiGHS


def _rationalize(values):
    return [Fraction(float(v)).limit_denominator(10**6) for v in values]


@pytest.mark.oracle_highs
def test_highs_deterministic_case_validates():
    from scipy.optimize import linprog

    from corollarykit.lp import StandardFormLP

    a, b, c = [[1, 2], [3, 1]], [4, 7], [1, 1]
    res = linprog(c=c, A_eq=a, b_eq=b, bounds=[(0, None)] * 2, method="highs")
    assert res.status == 0
    cert = Optimal(_rationalize(res.x), _rationalize(res.eqlin.marginals))
    r = check_lp_certificate(StandardFormLP.build(a, b, c), cert)
    assert r.valid, r.failures
    assert r.objective == 3


@pytest.mark.oracle_highs
@SETTINGS
@given(raw_lps(max_m=3, max_n=5))
def test_highs_soundness(raw):
    from scipy.optimize import linprog

    if raw.n == 0:
        return
    a, b, c = raw.fractions()
    res = linprog(
        c=[float(v) for v in c],
        A_eq=[[float(v) for v in row] for row in a] or None,
        b_eq=[float(v) for v in b] or None,
        bounds=[(0, None)] * raw.n,
        method="highs",
    )
    if res.status != 0 or raw.m == 0:
        return
    cert = Optimal(_rationalize(res.x), _rationalize(res.eqlin.marginals))
    result = check_lp_certificate(raw.problem(), cert)
    _assert_sound(raw, result)
