import dataclasses
import json
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from corollarykit.registry import Policy
from corollarykit.results import Claim, Result, Scope, compose, is_plain, plainify

LENIENT = Policy("t", allow_unchecked_transcriptions=True)
TRUSTING = Policy(
    "t2", trusted_proofs=frozenset({"alpoge-claude-2026"}), allow_unchecked_transcriptions=True
)


def test_claim_requires_basis_exactly_for_basis_scope():
    with pytest.raises(ValueError):
        Claim("c", Scope.BASIS, None)
    with pytest.raises(ValueError):
        Claim("c", Scope.FULL, "dusart2010.lower")
    Claim("c", Scope.BASIS, "dusart2010.lower")
    Claim("c", Scope.FULL, None)


@pytest.mark.parametrize("bad", [1.5, {1: 2}, object(), [1, 2.0], {"x": {3}}])
def test_claim_rejects_non_plain_certificate(bad):
    with pytest.raises(ValueError, match="plain"):
        Claim("c", Scope.FULL, None, bad)


def test_result_claims_are_immutable_and_keyed_by_name():
    r = Result(1, "exact", {"c": Claim("c", Scope.FULL, None)}, "default")
    with pytest.raises(TypeError):
        r.claims["d"] = Claim("d", Scope.FULL, None)  # type: ignore[index]
    with pytest.raises(ValueError):
        Result(1, "exact", {"x": Claim("c", Scope.FULL, None)}, "default")


def test_weakest_ordering():
    full = Claim("full", Scope.FULL, None)
    classical = Claim("classical", Scope.BASIS, "dusart2010.lower")
    rh = Claim("rh", Scope.BASIS, "schoenfeld1976")
    none = Claim("none", Scope.NONE, None)
    r = Result(0, "m", {c.name: c for c in [full, classical, rh, none]}, "t2")
    assert r.weakest(TRUSTING).name == "rh"  # trusted but claimed proof ranks lowest
    r2 = Result(0, "m", {c.name: c for c in [full, classical]}, "t")
    assert r2.weakest(LENIENT).name == "classical"
    assert Result(0, "m", {"full": full}, "t").weakest(LENIENT).name == "full"
    assert Result(0, "m", {"none": none}, "t").weakest(LENIENT) is None
    # A basis the policy refuses ranks below everything.
    r3 = Result(0, "m", {c.name: c for c in [rh, classical]}, "t")
    assert r3.weakest(LENIENT).name == "rh"


def _encode(o):
    if isinstance(o, Fraction):
        return {"fraction": [o.numerator, o.denominator]}
    raise TypeError(o)


def _decode(d):
    if set(d) == {"fraction"}:
        return Fraction(*d["fraction"])
    return d


def test_to_plain_round_trips_through_json():
    @dataclasses.dataclass(frozen=True)
    class Interval:
        lo: int
        hi: Fraction

    r = Result(
        Interval(1, Fraction(7, 3)),
        "analytic",
        {
            "bound_lo": Claim(
                "bound_lo", Scope.BASIS, "dusart2010.lower", {"x": [1, Fraction(1, 2)]}
            )
        },
        "default",
    )
    plain = r.to_plain()
    assert json.loads(json.dumps(plain, default=_encode), object_hook=_decode) == plain
    assert plain["value"] == {"lo": 1, "hi": Fraction(7, 3)}


def test_plainify_rejects_unknown_types():
    with pytest.raises(TypeError):
        plainify(1.0)
    with pytest.raises(TypeError):
        plainify({1, 2})


plain_trees = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=5) | st.fractions(),
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=4), children, max_size=4)
    ),
    max_leaves=20,
)


@given(plain_trees)
def test_plain_trees_survive(tree):
    assert is_plain(tree)
    Claim("c", Scope.FULL, None, tree)
    assert plainify(tree) == tree


def test_compose_copies_without_merging():
    helper = Result(
        97,
        "scan",
        {"primality": Claim("primality", Scope.BASIS, "sorenson_webster2017", {"bases": [2, 3]})},
        "default",
    )
    c = compose("primality_of_p", helper, "primality")
    assert (c.name, c.scope, c.basis, c.certificate) == (
        "primality_of_p",
        Scope.BASIS,
        "sorenson_webster2017",
        {"bases": [2, 3]},
    )
