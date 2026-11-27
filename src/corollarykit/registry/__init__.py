"""The basis registry and acceptance policies.

The registry data lives in ``bases.toml`` next to this file and ships inside
the wheel. See that file's header for the model.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from fractions import Fraction
from functools import cache
from importlib.resources import files
from types import MappingProxyType
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


STATEMENT_MATCH_VALUES = ("unchecked", "partial", "checked")


@dataclass(frozen=True)
class Proof:
    id: str
    source: str
    status: Status
    statement_match: str
    statement_match_source: str = ""

    def __post_init__(self) -> None:
        if self.statement_match not in STATEMENT_MATCH_VALUES:
            raise ValueError(
                f"proof {self.id!r}: statement_match must be one of {STATEMENT_MATCH_VALUES}"
            )

    @property
    def effective_status(self) -> Status:
        """A Lean proof counts as claimed until its statement is matched to a vetted one."""
        if self.status == Status.LEAN_COMPILED and self.statement_match != "checked":
            return Status.CLAIMED
        return self.status


@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    proofs: tuple[Proof, ...]
    note: str = ""


@dataclass(frozen=True)
class Domain:
    """A numeric range on the basis's size variable. Missing bounds are unbounded."""

    ge: int | None = None
    gt: int | None = None
    le: int | None = None
    lt: int | None = None

    def contains(self, x: int) -> bool:
        return (
            (self.ge is None or x >= self.ge)
            and (self.gt is None or x > self.gt)
            and (self.le is None or x <= self.le)
            and (self.lt is None or x < self.lt)
        )


@dataclass(frozen=True)
class CeilingSpec:
    """A named ceiling formula with exact rational parameters (see corollarykit._bases)."""

    kind: str
    params: Mapping[str, Fraction]


@dataclass(frozen=True)
class Basis:
    id: str
    statement: str
    source: str
    status: Status
    transcription_checked: bool
    hypothesis: Hypothesis | None = None
    note: str = ""
    domain: Domain = field(default_factory=Domain)
    domain_text: str = ""
    requires: tuple[str, ...] = ()
    ceiling: CeilingSpec | None = None
    checked_against: str = ""


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

    def _accepted_proofs(self, basis: Basis) -> list[Proof]:
        assert basis.hypothesis is not None
        return [
            p
            for p in basis.hypothesis.proofs
            if p.effective_status >= self.min_status or p.id in self.trusted_proofs
        ]

    def accepts(self, basis: Basis) -> bool:
        if not (basis.transcription_checked or self.allow_unchecked_transcriptions):
            return False
        if basis.status < self.min_status:
            return False
        if basis.hypothesis is None:
            return True
        return bool(self._accepted_proofs(basis))


DEFAULT = Policy("default")
STRICT = Policy("strict")
ACCEPT_RH_ALPOGE = Policy("accept_rh_alpoge", trusted_proofs=frozenset({"alpoge-claude-2026"}))
BUILTIN_POLICIES = (DEFAULT, STRICT, ACCEPT_RH_ALPOGE)


def effective_status(basis: Basis, policy: Policy) -> Status | None:
    """How strong ``basis`` is under ``policy``, or None if the policy refuses it.

    This is the weaker of the basis's own status and the strongest proof the policy
    accepts for its hypothesis. A trusted proof still reports its own status: trusting
    a claimed proof doesn't make it classical.
    """
    if not policy.accepts(basis):
        return None
    if basis.hypothesis is None:
        return basis.status
    best = max(p.effective_status for p in policy._accepted_proofs(basis))
    return min(basis.status, best)


# ---------------------------------------------------------------------------- loading

_DOMAIN_KEYS = {"ge", "gt", "le", "lt"}


def _flatten(table: dict[str, Any], prefix: str = "") -> dict[str, dict[str, Any]]:
    """TOML dotted keys (dusart2010.lower) arrive nested; flatten to full ids."""
    out: dict[str, dict[str, Any]] = {}
    for key, value in table.items():
        full = f"{prefix}{key}"
        if "statement" in value:
            if full in out:
                raise ValueError(f"duplicate basis id {full!r}")
            out[full] = value
        else:
            for sub_id, sub in _flatten(value, f"{full}.").items():
                if sub_id in out:
                    raise ValueError(f"duplicate basis id {sub_id!r}")
                out[sub_id] = sub
    return out


