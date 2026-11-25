"""corollarykit: algorithms from recent mathematics.

Every guarantee a function makes is tied to a named *basis*: a theorem with an
explicit statement, the hypothesis it needs, and the status of that hypothesis.
See ``corollarykit.registry`` and ``planning/README.md``.
"""

__version__ = "0.0.1.dev0"

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
