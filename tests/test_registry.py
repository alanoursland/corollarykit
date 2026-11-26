import dataclasses
import itertools

import pytest
from _data import load_data

from corollarykit import ACCEPT_RH_ALPOGE, DEFAULT, Policy, Status, get_basis, list_bases
from corollarykit.registry import (
    Basis,
    Domain,
    Hypothesis,
    Proof,
    _load_from,
    effective_status,
    get_hypothesis,
)

# ----------------------------------------------------------------- data integrity


def test_registry_ships_in_wheel_and_parses():
    ids = {b.id for b in list_bases()}
    assert {"schoenfeld1976", "dusart2010.lower", "bach1990.miller"} <= ids


def test_dotted_ids_are_siblings():
    assert get_basis("bach1990.nonresidue").id == "bach1990.nonresidue"
    assert get_basis("bach1990.miller").id == "bach1990.miller"
    assert get_basis("bach1990.subgroup").id == "bach1990.subgroup"


@pytest.mark.parametrize("basis", list_bases(), ids=lambda b: b.id)
def test_basis_fields_are_complete(basis):
    assert basis.statement.strip()
    assert basis.source.strip()
    assert basis.domain_text.strip()
    assert isinstance(basis.status, Status)
    if basis.transcription_checked:
        assert basis.checked_against.strip()


def test_hypotheses_resolve():
    assert get_basis("schoenfeld1976").hypothesis is get_hypothesis("RH")
    assert get_basis("dusart2010.upper").hypothesis is None


def test_big_domain_bound_parses_from_string():
    assert get_basis("sorenson_webster2017").domain.lt == 3317044064679887385961981


def test_unchecked_lean_proof_counts_as_claimed():
    (proof,) = get_hypothesis("RH").proofs
    assert proof.status is Status.LEAN_COMPILED
    assert proof.effective_status is Status.CLAIMED


def test_quasi_grh_records_weaker_statement():
    assert "11/12" in get_hypothesis("quasi-GRH-dirichlet").statement


@pytest.mark.parametrize("hypothesis_id", ["GRH-dedekind", "GRH-hecke"])
def test_number_field_grh_has_no_proof(hypothesis_id):
    assert get_hypothesis(hypothesis_id).proofs == ()


# ------------------------------------------------------------------------ loader

MINIMAL = """
[hypotheses.H]
statement = "h"
[bases.b]
statement = "s"
domain_text = "x >= 1"
source = "src"
status = "classical"
transcription_checked = {checked}
checked_against = "{against}"
{extra}
"""


def _load(checked="false", against="", extra=""):
    return _load_from(MINIMAL.format(checked=checked, against=against, extra=extra))[1]["b"]


def test_checked_transcription_requires_citation():
    with pytest.raises(ValueError, match="checked_against"):
        _load(checked="true", against="")
    assert _load(checked="true", against="Thm 1, p. 3 - checked by X").transcription_checked


def test_loader_rejects_unknown_domain_key():
    with pytest.raises(ValueError, match="unknown domain keys"):
        _load(extra="domain = { at_least = 3 }")


def test_loader_rejects_non_boolean_transcription_flag():
    with pytest.raises(ValueError, match="boolean"):
        _load(checked='"yes"')


def test_loader_rejects_unknown_hypothesis():
    with pytest.raises(ValueError, match="unknown hypothesis"):
        _load(extra='hypothesis = "nope"')


# ------------------------------------------------------------------------ domain


@pytest.mark.parametrize(
    ("domain", "inside", "outside"),
    [
        (Domain(ge=5), [5, 6, 10**30], [4, 0, -1]),
        (Domain(gt=5), [6, 7], [5, 4]),
        (Domain(le=5), [5, 0, -10], [6]),
        (Domain(lt=5), [4, -3], [5, 6]),
        (Domain(ge=2, lt=10), [2, 9], [1, 10]),
        (Domain(), [-(10**9), 0, 10**9], []),
    ],
)
def test_domain_contains(domain, inside, outside):
    assert all(domain.contains(x) for x in inside)
    assert not any(domain.contains(x) for x in outside)


# --------------------------------------------------------- policy: truth table


def reference_accepts(policy: Policy, basis: Basis) -> bool:
    """The acceptance rule, restated independently of Policy.accepts."""
    if not (basis.transcription_checked or policy.allow_unchecked_transcriptions):
        return False
    if basis.status < policy.min_status:
        return False
    if basis.hypothesis is None:
        return True
    for proof in basis.hypothesis.proofs:
        if proof.status == Status.LEAN_COMPILED and proof.statement_match == "unchecked":
            eff = Status.CLAIMED
        else:
            eff = proof.status
        if eff >= policy.min_status or proof.id in policy.trusted_proofs:
            return True
    return False


