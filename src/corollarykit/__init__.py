"""corollarykit: algorithms from recent mathematics.

Every guarantee a function makes is tied to a named *basis*: a theorem with an
explicit statement, the hypothesis it needs, and the status of that hypothesis.
See ``corollarykit.registry`` and ``planning/README.md``.
"""

__version__ = "0.0.1.dev0"

import importlib

from corollarykit.errors import BasisNotAccepted, InconsistencyError
from corollarykit.registry import (
    ACCEPT_RH_ALPOGE,
    DEFAULT,
    STRICT,
    Basis,
    Policy,
    Status,
    get_basis,
    list_bases,
)

# Public algorithms are exported lazily (PEP 562). This module must import only
# errors and registry: tests/verify imports the registry, and an eager import here
# would pull library code into the independent checkers. See planning/architecture.md.
_LAZY = {
    name: "corollarykit.lp.certificate"
    for name in (
        "CheckResult",
        "Failure",
        "Infeasible",
        "Optimal",
        "SparseMatrix",
        "StandardFormLP",
        "Unbounded",
        "check_lp_certificate",
    )
}


def __getattr__(name: str) -> object:
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'corollarykit' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), *_LAZY])


__all__ = [
    "ACCEPT_RH_ALPOGE",
    "DEFAULT",
    "STRICT",
    "Basis",
    "BasisNotAccepted",
    "InconsistencyError",
    "Policy",
    "Status",
    "__version__",
    "get_basis",
    "list_bases",
]
