# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Lint skills. Run: uv run scripts/lint_skills.py [--root DIR]

Rules: frontmatter (name, description), SKILL.md < 500 lines, no hard-coded figures in prose
(dollar amounts, percentages, amounts with a thousands separator, business-day counts, and day
counts equal to a day-count figure in data/rates; allowlist data/lint_allowlist.yaml), banned synonyms
(data/glossary_banned.yaml, preferred terms in docs/GLOSSARY.md), refusal codes exist, tool names exist in
the registry, plus refusal catalogue checks (see lint_refusals.py). Exit 1 on any finding.
"""
from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CODE_RE = re.compile(r"AU-[A-Z]+-\d{3}")
DOLLAR_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|million|billion))?", re.I)
PCT_RE = re.compile(r"\d+(?:\.\d+)?\s?(?:%|per cent\b)", re.I)
# Bare amounts with a thousands separator (3,430 / 50,430 / 1,500,000), with or without a $.
THOUSANDS_RE = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d,])")
# Day counts: "7 business days", "28 continuous days", "90 days".
DAYS_RE = re.compile(r"\b(\d+)\s+(?:(business|calendar|continuous|consecutive)\s+)?days?\b", re.I)
DAY_UNITS = {"days", "business_days", "business days"}
MCP_PREFIX = "mcp__plugin_au-accounting_au-tax__"
BUILTIN_TOOLS = {"list_figures", "get_figure"}
TOOL_MCP_RE = re.compile(r"`" + re.escape(MCP_PREFIX) + r"([A-Za-z0-9_]+)`")
TOOL_BARE_RE = re.compile(r"`([a-z][a-z0-9_]*)`\s+(?:tool|calculator)\b")


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, m.group(2)
    return (fm if isinstance(fm, dict) else None), m.group(2)


def prose_lines(text: str):
    """Yield (lineno, line) for lines outside fenced code blocks."""
    fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if not fence:
            yield i, line


def load_allowlist(root: Path) -> list[dict]:
    p = root / "data" / "lint_allowlist.yaml"
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text()) or {}).get("allow", [])


URL_RE = re.compile(r"https?://\S+")
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def load_banned(root: Path) -> list[tuple[re.Pattern, str, str]]:
    """(pattern, synonym, preferred) from data/glossary_banned.yaml. Empty when the file is absent."""
    p = root / "data" / "glossary_banned.yaml"
    if not p.exists():
        return []
    out: list[tuple[re.Pattern, str, str]] = []
    for entry in (yaml.safe_load(p.read_text()) or {}).get("banned", []):
        for syn in entry["synonyms"]:
            rx = re.compile(r"(?<![\w-])" + re.escape(syn) + r"s?(?![\w-])", re.I)
            out.append((rx, syn, entry["preferred"]))
    return out


def banned_findings(line: str, banned: list[tuple[re.Pattern, str, str]]) -> list[str]:
    """Messages for banned synonyms in one prose line (URLs and inline code removed here)."""
    line = INLINE_CODE_RE.sub("", URL_RE.sub("", line))
    return [
        f"banned term '{m.group(0)}': use '{preferred}' (docs/GLOSSARY.md)"
        for rx, _syn, preferred in banned
        for m in rx.finditer(line)
    ]


def day_count_values(root: Path) -> set[int]:
    """Values of every day-count figure (unit days or business days) in data/rates, base and
    overlays. A bare "N days" in prose with one of these values duplicates a figure key."""
    out: set[int] = set()

    def walk(node):
        if isinstance(node, dict):
            if "status" in node:
                if str(node.get("unit", "")).strip().lower() in DAY_UNITS and isinstance(node.get("value"), int):
                    out.add(node["value"])
                return
            for child in node.values():
                walk(child)

    rates = root / "data" / "rates"
    for f in sorted(rates.glob("*.yaml")) + sorted(rates.glob("*.d/*.yaml")):
        walk(yaml.safe_load(f.read_text()) or {})
    return out


def figure_findings(line: str, day_values: set[int]) -> list[tuple[str, str]]:
    """(kind, text) for every hard-coded figure in one prose line (URLs already removed)."""
    found: list[tuple[str, str]] = []
    spans: list[tuple[int, int]] = []
    for rx, kind in ((DOLLAR_RE, "dollar amount"), (PCT_RE, "percentage"), (THOUSANDS_RE, "amount")):
        for m in rx.finditer(line):
            if any(a < m.end() and m.start() < b for a, b in spans):
                continue  # already reported as a dollar amount
            spans.append(m.span())
            found.append((kind, m.group(0)))
    for m in DAYS_RE.finditer(line):
        business = (m.group(2) or "").lower() == "business"
        if business or int(m.group(1)) in day_values:
            found.append(("day count (use the figure key)", m.group(0)))
    return found


def is_allowed(rel: str, line: str, allow: list[dict]) -> bool:
    return any(
        fnmatch.fnmatch(rel, a["file"]) and re.search(a["pattern"], line, re.I) for a in allow
    )


def lint_file(path: Path, root: Path, codes: set[str], tools: set[str] | None, allow: list[dict],
              day_values: set[int] = frozenset(), banned: list | tuple = ()) -> list[str]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text()
    errs: list[str] = []
    fm, body = split_frontmatter(text)
    is_skill = path.name == "SKILL.md"
    if fm is None:
        if is_skill:  # reference files may omit frontmatter
            errs.append(f"{rel}: missing or invalid frontmatter")
    else:
        name, desc = fm.get("name"), fm.get("description")
        if not isinstance(name, str) or not name:
            errs.append(f"{rel}: frontmatter name missing")
        else:
            if not NAME_RE.match(name) or len(name) > 64:
                errs.append(f"{rel}: name '{name}' must be kebab-case, <=64 chars")
            if name != path.parent.name and is_skill:
                errs.append(f"{rel}: name '{name}' != folder '{path.parent.name}'")
            if not is_skill and name != path.parent.parent.name:
                errs.append(f"{rel}: name '{name}' != skill folder '{path.parent.parent.name}'")
        if not isinstance(desc, str) or not desc.strip():
            errs.append(f"{rel}: description missing or empty")
        elif len(desc) > 1024:
            errs.append(f"{rel}: description {len(desc)} chars > 1024")
    if is_skill and len(text.splitlines()) >= 500:
        errs.append(f"{rel}: SKILL.md has {len(text.splitlines())} lines (must be < 500)")
    for ln, line in prose_lines(text):
        line = URL_RE.sub("", line)  # URLs carry %-escapes and ids that are not figures
        for kind, found in figure_findings(line, day_values):
            if not is_allowed(rel, line, allow):
                errs.append(f"{rel}:{ln}: hard-coded {kind} '{found}'")
        for msg in banned_findings(line, list(banned)):
            errs.append(f"{rel}:{ln}: {msg}")
    for m in CODE_RE.finditer(text):
        if m.group(0) not in codes:
            line = text.count("\n", 0, m.start()) + 1
            errs.append(f"{rel}:{line}: unknown refusal code {m.group(0)}")
    if tools is not None:
        for rx in (TOOL_MCP_RE, TOOL_BARE_RE):
            for m in rx.finditer(text):
                if m.group(1) not in tools:
                    line = text.count("\n", 0, m.start()) + 1
                    errs.append(f"{rel}:{line}: unknown tool '{m.group(1)}'")
    return errs


def registry_tools() -> set[str] | None:
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from au_tax.registry import load_all

        return set(load_all()) | BUILTIN_TOOLS
    except Exception as e:  # pragma: no cover
        print(f"WARN: could not load registry ({e}); tool-name check skipped")
        return None


def lint_skills(root: Path, tools: set[str] | None = None) -> list[str]:
    from lint_refusals import catalogue_codes

    codes = catalogue_codes(root)
    allow = load_allowlist(root)
    day_values = day_count_values(root)
    banned = load_banned(root)
    errs: list[str] = []
    files = sorted((root / "skills").glob("*/SKILL.md")) + sorted((root / "skills").glob("*/references/*.md"))
    for f in files:
        errs += lint_file(f, root, codes, tools, allow, day_values, banned)
    return errs


def main() -> int:
    root = ROOT
    if "--root" in sys.argv:
        root = Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
    from lint_refusals import lint_refusals

    errs = lint_skills(root, registry_tools()) + lint_refusals(root)
    for e in errs:
        print(e)
    n = len(list((root / "skills").glob("*/SKILL.md")))
    print(f"lint_skills: {n} skills, {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
