# corollarykit

Algorithms and tools from recent mathematics, with every guarantee tied to the theorem it rests on.

**Status: planning.** The public API is stubbed. Design documents are in [`planning/`](planning/README.md), and implementation specs are in [`planning/specs/`](planning/specs/).

## Idea

Several 2026 results claim to settle hypotheses that many algorithms have long assumed: the Riemann hypothesis, GRH for Dirichlet L-functions, and others. None of them is fully verified yet. corollarykit implements the algorithms those results affect. Every output names the **basis** it relies on: a theorem with an exact statement, the hypothesis it needs, and the current status of that hypothesis. You choose which bases you accept:

```python
import corollarykit as ck

ck.DEFAULT                 # classical, checked theorems only
ck.ACCEPT_RH_ALPOGE        # also trust the Alpöge–Claude RH/GRH proof
ck.get_basis("schoenfeld1976").hypothesis.proofs
```

If a result turns out to be wrong, its registry entry changes and the default answers stay correct.

## Install (development)

```sh
pip install -e ".[dev]"
pytest
```

Requires Python ≥ 3.11. Optional extras: `arb` (python-flint, for rigorous ball arithmetic) and `fast` (gmpy2).

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
- MIT license ([LICENSE-MIT](LICENSE-MIT))

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this project by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any additional terms or conditions.
