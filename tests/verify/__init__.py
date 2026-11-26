"""Independent certificate checkers.

Rule: nothing in this package may import ``corollarykit`` except ``corollarykit.registry``.
Arithmetic here is deliberately naive and written out, so that a bug in a library helper
cannot also hide in the checker. See README.md.
"""
