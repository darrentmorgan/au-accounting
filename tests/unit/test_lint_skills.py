"""Tests for the banned-synonym rule in scripts/lint_skills.py and its link to docs/GLOSSARY.md.

Expected results come from the rule as written in data/glossary_banned.yaml (whole words, case
insensitive, optional plural, skipped inside code fences, inline code and URLs), not from running
the linter to see what it does.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_skills  # noqa: E402

BANNED_YAML = ROOT / "data" / "glossary_banned.yaml"
GLOSSARY = ROOT / "docs" / "GLOSSARY.md"


def make_root(tmp_path: Path, skill_body: str, banned: str | None = None) -> Path:
    """A minimal repo root with one skill and (optionally) a banned list."""
    skill = tmp_path / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill for lint tests.\n---\n" + skill_body
    )
    (tmp_path / "data" / "refusals").mkdir(parents=True)
    (tmp_path / "data" / "refusals" / "au.yaml").write_text("refusals: []\n")
    if banned is not None:
        (tmp_path / "data" / "glossary_banned.yaml").write_text(banned)
    return tmp_path


BANNED = """
banned:
  - preferred: income year
    synonyms: [tax year, fiscal year]
  - preferred: working paper
    synonyms: [workpaper, working-paper]
"""


def banned_errors(root: Path) -> list[str]:
    return [e for e in lint_skills.lint_skills(root, tools=None) if "banned term" in e]


def test_flags_banned_synonym_with_preferred_term(tmp_path):
    root = make_root(tmp_path, "Use the tax year of the sale.\n", BANNED)
    errs = banned_errors(root)
    assert len(errs) == 1
    assert "skills/demo/SKILL.md:5" in errs[0]
    assert "'tax year'" in errs[0]
    assert "use 'income year'" in errs[0]


def test_case_insensitive_plural_and_hyphen_variant(tmp_path):
    root = make_root(tmp_path, "Two Tax Years apply.\nProduce a working-paper.\n", BANNED)
    errs = banned_errors(root)
    assert len(errs) == 2
    assert "use 'income year'" in errs[0]
    assert "use 'working paper'" in errs[1]


def test_preferred_term_is_not_flagged(tmp_path):
    root = make_root(tmp_path, "State the income year. Write a working paper.\n", BANNED)
    assert banned_errors(root) == []


def test_ignored_in_code_fence_inline_code_and_url(tmp_path):
    body = (
        "```\ntax year = 2026\n```\n"
        "Field `tax year` is not prose.\n"
        "See https://example.gov.au/tax year/fiscal-year for detail.\n"
    )
    root = make_root(tmp_path, body, BANNED)
    assert banned_errors(root) == []


def test_whole_words_only(tmp_path):
    root = make_root(tmp_path, "The networkpaper and the fiscal-yearbook are unrelated.\n", BANNED)
    assert banned_errors(root) == []


def test_flags_in_frontmatter_description(tmp_path):
    root = make_root(tmp_path, "Body is clean.\n", BANNED)
    skill = root / "skills" / "demo" / "SKILL.md"
    skill.write_text(skill.read_text().replace("Demo skill", "Demo fiscal year skill"))
    errs = banned_errors(root)
    assert len(errs) == 1
    assert "SKILL.md:3" in errs[0]


def test_no_banned_file_means_no_banned_findings(tmp_path):
    root = make_root(tmp_path, "Use the tax year.\n", banned=None)
    assert lint_skills.load_banned(root) == []
    assert banned_errors(root) == []


def test_real_skills_are_clean():
    assert banned_errors(ROOT) == []


def test_real_banned_list_is_short_and_well_formed():
    data = yaml.safe_load(BANNED_YAML.read_text())["banned"]
    assert 1 <= len(data) <= 10
    for entry in data:
        assert entry["preferred"] and entry["synonyms"]
        # A preferred term must never be caught by the list itself.
        for rx, _syn, _pref in lint_skills.load_banned(ROOT):
            assert not rx.search(entry["preferred"])


def test_glossary_defines_every_preferred_term_and_lists_every_synonym():
    text = GLOSSARY.read_text()
    bold_terms = {t.lower() for t in re.findall(r"^- \*\*(.+?)\*\*", text, re.M)}
    for entry in yaml.safe_load(BANNED_YAML.read_text())["banned"]:
        assert entry["preferred"].lower() in bold_terms, entry["preferred"]
        for syn in entry["synonyms"]:
            assert syn in text, f"{syn} not listed in docs/GLOSSARY.md"
            # The synonym is listed against its preferred term ("Not: ...") in that entry.
            entry_line = next(
                line for line in text.splitlines()
                if line.startswith(f"- **{entry['preferred']}**")
            )
            assert syn in entry_line, f"{syn} not under {entry['preferred']}"


def test_glossary_terms_are_defined_once():
    text = GLOSSARY.read_text()
    terms = [t.lower() for line in re.findall(r"^- (\*\*.+?\*\*(?:, \*\*.+?\*\*)*)\.", text, re.M)
             for t in re.findall(r"\*\*(.+?)\*\*", line)]
    assert len(terms) > 50
    dupes = {t for t in terms if terms.count(t) > 1}
    assert not dupes, dupes


def test_glossary_has_no_dollar_amounts_or_percentages():
    text = GLOSSARY.read_text()
    assert not lint_skills.DOLLAR_RE.search(text)
    assert not lint_skills.PCT_RE.search(text)
    assert "—" not in text
