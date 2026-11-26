"""Structural checks of Result.to_plain() output."""

from __future__ import annotations

from typing import Any

from corollarykit.registry import list_bases

SCOPES = {"full", "basis", "none"}
ENVELOPE_KEYS = {"value", "method", "policy", "claims"}


def check_envelope(d: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(d, dict):
        return ["result is not a dict"]
    missing = ENVELOPE_KEYS - d.keys()
    if missing:
        problems.append(f"missing keys {sorted(missing)}")
    claims = d.get("claims", {})
    if not isinstance(claims, dict):
        return [*problems, "claims is not a dict"]
    known = {b.id for b in list_bases()}
    for name, c in claims.items():
        if not isinstance(c, dict):
            problems.append(f"claim {name!r} is not a dict")
            continue
        scope, basis = c.get("scope"), c.get("basis")
        if scope not in SCOPES:
            problems.append(f"claim {name!r}: bad scope {scope!r}")
        if (scope == "basis") != (basis is not None):
            problems.append(f"claim {name!r}: basis must be set exactly for scope 'basis'")
        if basis is not None and basis not in known:
            problems.append(f"claim {name!r}: unknown basis {basis!r}")
    return problems
