"""Exceptions shared across corollarykit."""


class InconsistencyError(RuntimeError):
    """A theorem-backed bound was violated.

    This means one of three things: the cited theorem is false, its statement
    was transcribed incorrectly into the registry, or there is a bug. It is
    never an expected outcome.
    """


class BasisNotAccepted(LookupError):
    """No basis accepted by the active policy covers the requested input."""
