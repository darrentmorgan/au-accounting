"""Tests for scripts/lint_risk_flags.py.

The rules come from CONVENTIONS section 7 (risk flags carry id, topic, description, citations,
skills) and from the requirement that catalogue YAML must actually parse, ids are unique across
files, `skills` name real skill folders, and ids that skills or calculators cite exist.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_risk_flags  # noqa: E402

FLAG = """
risk_flags:
  - id: DEMO-RF-001
    topic: Demo topic
    description: Demo description.
    citations: ["ITAA 1997 s 8-1"]
    skills: [demo]
"""


def make_root(tmp_path: Path, flags: str = FLAG, refusals: str = "refusals: []\n",
              skill_md: str = "Plain prose.\n", py: str = "") -> Path:
    for d in ("data/risk_flags", "data/refusals", "skills/demo", "src/au_tax/calculators"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/risk_flags/demo.yaml").write_text(flags)
    (tmp_path / "data/refusals/demo.yaml").write_text(refusals)
    (tmp_path / "skills/demo/SKILL.md").write_text("---\nname: demo\ndescription: d\n---\n" + skill_md)
    (tmp_path / "src/au_tax/calculators/demo.py").write_text(py)
    return tmp_path


def errs(root: Path) -> list[str]:
    return lint_risk_flags.lint(root)


def test_clean_fixture_passes(tmp_path):
    assert errs(make_root(tmp_path)) == []


def test_real_repo_is_clean():
    assert lint_risk_flags.lint(ROOT) == []


def test_invalid_yaml_reported_not_raised(tmp_path):
    bad = 'risk_flags:\n  - id: DEMO-RF-001\n    topic: a\n    description: x: y\n    citations: ["a"]\n    skills: [demo]\n'
    out = errs(make_root(tmp_path, flags=bad))
    assert any("demo.yaml" in e and "not valid YAML" in e for e in out)


def test_unquoted_nested_flow_list_is_invalid(tmp_path):
    bad = FLAG.replace('["ITAA 1997 s 8-1"]', '["ITAA 1997 s 8-1" [2010] x]')
    assert any("not valid YAML" in e for e in errs(make_root(tmp_path, flags=bad)))


def test_invalid_refusals_yaml_reported(tmp_path):
    out = errs(make_root(tmp_path, refusals="refusals:\n  - code: AU-X-001\n    message: a: b\n"))
    assert any("refusals" in e and "not valid YAML" in e for e in out)


def test_missing_top_level_key(tmp_path):
    out = errs(make_root(tmp_path, flags="flags: []\n"))
    assert any("top-level 'risk_flags'" in e for e in out)


def test_missing_field(tmp_path):
    for field in ("topic", "description", "citations", "skills"):
        lines = [ln for ln in FLAG.splitlines() if not ln.strip().startswith(field + ":")]
        out = errs(make_root(tmp_path, flags="\n".join(lines) + "\n"))
        assert any(f"'{field}'" in e and "DEMO-RF-001" in e for e in out), field


def test_missing_id(tmp_path):
    flags = FLAG.replace("id: DEMO-RF-001", "idx: DEMO-RF-001")
    assert any("'id'" in e for e in errs(make_root(tmp_path, flags=flags)))


def test_empty_citations_and_wrong_types(tmp_path):
    assert any("'citations'" in e for e in errs(make_root(tmp_path, flags=FLAG.replace('["ITAA 1997 s 8-1"]', "[]"))))
    assert any("'skills'" in e for e in errs(make_root(tmp_path, flags=FLAG.replace("[demo]", "demo"))))


def test_duplicate_id_across_files(tmp_path):
    root = make_root(tmp_path)
    (root / "data/risk_flags/other.yaml").write_text(FLAG)
    assert any("duplicate risk flag id DEMO-RF-001" in e for e in errs(root))


def test_unknown_skill_reference(tmp_path):
    out = errs(make_root(tmp_path, flags=FLAG.replace("[demo]", "[demo, ghost]")))
    assert any("unknown skill 'ghost'" in e for e in out)


def test_skill_cites_missing_uppercase_id(tmp_path):
    out = errs(make_root(tmp_path, skill_md="See DEMO-RF-001 and DEMO-RF-002.\n"))
    assert any("DEMO-RF-002" in e for e in out)
    assert not any("DEMO-RF-001" in e for e in out)


def test_skill_cites_missing_kebab_id_in_backticks(tmp_path):
    flags = FLAG.replace("DEMO-RF-001", "demo-kebab-flag")
    ok = errs(make_root(tmp_path, flags=flags, skill_md="Flag `demo-kebab-flag` applies.\n"))
    assert ok == []
    out = errs(make_root(tmp_path, flags=flags, skill_md="Flag `demo-kebab-missing` applies.\n"))
    assert any("demo-kebab-missing" in e for e in out)


def test_prose_and_refusal_codes_not_flagged(tmp_path):
    md = "Refusal AU-DEMO-001 stops work. Skill `demo` and file `data/risk_flags/demo.yaml`; ITAA 1997 s 8-1; GST-free.\n"
    assert errs(make_root(tmp_path, skill_md=md)) == []


def test_references_folder_scanned(tmp_path):
    root = make_root(tmp_path)
    (root / "skills/demo/references").mkdir()
    (root / "skills/demo/references/a.md").write_text("Cites DEMO-RF-999.\n")
    assert any("DEMO-RF-999" in e and "references/a.md" in e for e in errs(root))


def test_calculator_emitting_unknown_flag(tmp_path):
    py = (
        "def f():\n"
        "    flags = []\n"
        "    flags.append('DEMO-RF-001')\n"
        "    flags.append('demo-missing')\n"
        "    return {'risk_flag_ids': sorted(set(flags)), 'x': ['DEMO-RF-404']}\n"
        "def g():\n"
        "    return {'risk_flags': ['DEMO-RF-001', 'demo-other-missing'] if True else []}\n"
    )
    out = errs(make_root(tmp_path, py=py))
    assert any("demo-missing" in e for e in out)
    assert any("demo-other-missing" in e for e in out)
    assert not any("DEMO-RF-404" in e for e in out)  # only flag-named keys and appends count
    assert not any("'DEMO-RF-001'" in e for e in out)
