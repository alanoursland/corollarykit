import subprocess
import sys

import pytest
from _data import DATA_DIR, DataError, check_file, data_files, load_data, render


def test_every_data_file_has_valid_provenance():
    files = data_files()
    assert files, "tests/data should contain at least one file"
    for path in files:
        check_file(path)


def test_generated_files_are_up_to_date():
    result = subprocess.run(
        [sys.executable, str(DATA_DIR / "regen.py"), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_render_round_trip(tmp_path):
    path = tmp_path / "x.txt"
    path.write_bytes(render({"source": "s", "url": "u", "retrieved": "r"}, ["1", "2", "3"]))
    assert check_file(path) == ["1", "2", "3"]


def test_tampered_body_is_rejected(tmp_path):
    path = tmp_path / "x.txt"
    path.write_bytes(render({"source": "s", "url": "u", "retrieved": "r"}, ["1", "2"]))
    path.write_bytes(path.read_bytes().replace(b"2\n", b"3\n"))
    with pytest.raises(DataError, match="sha256"):
        check_file(path)


def test_missing_header_is_rejected(tmp_path):
    path = tmp_path / "x.txt"
    path.write_bytes(b"# source: s\n1\n")
    with pytest.raises(DataError, match="missing header"):
        check_file(path)


def test_primes_file_matches_known_count():
    primes = [int(x) for x in load_data("primes_below_100000.txt")]
    assert len(primes) == 9592
    assert primes[:5] == [2, 3, 5, 7, 11]
    assert primes[-1] == 99991