def _int(value: Any, where: str) -> int:
    # Integers beyond 64 bits are written as strings to stay within portable TOML.
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"{where}: expected an integer, got {value!r}")
    return int(value)


def _parse_domain(raw: Any, bid: str) -> Domain:
    if raw is None:
        return Domain()
    if not isinstance(raw, dict):
        raise ValueError(f"basis {bid!r}: domain must be a table, got {raw!r}")
    unknown = raw.keys() - _DOMAIN_KEYS
    if unknown:
        raise ValueError(f"basis {bid!r}: unknown domain keys {sorted(unknown)}")
    return Domain(**{k: _int(v, f"basis {bid!r} domain.{k}") for k, v in raw.items()})


def _parse_ceiling(raw: Any, bid: str) -> CeilingSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or "kind" not in raw:
        raise ValueError(f"basis {bid!r}: ceiling must be a table with a 'kind'")
    params = {k: Fraction(str(v)) for k, v in raw.items() if k != "kind"}
    return CeilingSpec(kind=str(raw["kind"]), params=MappingProxyType(params))


def _parse_proof(p: dict[str, Any], hid: str) -> Proof:
    match = p["statement_match"]
    source = str(p.get("statement_match_source", "")).strip()
    if match != "unchecked" and not source:
        raise ValueError(
            f"hypothesis {hid!r} proof {p['id']!r}: statement_match = {match!r} requires "
            "statement_match_source (who checked, against what, where)"
        )
    return Proof(p["id"], p["source"], Status.parse(p["status"]), match, source)


def _parse(raw: dict[str, Any]) -> tuple[dict[str, Hypothesis], dict[str, Basis]]:
    hyps = {
        hid: Hypothesis(
            id=hid,
            statement=h["statement"],
            note=h.get("note", ""),
            proofs=tuple(_parse_proof(p, hid) for p in h.get("proofs", [])),
        )
        for hid, h in raw["hypotheses"].items()
    }
    bases = {}
    for bid, b in _flatten(raw["bases"]).items():
        hyp = b.get("hypothesis")
        if hyp is not None and hyp not in hyps:
            raise ValueError(f"basis {bid!r} names unknown hypothesis {hyp!r}")
        checked = b["transcription_checked"]
        if not isinstance(checked, bool):
            raise ValueError(f"basis {bid!r}: transcription_checked must be a boolean")
        checked_against = str(b.get("checked_against", ""))
        if checked and not checked_against.strip():
            raise ValueError(
                f"basis {bid!r}: transcription_checked = true requires checked_against "
                "(page/equation and checker)"
            )
        bases[bid] = Basis(
            id=bid,
            statement=b["statement"],
            source=b["source"],
            status=Status.parse(b["status"]),
            transcription_checked=checked,
            hypothesis=hyps[hyp] if hyp is not None else None,
            note=b.get("note", ""),
            domain=_parse_domain(b.get("domain"), bid),
            domain_text=b.get("domain_text", ""),
            requires=tuple(b.get("requires", ())),
            ceiling=_parse_ceiling(b.get("ceiling"), bid),
            checked_against=checked_against,
        )
    return hyps, bases


def _load_from(text: str) -> tuple[dict[str, Hypothesis], dict[str, Basis]]:
    """Parse registry TOML text. Test hook; the package itself uses _load()."""
    return _parse(tomllib.loads(text))


@cache
def _load() -> tuple[dict[str, Hypothesis], dict[str, Basis]]:
    return _load_from(files(__package__).joinpath("bases.toml").read_text("utf-8"))


def get_basis(basis_id: str) -> Basis:
    return _load()[1][basis_id]


def list_bases() -> list[Basis]:
    return list(_load()[1].values())


def get_hypothesis(hypothesis_id: str) -> Hypothesis:
    return _load()[0][hypothesis_id]


__all__ = [
    "ACCEPT_RH_ALPOGE",
    "BUILTIN_POLICIES",
    "DEFAULT",
    "STATEMENT_MATCH_VALUES",
    "STRICT",
    "Basis",
    "CeilingSpec",
    "Domain",
    "Hypothesis",
    "Policy",
    "Proof",
    "Status",
    "effective_status",
    "get_basis",
    "get_hypothesis",
    "list_bases",
]
