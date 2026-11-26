"""Result types shared by every public function.

A result can make several claims (for example "p is prime", "p is the least such
prime", "the search was guaranteed to stop"), each with its own scope and basis.
Certificates are plain data only, so the independent checkers in ``tests/verify``
never handle library objects.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Generic, TypeVar

from corollarykit.registry import Policy, Status, effective_status, get_basis

T = TypeVar("T")


class Scope(Enum):
    FULL = "full"  # checkable without trusting any basis
    BASIS = "basis"  # true if the named basis holds
    NONE = "none"  # this claim is not made


def is_plain(obj: object) -> bool:
    """True for int, str, bool, None, Fraction, and tuples, lists, str-keyed dicts of those
    (including the read-only mappings that frozen certificates use)."""
    if obj is None or isinstance(obj, bool | int | str | Fraction):
        return True
    if isinstance(obj, tuple | list):
        return all(is_plain(x) for x in obj)
    if isinstance(obj, dict | MappingProxyType):
        return all(isinstance(k, str) and is_plain(v) for k, v in obj.items())
    return False


def freeze(obj: Any) -> Any:
    """An immutable deep copy of plain data: lists become tuples, dicts read-only mappings."""
    if isinstance(obj, tuple | list):
        return tuple(freeze(x) for x in obj)
    if isinstance(obj, dict | MappingProxyType):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    return obj  # int, str, bool, None, Fraction: all immutable


def thaw(obj: Any) -> Any:
    """A fresh, mutable deep copy of frozen plain data: tuples become lists, mappings dicts."""
    if isinstance(obj, tuple | list):
        return [thaw(x) for x in obj]
    if isinstance(obj, dict | MappingProxyType):
        return {k: thaw(v) for k, v in obj.items()}
    return obj


def plainify(value: object) -> Any:
    """Convert a result value to plain data. Unknown types raise TypeError."""
    if value is None or isinstance(value, bool | int | str | Fraction):
        return value
    if isinstance(value, tuple | list):
        return [plainify(x) for x in value]
    if isinstance(value, dict):
        return {str(k): plainify(v) for k, v in value.items()}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: plainify(getattr(value, f.name)) for f in dataclasses.fields(value)}
    raise TypeError(f"cannot convert {type(value).__name__} to plain data")


@dataclass(frozen=True)
class Claim:
    name: str
    scope: Scope
    basis: str | None
    certificate: Any = None

    def __post_init__(self) -> None:
        if (self.scope is Scope.BASIS) != (self.basis is not None):
            raise ValueError(f"claim {self.name!r}: a basis id is required exactly for BASIS scope")
        if not is_plain(self.certificate):
            raise ValueError(f"claim {self.name!r}: certificate must be plain data")
        # Snapshot: later changes to the caller's object can't reach the claim, and the
        # claim can't be changed through anything it hands out.
        object.__setattr__(self, "certificate", freeze(self.certificate))


@dataclass(frozen=True)
class Result(Generic[T]):
    value: T
    method: str
    claims: Mapping[str, Claim]
    policy: str

    def __post_init__(self) -> None:
        for key, claim in self.claims.items():
            if key != claim.name:
                raise ValueError(f"claim stored under {key!r} is named {claim.name!r}")
        object.__setattr__(self, "claims", MappingProxyType(dict(self.claims)))

    def weakest(self, policy: Policy) -> Claim | None:
        """The made claim that deserves the least trust under ``policy``.

        FULL is strongest. BASIS claims are ordered by the effective status of their
        basis; a basis the policy no longer accepts ranks below everything.
        """
        made = [c for c in self.claims.values() if c.scope is not Scope.NONE]
        if not made:
            return None

        def strength(c: Claim) -> tuple[int, int]:
            if c.scope is Scope.FULL:
                return (1, int(Status.CLASSICAL))
            assert c.basis is not None
            status = effective_status(get_basis(c.basis), policy)
            return (0, -1 if status is None else int(status))

        return min(made, key=strength)

    def to_plain(self) -> dict[str, Any]:
        return {
            "value": plainify(self.value),
            "method": self.method,
            "policy": self.policy,
            "claims": {
                name: {
                    "scope": c.scope.value,
                    "basis": c.basis,
                    "certificate": thaw(c.certificate),
                }
                for name, c in self.claims.items()
            },
        }


def compose(own_name: str, helper: Result[Any], helper_claim: str) -> Claim:
    """Copy a helper's claim into the caller's result under a new name. Never merges."""
    c = helper.claims[helper_claim]
    return Claim(own_name, c.scope, c.basis, c.certificate)


__all__ = ["Claim", "Result", "Scope", "compose", "freeze", "is_plain", "plainify", "thaw"]
