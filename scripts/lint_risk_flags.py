# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Lint the risk-flag and refusal catalogues. Run: uv run scripts/lint_risk_flags.py

Rules (CONVENTIONS section 7):
  1. Every data/risk_flags/*.yaml and data/refusals/*.yaml parses with yaml.safe_load.
  2. Risk-flag files have a top-level `risk_flags` list; each entry has a non-empty string `id`,
     `topic` and `description`, a non-empty list of string `citations`, and a non-empty list of
     string `skills` (each naming an existing folder under skills/).
  3. Risk-flag ids are unique across all files.
  4. Every risk-flag id cited in skills/*/SKILL.md or skills/*/references/*.md exists. Only
     id-shaped tokens are checked: UPPER-CASE ids whose first segment is used by a catalogue id,
     and back-ticked kebab-case ids whose first segment is used by a catalogue id (skill folder names
     are not ids). Prose is ignored.
  5. Every id a calculator emits (string literals appended to a *flag* list, or placed under a
     risk_flags / risk_flag_ids key) in src/ exists.

Refusal codes are otherwise checked by scripts/lint_refusals.py.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPPER_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
TICKED_KEBAB = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")
REFUSAL_FMT = re.compile(r"AU-[A-Z]+-\d{3}")
EMIT_KEYS = {"risk_flags", "risk_flag_ids"}
EMIT_METHODS = {"append", "extend", "add"}


def _load(path: Path, root: Path, errs: list[str]):
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        text = str(e).strip()
        first = text.splitlines()[0] if text else "parse error"
        mark = getattr(e, "problem_mark", None)
        where = f" at line {mark.line + 1}" if mark else ""
        errs.append(f"{path.relative_to(root)}: not valid YAML ({first}{where})")
        return None


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _str_list(v) -> bool:
    return isinstance(v, list) and bool(v) and all(_nonempty_str(x) for x in v)


def catalogue(root: Path, errs: list[str]) -> dict[str, Path]:
    """Return {flag id: file}, appending schema, parse and uniqueness problems to errs."""
    skills_dir = root / "skills"
    skill_names = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.exists() else set()
    ids: dict[str, Path] = {}
    for p in sorted((root / "data" / "risk_flags").glob("*.yaml")):
        rel = p.relative_to(root)
        doc = _load(p, root, errs)
        if doc is None:
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("risk_flags"), list):
            errs.append(f"{rel}: missing top-level 'risk_flags' list")
            continue
        for i, e in enumerate(doc["risk_flags"]):
            label = f"{rel} risk_flags[{i}]"
            if not isinstance(e, dict):
                errs.append(f"{label}: entry is not a mapping")
                continue
            fid = e.get("id")
            if _nonempty_str(fid):
                label = f"{rel} {fid}"
            else:
                errs.append(f"{label}: field 'id' missing or empty")
            for f in ("topic", "description"):
                if not _nonempty_str(e.get(f)):
                    errs.append(f"{label}: field '{f}' missing or empty")
            if not _str_list(e.get("citations")):
                errs.append(f"{label}: field 'citations' must be a non-empty list of strings")
            sk = e.get("skills")
            if not _str_list(sk):
                errs.append(f"{label}: field 'skills' must be a non-empty list of skill names")
            else:
                for s in sk:
                    if s not in skill_names:
                        errs.append(f"{label}: unknown skill '{s}' (no skills/{s}/ folder)")
            if _nonempty_str(fid):
                if fid in ids:
                    errs.append(f"duplicate risk flag id {fid} ({rel} and {ids[fid].relative_to(root)})")
                else:
                    ids[fid] = p
    return ids


def check_refusal_files(root: Path, errs: list[str]) -> set[str]:
    """Parse every refusals file; return the codes found."""
    codes: set[str] = set()
    for p in sorted((root / "data" / "refusals").glob("*.yaml")):
        doc = _load(p, root, errs)
        if doc is None:
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("refusals"), list):
            errs.append(f"{p.relative_to(root)}: missing top-level 'refusals' list")
            continue
        codes |= {e["code"] for e in doc["refusals"] if isinstance(e, dict) and isinstance(e.get("code"), str)}
    return codes


def check_skill_mentions(root: Path, ids: dict[str, Path], refusal_codes: set[str], errs: list[str]) -> None:
    upper_prefixes = {i.split("-")[0] for i in ids if i.isupper()}
    kebab_prefixes = {i.split("-")[0] for i in ids if i.islower()}
    skill_names = {p.name for p in (root / "skills").iterdir() if p.is_dir()}
    files = sorted((root / "skills").glob("*/SKILL.md")) + sorted((root / "skills").glob("*/references/*.md"))
    for f in files:
        text = f.read_text()
        seen = {
            t for t in UPPER_ID.findall(text)
            if t.split("-")[0] in upper_prefixes and t not in refusal_codes and not REFUSAL_FMT.fullmatch(t)
        }
        seen |= {t for t in TICKED_KEBAB.findall(text) if t.split("-")[0] in kebab_prefixes and t not in skill_names}
        for tok in sorted(seen - ids.keys()):
            errs.append(f"{f.relative_to(root)}: cites risk flag '{tok}' which is not in data/risk_flags")


def _strings(node: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def emitted_flags(py: Path) -> list[str]:
    """String literals a module appends to a *flag* list or puts under a risk_flags key."""
    out: list[str] = []
    for n in ast.walk(ast.parse(py.read_text())):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value in EMIT_KEYS:
                    out += _strings(v)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in EMIT_METHODS:
            tgt = n.func.value
            name = tgt.id if isinstance(tgt, ast.Name) else tgt.attr if isinstance(tgt, ast.Attribute) else ""
            if "flag" in name.lower():
                for a in n.args:
                    out += _strings(a)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value in EMIT_KEYS:
                    out += _strings(n.value)
    return out


def check_calculators(root: Path, ids: dict[str, Path], errs: list[str]) -> None:
    src = root / "src"
    if not src.exists():
        return
    for py in sorted(src.rglob("*.py")):
        for fid in sorted(set(emitted_flags(py)) - ids.keys()):
            errs.append(f"{py.relative_to(root)}: emits risk flag '{fid}' which is not in data/risk_flags")


def lint(root: Path) -> list[str]:
    errs: list[str] = []
    ids = catalogue(root, errs)
    codes = check_refusal_files(root, errs)
    check_skill_mentions(root, ids, codes, errs)
    check_calculators(root, ids, errs)
    return errs


def main() -> int:
    errs = lint(ROOT)
    for e in errs:
        print(e)
    print(f"lint_risk_flags: {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
