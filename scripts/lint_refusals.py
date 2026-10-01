# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Lint data/refusals/*.yaml and Refusal("CODE") usage in src/. Run: uv run scripts/lint_refusals.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("code", "trigger", "message", "route")
CODE_FMT = re.compile(r"^AU-[A-Z]+-\d{3}$")
RAISE_RE = re.compile(r"""Refusal\(\s*["']([^"']+)["']""")


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
            for m in RAISE_RE.finditer(py.read_text()):
                if m.group(1) not in seen:
                    errs.append(f"{py.relative_to(root)}: Refusal('{m.group(1)}') not in catalogue")
    return errs


def main() -> int:
    errs = lint_refusals(ROOT)
    for e in errs:
        print(e)
    print(f"lint_refusals: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
