# Architecture: shared helpers, result types, build order

The planned functions share a small set of helpers. Two consequences shape the build order:
- **`is_prime_miller` and `prove_prime` are infrastructure.** Five other functions need proven primality.
- **One helper, `bach_scan`, is the only place the Dirichlet-GRH bound gets applied.**

## Module layout

Modules with a leading underscore are private. Their APIs can change without a deprecation period.

```
src/corollarykit/
    registry/            # bases.toml, Policy, Basis            (done)
    errors.py            # InconsistencyError, BasisNotAccepted (done)
    results.py           # Result base class, Claim, Scope, certificate payloads
    _bases.py            # select_bases, ceiling_upper
    _intmath.py          # integer helpers
    _search.py           # bach_scan, bounded_search
    _miller.py           # miller_sequence
    _balls.py            # Arb wrapper with outward rounding (optional dependency)
    _polyfp.py           # polynomials over F_p
    _factor.py           # factor_small
    primes/
        primality.py     # is_prime_miller, prove_prime
        count.py         # prime_count_interval, nth_prime_bounds, nth_prime
        gaps.py          # next_prime, prime_exists_between
        progression.py   # least_prime_in_progression, ntt_prime, prime_with_residue
        factor.py        # factor_with_phi
    modular/
        nonresidue.py    # least_nonresidue
        roots.py         # sqrt_mod_prime, nth_root_mod_prime
        primitive_root.py
    finite_fields/
        irreducible.py   # irreducible_polynomial
    lp/
        certificate.py   # check_lp_certificate
        solver.py        # solve_lp_exact (research)
    experimental/
tests/
    verify/              # independent checkers; must not import corollarykit except corollarykit.registry
```

## Helpers

### `_intmath.py`

Pure functions on Python ints, with no basis and no policy.

| Function | Contract | Used by |
|---|---|---|
| `small_primes(B) -> list[int]` | all primes ≤ B, from a cached sieve | almost everything |
| `sieve_segment(lo, hi) -> bytearray` | primality flags for the half-open (lo, hi] | `nth_prime`, `next_prime`, `prime_count_interval` (exact branch) |
| `progression_sieve(a, q, j0, j1, B) -> bytearray` | flags for a + jq, j ∈ [j0, j1), with multiples of primes ≤ B crossed off **except the primes themselves** | `least_prime_in_progression` |
| `jacobi(a, n) -> int` | Jacobi symbol, n odd and positive | non-residues, `sqrt_mod_prime`, `primitive_root` |
| `iroot(n, k) -> (r, exact)` | floor of the k-th root, and whether it is exact | `perfect_power` |
| `perfect_power(n) -> (r, k) or None` | the largest k with n = r^k | `is_prime_miller`, `factor_with_phi` |
| `trial_divide(n, B) -> (factors, cofactor)` | divide out the primes ≤ B | `prove_prime`, `factor_small` |
| `prime_count_exact(x) -> int` | odd-only `bytearray` sieve, with `primecount` when installed | `prime_count_interval`, `nth_prime` |

### `_bases.py`

| Function | Contract |
|---|---|
| `select_bases(policy, candidates, x) -> list[Basis]` | the bases in `candidates` that `policy` accepts and whose domain covers x, strongest first |
| `ceiling_upper(formula, x) -> int` | a **rigorous integer upper bound** on a ceiling formula. It uses rational bounds, ln n ≤ bit_length(n) · 6932/10000, and never Arb, so it works without optional dependencies. A ceiling that is too big is safe, because the search just runs longer. One that is too small would be a bug. |

Ceiling formulas are declared once, next to their basis id. For example, `bach1990.subgroup: 2·ln²n` and `lls2015: (φ(q)·ln q)²`. They are not repeated inside each algorithm.

### `_miller.py`

```python
def miller_sequence(n: int, m: int, a: int) -> Passes | Witness | Split
```

Write m = 2^s·t with t odd, and walk a^t, a^(2t), …, a^(2^s·t) mod n.
- `Passes`: the chain looks like n is prime.
- `Witness`: n is certainly composite. It carries the offending value.
- `Split(d)`: a nontrivial square root of 1 turned up, and d = gcd(x − 1, n).

