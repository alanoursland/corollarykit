# tests/verify

Independent checkers for the certificates corollarykit emits.

**The independence rule.** Files here may import the standard library and `corollarykit.registry`, nothing else from `corollarykit`. `tests/test_verify_independence.py` enforces this by parsing every file. Dynamic imports (`importlib.import_module`, `__import__`) are forbidden too.

**Why.** A checker that reuses the library's sieve, Jacobi symbol or modular exponentiation would share that code's bugs, and would pass exactly the results it should catch.

**Adding a checker.** Add one module per certificate type (`lp.py`, `prime_count.py`, `primality.py`, ...). Each exposes:

```python
def check(plain: dict) -> list[str]:
    """Problems found in Result.to_plain() output; an empty list means valid."""
```

Start every checker with `plain.check_envelope(d)`, and build the arithmetic from `_naive.py` or write it out locally. Slow is fine.
