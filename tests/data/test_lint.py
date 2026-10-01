import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lint_refusals as lr  # noqa: E402
import lint_skills as ls  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GOOD_REFUSALS = """refusals:
  - {code: AU-GEN-001, trigger: t, message: m, route: r}
"""


def make(tmp_path, skill="demo", body="Body.\n", desc="Does a thing.", name=None, refusals=GOOD_REFUSALS, allow=""):
    (tmp_path / "data" / "refusals").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "refusals" / "au.yaml").write_text(refusals)
    (tmp_path / "data" / "lint_allowlist.yaml").write_text(allow or "allow: []\n")
    d = tmp_path / "skills" / skill
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name or skill}\ndescription: {desc}\n---\n{body}")
    return d


def run(tmp_path, tools=None):
    return ls.lint_skills(tmp_path, tools if tools is not None else {"list_figures", "get_figure"})


def test_clean_skill_passes(tmp_path):
    make(tmp_path)
    assert run(tmp_path) == []


def test_name_must_match_folder_and_kebab(tmp_path):
    make(tmp_path, name="other")
    assert any("!= folder" in e for e in run(tmp_path))
    make(tmp_path, skill="Bad_Name")
    assert any("kebab-case" in e for e in run(tmp_path))


def test_description_rules(tmp_path):
    make(tmp_path, desc="''")
    assert any("description" in e for e in run(tmp_path))
    make(tmp_path, desc="x" * 1025)
    assert any("> 1024" in e for e in run(tmp_path))


def test_line_limit(tmp_path):
    make(tmp_path, body="line\n" * 500)
    assert any("must be < 500" in e for e in run(tmp_path))


def test_hardcoded_figures_flagged_outside_code_only(tmp_path):
    make(tmp_path, body="The cap is $30,000 and rate 32.5%.\n```\n$99 and 5%\n```\nAlso 12 per cent.\n")
    errs = run(tmp_path)
    assert len([e for e in errs if "hard-coded" in e]) == 3
    assert not any("$99" in e for e in errs)


def test_allowlist_suppresses(tmp_path):
    allow = "allow:\n  - {file: 'skills/*/*.md', pattern: '50% CGT discount', reason: statutory}\n"
    make(tmp_path, body="Apply the 50% CGT discount.\n", allow=allow)
    assert run(tmp_path) == []


def test_refusal_code_must_exist(tmp_path):
    make(tmp_path, body="Surface AU-GEN-001 and AU-TAX-999.\n")
    errs = run(tmp_path)
    assert any("AU-TAX-999" in e for e in errs)
    assert not any("AU-GEN-001" in e for e in errs)


def test_unknown_tool_flagged(tmp_path):
    make(tmp_path, body="Call the `nonexistent_calc` tool and `mcp__plugin_au-accounting_au-tax__bad_tool`, then `get_figure` tool.\n")
    errs = run(tmp_path)
    assert any("nonexistent_calc" in e for e in errs)
    assert any("bad_tool" in e for e in errs)
    assert not any("'get_figure'" in e for e in errs)


def test_reference_files_checked(tmp_path):
    d = make(tmp_path)
    (d / "references").mkdir()
    (d / "references" / "r.md").write_text("---\nname: demo\ndescription: ref\n---\nRate 10% here.\n")
    assert any("references/r.md" in e and "percentage" in e for e in run(tmp_path))


def test_refusal_catalogue_rules(tmp_path):
    bad = """refusals:
  - {code: AU-GEN-001, trigger: t, message: m, route: r}
  - {code: AU-GEN-001, trigger: t, message: m, route: r}
  - {code: AU-GEN-002, trigger: t, message: '', route: r}
"""
    make(tmp_path, refusals=bad)
    errs = lr.lint_refusals(tmp_path)
    assert any("duplicate" in e for e in errs)
    assert any("'message'" in e for e in errs)


def test_refusal_raised_in_src_must_exist(tmp_path):
    make(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text('raise Refusal("AU-GEN-001")\nraise Refusal("AU-ZZZ-404", "x")\n')
    errs = lr.lint_refusals(tmp_path)
    assert len(errs) == 1 and "AU-ZZZ-404" in errs[0]


def test_review_status_hash_and_states(tmp_path):
    rs = _load("review_status")
    d = make(tmp_path)
    assert rs.status(tmp_path, "demo")[0] == "draft"
    h = rs.content_hash(d)
    (tmp_path / "data" / "reviews").mkdir(parents=True)
    (tmp_path / "data" / "reviews" / "demo.yaml").write_text(
        f"skill: demo\nreviewer: A\nregistration_number: '1'\ndate: 2026-10-01\ncontent_hash: {h}\n"
    )
    assert rs.status(tmp_path, "demo")[0] == "reviewed"
    (d / "SKILL.md").write_text("changed")
    assert rs.status(tmp_path, "demo")[0] == "stale"


def test_thousands_separator_amounts_flagged(tmp_path):
    make(tmp_path, body="ATO example: interest 3,430 and closing 50,430.\nCap 1,500,000.50 here.\n"
                        "Also $30,000 once.\n```\nin code 12,345\n```\nSee https://x.gov.au/a?b=1,234\n")
    errs = [e for e in run(tmp_path) if "hard-coded" in e]
    texts = sorted(e.split("'")[1] for e in errs)
    assert texts == ["$30,000", "1,500,000.50", "3,430", "50,430"]  # $ amount reported once, code and URL skipped


def test_plain_numbers_not_flagged(tmp_path):
    make(tmp_path, body="Section 109E(6), 12 months, 2026-27, ITAA 1997 s 115-100, 1234 items.\n")
    assert run(tmp_path) == []


def _rates(tmp_path, figs):
    (tmp_path / "data" / "rates" / "2026-27.d").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "rates" / "2026-27.d" / "x.yaml").write_text(figs)


def test_business_day_counts_always_flagged(tmp_path):
    make(tmp_path, body="Received within 7 business days (20 business days for a new fund).\n")
    errs = run(tmp_path)
    assert any("'7 business days'" in e for e in errs) and any("'20 business days'" in e for e in errs)


def test_day_counts_matching_a_figure_flagged(tmp_path):
    _rates(tmp_path, "gst:\n  div87_long_term_days: {value: 28, unit: days, status: VERIFIED, source: s, as_at: 2026-07-01}\n"
                     "  due_day: {value: 21, unit: day_of_month, status: VERIFIED, source: s, as_at: 2026-07-01}\n")
    make(tmp_path, body="Stays of 28 continuous days or more.\nStays of 28 days.\nWithin 21 days.\nThe 183 days test.\n")
    errs = [e for e in run(tmp_path) if "day count" in e]
    assert len(errs) == 2 and all("28" in e for e in errs)  # 21 is a day-of-month figure, 183 no figure


def test_day_count_allowlist(tmp_path):
    _rates(tmp_path, "x:\n  d: {value: 14, unit: days, status: VERIFIED, source: s, as_at: 2026-07-01}\n")
    allow = "allow:\n  - {file: 'skills/*/*.md', pattern: 'within 14 days of detection', reason: statutory}\n"
    make(tmp_path, body="Correct errors within 14 days of detection.\n", allow=allow)
    assert run(tmp_path) == []