| Caller | m |
|---|---|
| `is_prime_miller` | n − 1 |
| `factor_with_phi` | φ(n), or any multiple of λ(n) |

### `_search.py`

```python
def bach_scan(n: int, escapes: Callable[[int], T | None], *, basis: str, policy: Policy) -> ScanResult[T]
```

Tries **prime** bases a = 2, 3, 5, … and returns the first non-None `escapes(a)`.
- **Ceiling:** `ceiling_upper(basis formula, n)`, when `policy` accepts the basis. Otherwise there is no ceiling, and the result says so.
- **Passing the ceiling raises `InconsistencyError`**, except for callers whose basis defines "no escape below the ceiling" as the answer. Miller's test is one: with no witness found, the answer is "prime". Those callers set `exhaustion_means=...`.
- Restricting to prime bases is enforced here once. If every prime below B lay in a subgroup, every integer below B would too.

| Caller | `escapes(a)` |
|---|---|
| `is_prime_miller` | `miller_sequence(n, n−1, a)` is a `Witness` |
| `factor_with_phi` | `miller_sequence(n, m, a)` is a `Split` |
| `least_nonresidue(p, ℓ)` | a^((p−1)/ℓ) ≢ 1 (mod p), and for ℓ = 2, `jacobi(a, p) == −1` |

```python
def bounded_search(candidates: Iterator[int], test: Callable[[int], Accept | Reject],
                   *, ceiling: int | None, budget: int | None, collect: bool) -> SearchResult
```

The shared scan loop:
- It stops at the first `Accept`.
- Past `ceiling` it raises `InconsistencyError`. Past `budget` it returns `NoResult`. A missing ceiling with no budget means "search forever".
- With `collect=True`, it keeps every `Reject` witness (a factor or a compositeness witness). Those form the `full` minimality certificate.

Users: `next_prime`, `least_prime_in_progression`, `ntt_prime`, `prime_with_residue`, and the fallback scan in `irreducible_polynomial`.

### `primes/primality.py`: `prove_prime`

```python
def prove_prime(n: int, policy: Policy) -> PrimalityResult   # Prime(cert) | Composite(cert)
```

| Step | Can it accept? | Basis |
|---|---|---|
| trial division by small primes | yes, if n is itself a small prime | none |
| BPSW | **reject only** | none |
| fixed 13 bases, n < ψ₁₃ | yes | `sorenson_webster2017` |
| `is_prime_miller` in the GRH range | yes, if the policy accepts the basis | `bach1990.miller` |
| ECPP (optional backend, later) | yes | none; the certificate can be checked on its own |
| none of the above available | raise `BasisNotAccepted` | |

Users: `next_prime`, `least_prime_in_progression`, `primitive_root` (each prime factor of p−1), `factor_with_phi` (each output factor), and the `verify_prime=True` input checks.

### Others

| Module | Contents | Users |
|---|---|---|
| `modular/nonresidue.py` | `least_nonresidue(p, ℓ=2)`, cached per (p, ℓ) with an LRU | `sqrt_mod_prime`, `nth_root_mod_prime`, `primitive_root` (safe primes), `irreducible_polynomial` |
| `_balls.py` | `li_ball(x, prec)`, `floor_lower(ball)`, `ceil_upper(ball)`, rounded outward. Imports `flint` lazily and raises a clear error if it is missing. | `prime_count_interval`, `nth_prime_bounds` |
| `_polyfp.py` | dense polynomials over F_p: mul, divmod, powmod, gcd, composed product | `irreducible_polynomial`; Cipolla in `sqrt_mod_prime` (optional) |
| `_factor.py` | `factor_small(n, budget)`: trial division, then Pollard rho with a fixed seed so output is deterministic. Every factor is passed through `prove_prime`. | `primitive_root` (factoring p − 1), unit-distance scale selection |

## Result types (`results.py`)

A result can make **several claims, each with its own basis.**

For example, `least_prime_in_progression` claims three things:

| Claim | What it says | Rests on |
|---|---|---|
| `primality` | p is prime | `prove_prime`'s basis, such as `sorenson_webster2017` or `bach1990.miller` |
| `minimality` | no smaller prime in the class | the `full` witnesses (no basis), or nothing if only `membership` was requested |
| `termination` | the search was guaranteed to stop | `lls2015` or `bach_sorenson1996`, or `none` |

