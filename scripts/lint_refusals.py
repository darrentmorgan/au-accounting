# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Lint data/refusals/*.yaml and Refusal("CODE") usage in src/. Run: uv run scripts/lint_refusals.py"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("code", "trigger", "message", "route")
CODE_FMT = re.compile(r"^AU-[A-Z]+-\d{3}$")


def refusal_literals(tree: ast.AST):
    """Find positional/keyword codes, including imported aliases and qualified calls.

    Non-literal codes are checked by Refusal itself when constructed. Parsing the
    syntax also avoids treating examples in comments or docstrings as real calls.
    """
    names = {"Refusal"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "au_tax.registry":
            names.update(alias.asname or alias.name for alias in node.names if alias.name == "Refusal")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not ((isinstance(func, ast.Name) and func.id in names)
                or (isinstance(func, ast.Attribute) and func.attr == "Refusal")):
            continue
        code = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "code"), None)
        if isinstance(code, ast.Constant) and isinstance(code.value, str):
            yield node.lineno, code.value


def _entries(root: Path) -> list[dict]:
    out: list[dict] = []
    for p in sorted((root / "data" / "refusals").glob("*.yaml")):
        out += (yaml.safe_load(p.read_text()) or {}).get("refusals", [])
    return out


def catalogue_codes(root: Path) -> set[str]:
    return {e.get("code") for e in _entries(root) if isinstance(e, dict)}


def lint_refusals(root: Path) -> list[str]:
    errs: list[str] = []
    seen: set[str] = set()
    for i, e in enumerate(_entries(root)):
        for f in FIELDS:
            if not isinstance(e.get(f), str) or not e[f].strip():
                errs.append(f"refusals[{i}] ({e.get('code')}): field '{f}' missing or empty")
        code = e.get("code")
        if isinstance(code, str):
            if not CODE_FMT.match(code):
                errs.append(f"refusals[{i}]: code '{code}' does not match AU-XXX-000")
            if code in seen:
                errs.append(f"refusals: duplicate code {code}")
            seen.add(code)
    src = root / "src"
    if src.exists():
        for py in sorted(src.rglob("*.py")):
            try:
                tree = ast.parse(py.read_text(), filename=str(py))
            except SyntaxError as e:
                errs.append(f"{py.relative_to(root)}:{e.lineno}: invalid Python: {e.msg}")
                continue
            for line, code in refusal_literals(tree):
                if code not in seen:
                    errs.append(f"{py.relative_to(root)}:{line}: Refusal('{code}') not in catalogue")
    return errs


def main() -> int:
    errs = lint_refusals(ROOT)
    for e in errs:
        print(e)
    print(f"lint_refusals: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
