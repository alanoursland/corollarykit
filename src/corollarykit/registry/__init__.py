"""The basis registry and acceptance policies.

The registry data lives in ``bases.toml`` next to this file and ships inside
the wheel. See that file's header for the model.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from enum import IntEnum
from functools import cache
from importlib.resources import files
from typing import Any


class Status(IntEnum):
    """Status of a theorem or proof. Higher is stronger."""

    CLAIMED = 0
    LEAN_COMPILED = 1
    PEER_VERIFIED = 2
    CLASSICAL = 3

    @classmethod
    def parse(cls, text: str) -> Status:
        return cls[text.upper().replace("-", "_")]

    def __str__(self) -> str:
        return self.name.lower().replace("_", "-")


@dataclass(frozen=True)
class Proof:
    id: str
    source: str
    status: Status
    statement_match: str

    @property
    def effective_status(self) -> Status:
        """A Lean proof whose statements nobody has matched counts as claimed."""
        if self.status == Status.LEAN_COMPILED and self.statement_match == "unchecked":
            return Status.CLAIMED
        return self.status


@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    proofs: tuple[Proof, ...]
    note: str = ""


@dataclass(frozen=True)
class Basis:
    id: str
    statement: str
    domain: str
    source: str
    status: Status
    transcription_checked: bool
    hypothesis: Hypothesis | None = None
    note: str = ""


@dataclass(frozen=True)
class Policy:
    """Which bases a computation may rely on.

    A basis is accepted when its transcription has been checked (or
    ``allow_unchecked_transcriptions`` is set), its own status is at least
    ``min_status``, and, if it has a hypothesis, at least one proof of that
    hypothesis is either at least ``min_status`` or listed in ``trusted_proofs``.
    """

    name: str
    min_status: Status = Status.CLASSICAL
    trusted_proofs: frozenset[str] = field(default_factory=frozenset)
    allow_unchecked_transcriptions: bool = False

    def accepts(self, basis: Basis) -> bool:
        if not (basis.transcription_checked or self.allow_unchecked_transcriptions):
            return False
        if basis.status < self.min_status:
            return False
        if basis.hypothesis is None:
            return True
        return any(
            p.effective_status >= self.min_status or p.id in self.trusted_proofs
            for p in basis.hypothesis.proofs
        )


DEFAULT = Policy("default")
STRICT = Policy("strict")
ACCEPT_RH_ALPOGE = Policy("accept_rh_alpoge", trusted_proofs=frozenset({"alpoge-claude-2026"}))


def _flatten(table: dict[str, Any], prefix: str = "") -> dict[str, dict[str, Any]]:
    """TOML dotted keys (dusart2010.lower) arrive nested; flatten to full ids."""
    out: dict[str, dict[str, Any]] = {}
    for key, value in table.items():
        full = f"{prefix}{key}"
        if "statement" in value:
            out[full] = value
        else:
            out.update(_flatten(value, f"{full}."))
    return out


@cache
def _load() -> tuple[dict[str, Hypothesis], dict[str, Basis]]:
    raw = tomllib.loads(files(__package__).joinpath("bases.toml").read_text("utf-8"))
    hyps = {
        hid: Hypothesis(
            id=hid,
            statement=h["statement"],
            note=h.get("note", ""),
            proofs=tuple(
                Proof(p["id"], p["source"], Status.parse(p["status"]), p["statement_match"])
                for p in h.get("proofs", [])
            ),
        )
        for hid, h in raw["hypotheses"].items()
    }
    bases = {}
    for bid, b in _flatten(raw["bases"]).items():
        hyp = b.get("hypothesis")
        if hyp is not None and hyp not in hyps:
            raise ValueError(f"basis {bid!r} names unknown hypothesis {hyp!r}")
        bases[bid] = Basis(
            id=bid,
            statement=b["statement"],
            domain=b["domain"],
            source=b["source"],
            status=Status.parse(b["status"]),
            transcription_checked=bool(b["transcription_checked"]),
            hypothesis=hyps[hyp] if hyp is not None else None,
            note=b.get("note", ""),
        )
    return hyps, bases


def get_basis(basis_id: str) -> Basis:
    return _load()[1][basis_id]


def list_bases() -> list[Basis]:
    return list(_load()[1].values())


def get_hypothesis(hypothesis_id: str) -> Hypothesis:
    return _load()[0][hypothesis_id]


__all__ = [
    "ACCEPT_RH_ALPOGE",
    "DEFAULT",
    "STRICT",
    "Basis",
    "Hypothesis",
    "Policy",
    "Proof",
    "Status",
    "get_basis",
    "get_hypothesis",
    "list_bases",
]
