# Changelog

Nothing is published to PyPI until 1.0. Milestones are tagged in git (`m0`, `m1`, ...).

## Unreleased

### M1: LP certificate checker

- `check_lp_certificate` for standard-form LPs (min cᵀx, Ax = b, x ≥ 0), with `Optimal`, `Infeasible` and `Unbounded` certificates checked in exact rational arithmetic.
- `SparseMatrix` (COO and dense factories, invariants enforced on every construction path) and `StandardFormLP`.
- Certificates are untrusted input: shape, then type, then numeric checks; never raises because of a certificate; subclass arithmetic never runs inside a check.
- Top-level lazy exports: `corollarykit.check_lp_certificate` and the LP types.
- Tests: independent dense checker compared on full failure sets, enumeration and simplex oracles, property tests, SciPy/HiGHS soundness; all mutants of `certificate.py` killed (`scripts/mutmut.sh`).
- `oracles` extra gains `scipy`.

### M0: Foundations

- Basis registry with structured domains, ceilings, transcription and statement-match citations, and policies.
- Result types with plain-data certificates; integer helpers; rigorous ceilings.
- Independent verifier package with an import lint; `scripts/check.sh` replaces CI.
