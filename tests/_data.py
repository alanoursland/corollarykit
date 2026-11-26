"""Reference-data loading with provenance and hash checks.

File format (tests/data/<name>)::

    # source: OEIS A006880
    # url: https://oeis.org/A006880
    # retrieved: 2026-11-26
    # sha256: <hex digest of the body bytes>
    <body lines>

The body is everything after the last header line. Large data sets are listed in
``tests/data/remote.toml`` and fetched only by slow tests through ``fetch_data``.
"""

from __future__ import annotations

import hashlib
import os
import tomllib
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REQUIRED_KEYS = {"source", "url", "retrieved", "sha256"}
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "corollarykit-tests"


class DataError(ValueError):
    pass


def split_header(raw: bytes) -> tuple[dict[str, str], bytes]:
    header: dict[str, str] = {}
    lines = raw.split(b"\n")
    i = 0
    while i < len(lines) and lines[i].startswith(b"# "):
        key, sep, value = lines[i][2:].decode("utf-8").partition(":")
        if not sep:
            raise DataError(f"malformed header line {i + 1}: {lines[i]!r}")
        header[key.strip()] = value.strip()
        i += 1
    body = b"\n".join(lines[i:])
    return header, body


def body_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def render(header: dict[str, str], body_lines: list[str]) -> bytes:
    """Build a data file; the sha256 header is computed here."""
    body = ("\n".join(body_lines) + "\n").encode("utf-8")
    header = {**header, "sha256": body_sha256(body)}
    head = "".join(f"# {k}: {header[k]}\n" for k in ("source", "url", "retrieved", "sha256"))
    extra = "".join(f"# {k}: {v}\n" for k, v in header.items() if k not in REQUIRED_KEYS)
    return (head + extra).encode("utf-8") + body


def check_file(path: Path) -> list[str]:
    header, body = split_header(path.read_bytes())
    missing = REQUIRED_KEYS - header.keys()
    if missing:
        raise DataError(f"{path.name}: missing header keys {sorted(missing)}")
    if body_sha256(body) != header["sha256"]:
        raise DataError(f"{path.name}: sha256 mismatch")
    return [line for line in body.decode("utf-8").split("\n") if line]


def load_data(name: str) -> list[str]:
    return check_file(DATA_DIR / name)


def fetch_data(name: str) -> bytes:
    """Download a large pinned data set (slow tests only), verifying its hash."""
    entries = tomllib.loads((DATA_DIR / "remote.toml").read_text("utf-8")).get("remote", [])
    entry = next((e for e in entries if e["name"] == name), None)
    if entry is None:
        raise DataError(f"{name} is not listed in remote.toml")
    cached = CACHE_DIR / name
    if not cached.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(entry["url"]) as response:
            cached.write_bytes(response.read())
    data = cached.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        cached.unlink()
        raise DataError(f"{name}: sha256 mismatch against remote.toml")
    return data


def data_files() -> list[Path]:
    return sorted(p for p in DATA_DIR.iterdir() if p.suffix == ".txt")
