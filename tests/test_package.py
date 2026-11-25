import importlib
from importlib.metadata import metadata

import pytest

import corollarykit


def test_version_matches_metadata():
    assert metadata("corollarykit")["Version"] == corollarykit.__version__


def test_license_expression():
    assert metadata("corollarykit")["License-Expression"] == "MIT OR Apache-2.0"


STUBS = [
    ("corollarykit.primes", "prime_count_interval", (10**6,)),
    ("corollarykit.primes", "nth_prime_bounds", (10,)),
    ("corollarykit.primes", "nth_prime", (10,)),
    ("corollarykit.primes", "next_prime", (10,)),
    ("corollarykit.primes", "prime_exists_between", (10, 20)),
    ("corollarykit.primes", "least_prime_in_progression", (1, 4)),
    ("corollarykit.primes", "is_prime_miller", (97,)),
    ("corollarykit.primes", "factor_with_phi", (15, 8)),
    ("corollarykit.finite_fields", "irreducible_polynomial", (7, 3)),
    ("corollarykit.modular", "sqrt_mod_prime", (2, 7)),
    ("corollarykit.modular", "nth_root_mod_prime", (2, 3, 7)),
    ("corollarykit.modular", "primitive_root", (7,)),
    ("corollarykit.lp", "check_lp_certificate", (None, None)),
    ("corollarykit.lp.solver", "solve_lp_exact", (None, None, None)),
    ("corollarykit.experimental.sat_count", "count_sat_subexp", (None,)),
    ("corollarykit.experimental.unit_distance", "erdos_grid", (4,)),
]


@pytest.mark.parametrize(("module", "name", "args"), STUBS)
def test_planned_api_is_stubbed(module, name, args):
    fn = getattr(importlib.import_module(module), name)
    with pytest.raises(NotImplementedError):
        fn(*args)
