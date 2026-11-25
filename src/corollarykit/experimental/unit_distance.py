"""Unit-distance point sets.

Plan: planning/unit_distance_construction.md
"""

from __future__ import annotations

from typing import Any


def erdos_grid(n: int) -> Any:
    """Integer lattice points plus a common squared scale m.

    A pair is at unit distance exactly when its squared integer distance is m.
    """
    raise NotImplementedError("see planning/unit_distance_construction.md")


def unit_distance_count(points: Any) -> int:
    raise NotImplementedError("see planning/unit_distance_construction.md")