```python
class Scope(Enum):
    FULL = "full"            # checkable without trusting any basis
    BASIS = "basis"          # true if the named basis holds
    NONE = "none"            # claim not made (e.g. membership-only certificate)

@dataclass(frozen=True)
class Claim:
    name: str                # "primality", "minimality", "termination", "bound_lo", "bound_hi", ...
    scope: Scope
    basis: str | None        # basis id when scope is BASIS
    certificate: object      # plain data for tests/verify/; never library objects

@dataclass(frozen=True)
class Result(Generic[T]):
    value: T
    method: str              # "exact", "analytic", "scan", "theorem", ...
    claims: Mapping[str, Claim]
    policy: str
```

**Composition rule:** when a function uses a helper's result, it copies the helper's claim under its own claim name. It never merges the claims into one.

**Weakest-link view:** `Result.weakest()` returns the claim with the weakest scope, for callers who want one answer to "how much should I trust this?"

The function-specific types from the specs (`PrimeCountInterval`, `Root`, `NoRoot`, and so on) subclass `Result`. `PrimeCountInterval`'s `lo_basis` and `hi_basis` become `claims["bound_lo"]` and `claims["bound_hi"]`. The spec gets updated to match when it is implemented.

## Build order

There are three independent tracks:

```
Track A (analytic)        Track B (algebraic)                                Track C (LP)
──────────────────        ─────────────────────────────────────              ─────────────────
results, _bases           results, _bases, _intmath                          check_lp_certificate
_intmath (sieve)          _miller, _search                                         │
_balls                          │                                            solve_lp_exact (research)
     │                    is_prime_miller ──► prove_prime
prime_count_interval            │                    │
     │                    least_nonresidue      bounded_search
nth_prime_bounds           │        │            │          │
     │              sqrt/nth_root   │       next_prime   least_prime_in_progression
nth_prime                           │
              primitive_root (+_factor)   factor_with_phi   irreducible_polynomial (+_polyfp)
```

Suggested sequence:
1. **Foundations:** `results.py`, `_bases.py`, `_intmath.py`, and the `tests/verify/` skeleton. These have to come first.
2. **`check_lp_certificate`** (Track C). It has a ready spec and no dependencies, so it can happen in parallel.
3. **`prime_count_interval`** (Track A). It has a ready spec.
4. **`_miller`, `_search`, `is_prime_miller`, `prove_prime`** (Track B core). This is the riskiest shared code, so it gets the heaviest testing (see `testing/is_prime_miller.md`). It moves up from fifth in the earlier build order.
5. `least_nonresidue` → `sqrt_mod_prime`, `nth_root_mod_prime`.
6. `bounded_search` → `next_prime`, `least_prime_in_progression`.
7. `nth_prime_bounds`, `nth_prime`.
8. `factor_with_phi`, `primitive_root` (+ `_factor`), `irreducible_polynomial` (+ `_polyfp`).
9. **Research:** `solve_lp_exact`, then the `experimental/` modules.

## Rule for the package `__init__`

`import corollarykit.registry` runs `corollarykit/__init__.py`, and `tests/verify/` imports the registry. So **`__init__` must import only `errors` and `registry`.** `tests/test_verify_independence.py` checks this in a subprocess through `sys.modules`.

To expose algorithms at the top level (`corollarykit.check_lp_certificate`), use lazy exports with a module-level `__getattr__` (PEP 562). Never import them eagerly:

```python
_LAZY = {"check_lp_certificate": "corollarykit.lp.certificate"}

def __getattr__(name):
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'corollarykit' has no attribute {name!r}")

def __dir__():
    return sorted([*globals(), *_LAZY])
```

Add a test that each lazy name resolves, and that importing the registry still loads only the three modules.

## Rule for the test verifier

`tests/verify/` must **not** reuse these helpers. Shared helpers are exactly where a bug would show up in the library and its checker at once. The verifier gets its own deliberately naive implementations:
- trial-division primality for small n, with Pratt or ECPP certificate checking for large n;
- Jacobi by Euler's criterion;
- modular exponentiation by plain square-and-multiply;
- polynomial arithmetic on lists.

A lint test fails if any file in `tests/verify/` imports `corollarykit` outside `corollarykit.registry`.
