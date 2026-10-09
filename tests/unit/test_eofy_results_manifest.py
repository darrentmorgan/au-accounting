"""Offline result-manifest tests: invented text evidence, no tax/model execution."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import eofy_results_manifest as manifest  # noqa: E402

CANDIDATE = "a" * 40


@pytest.fixture
def records(tmp_path):
    document = manifest.template(CANDIDATE)
    row = document["rows"][0]
    row.update(local_result="pass", evidence_tier="synthetic",
               run_at_utc="2026-10-09T00:00:00Z", versions={"synthetic-harness": "test-1"})
    for kind in manifest.EVIDENCE:
        path = f"demo-{kind}.txt"
        (tmp_path / path).write_text(f"Invented {kind} evidence. No financial computation.\n")
        row["evidence"][kind] = {"path": path, "sha256": None}
    return document


def test_template_explicit_not_run_and_future_years(tmp_path):
    document = manifest.inventory(manifest.template(CANDIDATE), tmp_path)
    assert len(document["rows"]) == 19
    assert {r["scenario_id"] for r in document["rows"]} == set(manifest.SCENARIOS)
    assert [r["year"] for r in document["rows"] if r["scenario_id"] == "E17"] == ["2026-27", "2027-28"]
    for row in document["rows"]:
        assert row["candidate_commit"] == CANDIDATE
        assert row["run_at_utc"] is None
        assert row["versions"] == {}
        assert all(ref is None for ref in row["evidence"].values())
        assert row["local_result"] == row["installed_model_result"] == row["professional_disposition"] == "not-run"


def test_freeze_is_stable_independent_of_input_order(tmp_path, records):
    original = copy.deepcopy(records)
    first = manifest.inventory(records, tmp_path)
    records["rows"].reverse()
    second = manifest.inventory(records, tmp_path)
    assert manifest.canonical(first) == manifest.canonical(second)
    assert manifest.sha256(manifest.canonical(first).encode()) == manifest.sha256(manifest.canonical(second).encode())
    assert original["rows"][0]["evidence"]["input"]["sha256"] is None
    assert manifest.inventory(first, tmp_path, verify=True) == first
    assert first["rows"][0]["installed_model_result"] == "not-run"
    assert first["rows"][0]["professional_disposition"] == "not-run"


@pytest.mark.parametrize("kind", manifest.EVIDENCE)
@pytest.mark.parametrize("action", ["modify", "delete"])
def test_changed_or_missing_evidence_rejected(tmp_path, records, kind, action):
    frozen = manifest.inventory(records, tmp_path)
    path = tmp_path / frozen["rows"][0]["evidence"][kind]["path"]
    if action == "modify":
        path.write_text("Different synthetic evidence")
        with pytest.raises(ValueError, match="modified evidence"):
            manifest.inventory(frozen, tmp_path, verify=True)
        with pytest.raises(ValueError, match="modified evidence"):
            manifest.inventory(frozen, tmp_path)
    else:
        path.unlink()
        with pytest.raises(FileNotFoundError):
            manifest.inventory(frozen, tmp_path, verify=True)


@pytest.mark.parametrize("field,value,message", [
    ("scenario_id", "E19", "unknown scenario"),
    ("year", "2026-27", "year outside"),
    ("candidate_commit", "b" * 40, "candidate differs"),
    ("run_at_utc", "2026-10-09T00:00:00+10:30", "run_at_utc"),
    ("run_at_utc", "2026-02-30T00:00:00Z", "day"),
    ("versions", {}, "software versions"),
    ("versions", {"harness": ""}, "nonempty version"),
    ("installed_model_result", "pass", "installed-model not-run"),
    ("professional_disposition", "approved", "professional not-run"),
    ("evidence_tier", "professional", "synthetic/local tier"),
    ("local_result", "unknown", "invalid local result"),
])
def test_invalid_or_inflated_results_rejected(tmp_path, records, field, value, message):
    records["rows"][0][field] = value
    with pytest.raises(ValueError, match=message):
        manifest.inventory(records, tmp_path)


def test_duplicate_unknown_and_omitted_rows(tmp_path):
    document = manifest.template(CANDIDATE)
    document["rows"].append(copy.deepcopy(document["rows"][0]))
    with pytest.raises(ValueError, match="duplicate scenario"):
        manifest.inventory(document, tmp_path)
    document["rows"].pop()
    document["rows"].pop()
    with pytest.raises(ValueError, match="missing required"):
        manifest.inventory(document, tmp_path)


def test_variants_preserve_not_run_coverage(tmp_path, records):
    row = copy.deepcopy(records["rows"][0])
    row["variant"] = "boundary-below"
    records["rows"].append(row)
    assert len(manifest.inventory(records, tmp_path)["rows"]) == 20


@pytest.mark.parametrize("field,value", [("signature", "invented"), ("reviewer_name", "invented")])
def test_no_identity_or_signature_fields(tmp_path, field, value):
    document = manifest.template(CANDIDATE)
    document[field] = value
    with pytest.raises(ValueError, match="no assurance/signature"):
        manifest.inventory(document, tmp_path)
    del document[field]
    document["rows"][0][field] = value
    with pytest.raises(ValueError, match="invalid result row"):
        manifest.inventory(document, tmp_path)


@pytest.mark.parametrize("field,value", [
    ("run_at_utc", "2026-10-09T00:00:00Z"), ("versions", {"harness": "test-1"}),
    ("evidence_tier", "synthetic"),
])
def test_unexecuted_cannot_claim_run_metadata(tmp_path, field, value):
    document = manifest.template(CANDIDATE)
    document["rows"][0][field] = value
    with pytest.raises(ValueError, match="not-run cannot claim"):
        manifest.inventory(document, tmp_path)


def test_run_requires_complete_evidence_and_saved_hashes(tmp_path, records):
    with pytest.raises(ValueError, match="missing frozen hash"):
        manifest.inventory(records, tmp_path, verify=True)
    records["rows"][0]["evidence"]["trace"] = None
    with pytest.raises(ValueError, match="all evidence files"):
        manifest.inventory(records, tmp_path)


@pytest.mark.parametrize("path", ["../outside.txt", "/absolute.txt", "./demo-input.txt"])
def test_noncanonical_and_escaping_paths(tmp_path, records, path):
    records["rows"][0]["evidence"]["input"]["path"] = path
    with pytest.raises(ValueError, match="canonical relative"):
        manifest.inventory(records, tmp_path)


def test_symlink_cannot_escape_root(tmp_path, records):
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("Synthetic outside evidence")
    (root / "link.txt").symlink_to(outside)
    document = manifest.template(CANDIDATE)
    document["rows"][0]["evidence"]["input"] = {"path": "link.txt", "sha256": None}
    with pytest.raises(ValueError, match="inside root"):
        manifest.inventory(document, root)


def test_cli_digest_verification_and_tampering(tmp_path, records, capsys):
    source = tmp_path / "records.json"
    source.write_text(json.dumps(records))
    assert manifest.main(["freeze", str(source), "--evidence-root", str(tmp_path)]) == 0
    raw = capsys.readouterr().out.encode()
    source.write_bytes(raw)
    digest = manifest.sha256(raw)
    args = ["verify", str(source), "--evidence-root", str(tmp_path), "--sha256", digest]
    assert manifest.main(args) == 0
    assert "file integrity only, no assurance" in capsys.readouterr().out
    source.write_bytes(raw + b" ")
    assert manifest.main(args) == 1
    assert "digest mismatch" in capsys.readouterr().err


def test_cli_template_and_invalid_json(tmp_path, capsys):
    assert manifest.main(["template", "--candidate", CANDIDATE]) == 0
    assert json.loads(capsys.readouterr().out) == manifest.template(CANDIDATE)
    source = tmp_path / "invalid.json"
    source.write_text('{"rows": [], "rows": []}')
    assert manifest.main(["freeze", str(source), "--evidence-root", str(tmp_path)]) == 1
    assert "duplicate JSON field" in capsys.readouterr().err
    assert manifest.main(["template", "--candidate", "HEAD"]) == 1
    assert "full Git SHA" in capsys.readouterr().err
