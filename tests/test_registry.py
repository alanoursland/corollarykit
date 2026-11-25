import dataclasses

import pytest

from corollarykit import ACCEPT_RH_ALPOGE, DEFAULT, Policy, Status, get_basis, list_bases
from corollarykit.registry import get_hypothesis


def test_registry_ships_in_wheel_and_parses():
    ids = {b.id for b in list_bases()}
    assert {"schoenfeld1976", "dusart2010.lower", "bach1990.miller"} <= ids


def test_hypotheses_resolve():
    assert get_basis("schoenfeld1976").hypothesis is get_hypothesis("RH")
    assert get_basis("dusart2010.upper").hypothesis is None


def test_unchecked_lean_proof_counts_as_claimed():
    (proof,) = get_hypothesis("RH").proofs
    assert proof.status is Status.LEAN_COMPILED
    assert proof.effective_status is Status.CLAIMED


def test_quasi_grh_records_weaker_statement():
    assert "11/12" in get_hypothesis("quasi-GRH-dirichlet").statement


@pytest.mark.parametrize("basis_id", [b.id for b in list_bases()])
def test_default_refuses_unchecked_transcriptions(basis_id):
    basis = get_basis(basis_id)
    assert DEFAULT.accepts(basis) == basis.transcription_checked


def test_rh_basis_needs_explicit_trust():
    lenient = Policy("t", allow_unchecked_transcriptions=True)
    trusting = Policy(
        "t2", trusted_proofs=ACCEPT_RH_ALPOGE.trusted_proofs, allow_unchecked_transcriptions=True
    )
    rh = get_basis("schoenfeld1976")
    classical = get_basis("dusart2010.lower")
    assert lenient.accepts(classical)
    assert not lenient.accepts(rh)
    assert trusting.accepts(rh)
    # Trusting Alpöge-Claude does not extend to OpenAI's quasi-GRH claim.
    quasi_hyp = get_hypothesis("quasi-GRH-dirichlet")
    quasi = dataclasses.replace(rh, id="synthetic", hypothesis=quasi_hyp)
    assert not trusting.accepts(quasi)


@pytest.mark.parametrize("hypothesis_id", ["GRH-dedekind", "GRH-hecke"])
def test_number_field_grh_has_no_proof(hypothesis_id):
    assert get_hypothesis(hypothesis_id).proofs == ()


def test_dedekind_bases_refused_even_when_trusting_alpoge():
    trusting = Policy(
        "t", trusted_proofs=ACCEPT_RH_ALPOGE.trusted_proofs, allow_unchecked_transcriptions=True
    )
    for basis_id in ["adleman_lenstra1986.A", "buchmann_shoup1996"]:
        assert not trusting.accepts(get_basis(basis_id))
    assert trusting.accepts(get_basis("bach1990.subgroup"))
