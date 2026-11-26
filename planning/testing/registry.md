# Testing: registry and policies

Every guarantee in the library goes through `Policy.accepts`, so this is the most important test file.

## 1. Data integrity

- `bases.toml` parses and every basis names a known hypothesis. This test exists already.
- Every basis has a non-empty `statement`, `domain` and `source`, and a valid `status`.
- **Transcription gate:** every basis with `transcription_checked = true` must also have a `checked_against` field giving the page or equation and the checker's name. Fail if it's missing.
- Basis ids are unique after the dotted keys are flattened. Keep a regression test for the TOML nesting, where `bach1990.nonresidue` and `bach1990.miller` are siblings.
- **Wheel contents:** the installed wheel contains `bases.toml`. This is covered implicitly by `scripts/check.sh` testing the built wheel, and checked explicitly with `importlib.resources`.

## 2. Policy semantics

Build an **exhaustive truth table** over the synthetic cases: own status (4 values) × hypothesis (none, or one with proofs of statuses {∅, claimed, lean-compiled unchecked, lean-compiled checked, peer-verified, classical}) × `trusted_proofs` (empty, or containing that proof) × transcription (checked or not) × `allow_unchecked_transcriptions`. Compare `accepts()` against a direct, separately written restatement of the rule in the test.

Named cases:
- `lean-compiled` with `statement_match = unchecked` behaves as `claimed`. Exists already.
- Trusting `alpoge-claude-2026` doesn't accept quasi-GRH, `GRH-dedekind` or `GRH-hecke` bases. Exists already.
- `GRH-dedekind` and `GRH-hecke` have no proofs, so no policy short of a custom proof can accept them.
- A basis whose own status is `claimed` is refused even when its hypothesis is classical.

## 3. Result labeling (once algorithms exist)

- Property, for every public function and policy: each `*_basis` field in a result names a basis the policy accepts and whose domain contains the input, or is `exact` or `none`.
- No result reports a basis the function doesn't declare.

## 4. Change safety

- **Downgrade test:** load a modified registry in which `alpoge-claude-2026` is `claimed`. Every function under `ACCEPT_RH_ALPOGE` must then still return correct answers by falling back, with the reported bases changed accordingly. This is the "if the proof fails, nothing breaks" promise, tested directly.
- **Snapshot:** a stored list of (basis id, effective status under each built-in policy). Any change needs the snapshot updated in the same commit, which makes policy changes visible in review.