PROOF_KINDS = [
    (Status.CLAIMED, "unchecked"),
    (Status.LEAN_COMPILED, "unchecked"),
    (Status.LEAN_COMPILED, "checked:x"),
    (Status.PEER_VERIFIED, "unchecked"),
    (Status.CLASSICAL, "unchecked"),
]
PROOF_SETS = [None, (), *[(k,) for k in PROOF_KINDS]] + [
    (a, b) for a, b in itertools.combinations(PROOF_KINDS, 2)
]


def _synthetic(own: Status, proof_set, transcribed: bool) -> Basis:
    hyp = None
    if proof_set is not None:
        proofs = tuple(
            Proof(f"p{i}", "src", status, match) for i, (status, match) in enumerate(proof_set)
        )
        hyp = Hypothesis("H", "h", proofs)
    return Basis("b", "s", "src", own, transcribed, hypothesis=hyp, domain_text="any")


def test_policy_truth_table():
    cases = 0
    for own, proof_set, transcribed, allow_unchecked, min_status, trust_first in itertools.product(
        Status, PROOF_SETS, [False, True], [False, True], Status, [False, True]
    ):
        basis = _synthetic(own, proof_set, transcribed)
        trusted = frozenset({"p0"}) if trust_first else frozenset()
        policy = Policy("t", min_status, trusted, allow_unchecked)
        assert policy.accepts(basis) == reference_accepts(policy, basis), (basis, policy)
        cases += 1
    assert cases > 2000


def test_default_refuses_unchecked_transcriptions():
    for basis in list_bases():
        assert DEFAULT.accepts(basis) == (
            basis.transcription_checked and reference_accepts(DEFAULT, basis)
        )


def test_rh_basis_needs_explicit_trust():
    lenient = Policy("t", allow_unchecked_transcriptions=True)
    trusting = Policy(
        "t2", trusted_proofs=ACCEPT_RH_ALPOGE.trusted_proofs, allow_unchecked_transcriptions=True
    )
    rh = get_basis("schoenfeld1976")
    assert lenient.accepts(get_basis("dusart2010.lower"))
    assert not lenient.accepts(rh)
    assert trusting.accepts(rh)
    quasi = dataclasses.replace(
        rh, id="synthetic", hypothesis=get_hypothesis("quasi-GRH-dirichlet")
    )
    assert not trusting.accepts(quasi)


def test_dedekind_bases_refused_even_when_trusting_alpoge():
    trusting = Policy(
        "t", trusted_proofs=ACCEPT_RH_ALPOGE.trusted_proofs, allow_unchecked_transcriptions=True
    )
    for basis_id in ["adleman_lenstra1986.A", "buchmann_shoup1996"]:
        assert not trusting.accepts(get_basis(basis_id))
    assert trusting.accepts(get_basis("bach1990.subgroup"))


def test_claimed_own_status_refused_even_with_classical_hypothesis():
    basis = _synthetic(Status.CLAIMED, ((Status.CLASSICAL, "unchecked"),), True)
    assert not Policy("t").accepts(basis)


# ------------------------------------------------------------ effective_status


def test_effective_status():
    lenient = Policy("t", allow_unchecked_transcriptions=True)
    assert effective_status(get_basis("dusart2010.lower"), lenient) is Status.CLASSICAL
    assert effective_status(get_basis("dusart2010.lower"), DEFAULT) is None
    trusting = Policy(
        "t2", trusted_proofs=ACCEPT_RH_ALPOGE.trusted_proofs, allow_unchecked_transcriptions=True
    )
    # Trusting a proof does not upgrade it: the basis reports the proof's own status.
    assert effective_status(get_basis("schoenfeld1976"), trusting) is Status.CLAIMED
    assert effective_status(get_basis("schoenfeld1976"), lenient) is None


# ----------------------------------------------------------------------- snapshot


def test_policy_snapshot_matches_registry():
    # tests/data/regen.py --check (test_data.py) guards freshness; this checks content shape.
    rows = load_data("policy_snapshot.txt")
    header, *body = rows
    assert header.startswith("basis\t")
    assert {r.split("\t")[0] for r in body} == {b.id for b in list_bases()}
