import dataclasses
import random
from fractions import Fraction

import mpmath
import pytest

from corollarykit import _bases
from corollarykit._bases import (
    ceiling_upper,
    ln1p_upper,
    ln_upper,
    select_bases,
    sqrt_upper,
    sqrt_upper_fraction,
    validate_registry_ceilings,
)
from corollarykit.registry import DEFAULT, CeilingSpec, Policy, get_basis, list_bases

mpmath.mp.prec = 400
LENIENT = Policy("t", allow_unchecked_transcriptions=True)
TRUSTING = Policy(
    "t2", trusted_proofs=frozenset({"alpoge-claude-2026"}), allow_unchecked_transcriptions=True
)


def mp(x: Fraction | int) -> mpmath.mpf:
    if isinstance(x, int):
        return mpmath.mpf(x)
    return mpmath.mpf(x.numerator) / x.denominator


def sample_n():
    rng = random.Random(3)
    fixed = [1, 2, 3, 4, 5, 7, 2**16, 2**16 - 1, 2**16 + 1, 2**32 - 1, 2**64 + 1]
    fixed += [2**k + d for k in (100, 1000, 4095) for d in (-1, 0, 1)]
    return fixed + [rng.getrandbits(rng.randint(2, 4096)) | 1 for _ in range(300)]


# ----------------------------------------------------------------------- ln bounds


def test_ln2_upper():
    assert mp(_bases.LN2_UP) > mpmath.log(2)
    assert mp(_bases.LN2_UP) - mpmath.log(2) < 1e-11


def test_ln_upper_sound_and_tight():
    for n in sample_n():
        diff = mp(ln_upper(n)) - mpmath.log(n)
        assert diff >= 0, n
        if n >= 2**16:
            assert diff < 1e-8, n


def test_ln1p_upper_sound_and_tight():
    rng = random.Random(4)
    ts = [Fraction(0), Fraction(1, 2), 1 - Fraction(1, 2**64)]
    ts += [Fraction(rng.getrandbits(64), 2**64) for _ in range(1000)]
    for t in ts:
        diff = mp(ln1p_upper(t)) - mpmath.log1p(mp(t))
        assert 0 <= diff < 1e-8, t


@pytest.mark.parametrize("bad", [Fraction(-1, 2), Fraction(1)])
def test_ln1p_upper_domain(bad):
    with pytest.raises(ValueError):
        ln1p_upper(bad)


def test_sqrt_upper():
    for x in range(0, 5000):
        s = sqrt_upper(x)
        assert s * s >= x and (s == 0 or (s - 1) ** 2 < x)


def test_sqrt_upper_fraction():
    for x in [*range(0, 3000), *(2**k + d for k in (64, 200, 4000) for d in (-1, 0, 1))]:
        u = sqrt_upper_fraction(x)
        assert u * u >= x
        assert mp(u) - mpmath.sqrt(x) <= mpmath.mpf(2) ** -64


@pytest.mark.oracle_flint
def test_ln_upper_against_arb():
    import flint

    flint.ctx.prec = 300
    for n in sample_n()[:100]:
        u = ln_upper(n)
        ball = flint.arb(n).log()
        # ln_upper must be at or above the ball's upper endpoint (equal only at n = 1).
        assert flint.arb(u.numerator) / u.denominator >= ball.mid() + ball.rad()


# ------------------------------------------------------------------------ ceilings

TRUE_FORMULAS = {
    "log_pow": lambda c, k, n: c * mpmath.log(n) ** k,
    "sqrt_log": lambda c, x: c * mpmath.sqrt(x) * mpmath.log(x),
    "qlogq_sq": lambda c, q: c * (q * mpmath.log(q)) ** 2,
    "phiqlogq_sq": lambda c, q, phi: c * (phi * mpmath.log(q)) ** 2,
}


def _true_value(basis, **inputs):
    p = {k: mp(v) for k, v in basis.ceiling.params.items()}
    kind = basis.ceiling.kind
    if kind == "log_pow":
        return TRUE_FORMULAS[kind](p["c"], int(p["k"]), mpmath.mpf(inputs["n"]))
    if kind == "sqrt_log":
        return TRUE_FORMULAS[kind](p["c"], mpmath.mpf(inputs["x"]))
    if kind == "qlogq_sq":
        return TRUE_FORMULAS[kind](p["c"], mpmath.mpf(inputs["q"]))
    phi = inputs.get("phi") or inputs["q"] - 1
    return TRUE_FORMULAS[kind](p["c"], mpmath.mpf(inputs["q"]), mpmath.mpf(phi))


INPUT_NAME = {"log_pow": "n", "sqrt_log": "x", "qlogq_sq": "q", "phiqlogq_sq": "q"}
CEILING_BASES = [b for b in list_bases() if b.ceiling is not None]


@pytest.mark.parametrize("basis", CEILING_BASES, ids=lambda b: b.id)
def test_ceiling_upper_sound_and_tight(basis):
    name = INPUT_NAME[basis.ceiling.kind]
    for n in sample_n():
        if n < 2:
            continue
        got = ceiling_upper(basis, **{name: n})
        true = _true_value(basis, **{name: n})
        assert got >= true, (basis.id, n)
        if n >= 2**16:
            assert got <= true * (1 + mpmath.mpf("1e-4")) + 2, (basis.id, n)


def test_phi_bound_uses_supplied_phi():
    b = get_basis("lls2015")
    q = 2**61 - 1  # prime, so phi = q - 1
    assert ceiling_upper(b, q=q) == ceiling_upper(b, q=q, phi=q - 1)
    assert ceiling_upper(b, q=30, phi=8) < ceiling_upper(b, q=30)
    with pytest.raises(ValueError):
        ceiling_upper(b, q=30, phi=30)


def test_ceiling_upper_without_ceiling():
    with pytest.raises(ValueError, match="no ceiling"):
        ceiling_upper("dusart2010.lower", n=10)


def test_registry_ceilings_validate():
    validate_registry_ceilings()
    b = get_basis("bach1990.miller")
    for bad in [
        CeilingSpec("nope", {"c": Fraction(2)}),
        CeilingSpec("log_pow", {"c": Fraction(2)}),
        CeilingSpec("log_pow", {"c": Fraction(2), "k": Fraction(3, 2)}),
        CeilingSpec("log_pow", {"c": Fraction(0), "k": Fraction(2)}),
    ]:
        with pytest.raises(ValueError):
            validate_registry_ceilings([dataclasses.replace(b, ceiling=bad)])


# ---------------------------------------------------------------------- selection


def test_select_bases_is_empty_under_default_while_unchecked():
    ids = [b.id for b in list_bases()]
    assert all(b.transcription_checked for b in select_bases(DEFAULT, ids, 10**6))


def test_select_bases_domain_edges():
    assert [b.id for b in select_bases(TRUSTING, ["schoenfeld1976"], 2656)] == []
    assert [b.id for b in select_bases(TRUSTING, ["schoenfeld1976"], 2657)] == ["schoenfeld1976"]
    assert select_bases(LENIENT, ["schoenfeld1976"], 2657) == []  # RH proof not trusted


def test_select_bases_preserves_caller_order():
    ids = ["rosser_schoenfeld1962.upper", "dusart2010.lower", "rosser_schoenfeld1962.lower"]
    got = [b.id for b in select_bases(LENIENT, ids, 10**6)]
    assert got == ids


def test_select_bases_unknown_id_is_a_bug():
    with pytest.raises(KeyError):
        select_bases(LENIENT, ["no-such-basis"], 1)
