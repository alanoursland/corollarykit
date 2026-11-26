"""tests/verify must not import corollarykit beyond corollarykit.registry."""

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

VERIFY_DIR = Path(__file__).parent / "verify"
ALLOWED = ("corollarykit.registry",)


def _violations(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
                if node.module == "corollarykit":
                    names = [f"corollarykit.{alias.name}" for alias in node.names]
            elif isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if name in ("import_module", "__import__"):
                    found.append(f"{path.name}:{node.lineno} dynamic import")
            for name in names:
                if name == "corollarykit" or (
                    name.startswith("corollarykit.")
                    and not any(name == a or name.startswith(a + ".") for a in ALLOWED)
                ):
                    found.append(f"{path.name}:{node.lineno} imports {name}")
    return found


def test_verify_package_is_independent():
    assert _violations(VERIFY_DIR) == []


def test_lint_catches_violations(tmp_path):
    (tmp_path / "bad1.py").write_text("import corollarykit._intmath\n")
    (tmp_path / "bad2.py").write_text("from corollarykit import results\n")
    (tmp_path / "bad3.py").write_text("from corollarykit._bases import ln_upper\n")
    (tmp_path / "bad4.py").write_text("import importlib\nimportlib.import_module('x')\n")
    (tmp_path / "ok.py").write_text("from corollarykit.registry import get_basis\nimport math\n")
    found = _violations(tmp_path)
    assert len(found) == 4, found
    assert not any(f.startswith("ok.py") for f in found)


def test_importing_registry_loads_nothing_else():
    code = textwrap.dedent(
        """
        import sys
        import corollarykit.registry
        loaded = sorted(m for m in sys.modules if m.startswith("corollarykit"))
        print(",".join(loaded))
        """
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    loaded = set(out.stdout.strip().split(","))
    assert loaded == {"corollarykit", "corollarykit.errors", "corollarykit.registry"}, loaded
