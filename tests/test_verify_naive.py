from verify import _naive
from verify.plain import check_envelope


def test_powmod_matches_builtin():
    for b in range(-5, 20):
        for e in range(0, 30):
            for m in range(1, 25):
                assert _naive.powmod(b, e, m) == pow(b, e, m)


def test_is_prime_small():
    assert [n for n in range(30) if _naive.is_prime_small(n)] == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
    ]


def test_primes_upto_agrees_with_trial_division():
    assert _naive.primes_upto(2000) == [n for n in range(2001) if _naive.is_prime_small(n)]


def test_euler_criterion():
    # squares mod 7 are {1, 2, 4}
    assert [_naive.euler_criterion(a, 7) for a in range(7)] == [0, 1, 1, -1, 1, -1, -1]


def test_envelope_checker():
    good = {
        "value": 3,
        "method": "exact",
        "policy": "default",
        "claims": {"c": {"scope": "full", "basis": None, "certificate": None}},
    }
    assert check_envelope(good) == []
    bad = {**good, "claims": {"c": {"scope": "basis", "basis": None, "certificate": None}}}
    assert check_envelope(bad)
    unknown = {**good, "claims": {"c": {"scope": "basis", "basis": "nope", "certificate": None}}}
    assert any("unknown basis" in p for p in check_envelope(unknown))
