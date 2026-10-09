"""Offline CLI coverage for plain and archived eval-result summaries."""

import gzip
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval_summary.py"


@pytest.fixture
def record():
    return {
        "aggregates": {"casesPassed": 1, "casesTotal": 2,
                       "overallScore": 0.75, "meanDelta": 0.25},
        "costUsd": 1.25,
        "cases": [
            {"name": "passing case", "aggregates": {"passRate": 1, "score": 1}},
            {"name": "failing case",
             "aggregates": {"passRate": 0.5, "score": 0.5,
                            "scoreWithout": 0.25, "delta": 0.25},
             "arms": {"with": [{"graders": [
                 {"name": "failed grader", "scored": True, "passed": False,
                  "explanation": "e" * 170, "evidence": "v" * 310},
                 {"name": "passed grader", "scored": True, "passed": True},
                 {"name": "unscored grader", "scored": False, "passed": False},
             ]}]}},
        ],
    }


def write_result(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(record).encode()
    path.write_bytes(gzip.compress(data) if path.name.endswith(".gz") else data)
    return path


def run(cwd, path=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *([] if path is None else [str(path)])],
        cwd=cwd, capture_output=True, text=True,
    )


def assert_error(result, message):
    assert result.returncode == 1
    assert result.stdout == ""
    assert message in result.stderr
    assert result.stderr.startswith("eval_summary:")
    assert "Traceback" not in result.stderr


def test_json_and_gzip_have_equivalent_scores_and_evidence(tmp_path, record):
    outputs = []
    for suffix in (".json", ".json.gz"):
        path = write_result(tmp_path / f"result{suffix}", record)
        result = run(tmp_path, path)
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        assert result.stdout.startswith(str(path))
        outputs.append(result.stdout.removeprefix(str(path)))
    assert outputs[0] == outputs[1]
    assert " | cases 1/2 | score 0.750 | delta 0.25 | cost $1.25\n" in outputs[0]
    assert f"  PASS {'passing case':<50} with 1.00  without -  delta -\n" in outputs[0]
    assert f"  FAIL {'failing case':<50} with 0.50  without 0.25  delta 0.25\n" in outputs[0]
    assert "      x failed grader: " + "e" * 160 + "\n" in outputs[0]
    assert "        evidence: '" + "v" * 300 + "'\n" in outputs[0]
    assert "passed grader" not in outputs[0]
    assert "unscored grader" not in outputs[0]


@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
def test_archive_is_labelled_historical(tmp_path, record, suffix):
    path = write_result(tmp_path / "docs/eval-results/v0.3" / f"old{suffix}", record)
    result = run(tmp_path, path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("Historical archived result; not a current evaluation.\n")


@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
def test_default_selects_latest_local_result(tmp_path, record, suffix):
    write_result(tmp_path / ".eval-results/20260101/result.json", record)
    latest = Path(f".eval-results/20261009/result{suffix}")
    write_result(tmp_path / latest, record)
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(str(latest))
    assert "Historical" not in result.stdout


@pytest.mark.parametrize("directory_exists", [False, True])
def test_no_local_results(tmp_path, directory_exists):
    if directory_exists:
        (tmp_path / ".eval-results").mkdir()
    assert_error(run(tmp_path), "no local results")


@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
@pytest.mark.parametrize("field_path", [
    ("aggregates",), ("aggregates", "casesPassed"), ("aggregates", "casesTotal"),
    ("aggregates", "overallScore"), ("cases",), ("cases", 1, "aggregates"),
    ("cases", 1, "name"), ("cases", 1, "aggregates", "score"),
    ("cases", 1, "arms"), ("cases", 1, "arms", "with"),
    ("cases", 1, "arms", "with", 0, "graders", 0, "name"),
])
def test_missing_fields_fail_without_partial_output(tmp_path, record, suffix, field_path):
    parent = record
    for key in field_path[:-1]:
        parent = parent[key]
    del parent[field_path[-1]]
    path = write_result(tmp_path / f"result{suffix}", record)
    assert_error(run(tmp_path, path), f"missing field '{field_path[-1]}'")


@pytest.mark.parametrize("bad_record", [None, [], {}, {"aggregates": None},
    {"aggregates": {"casesPassed": 0, "casesTotal": 1, "overallScore": "bad"}},
    {"aggregates": {"casesPassed": 0, "casesTotal": 1, "overallScore": 0}, "cases": {}},
])
def test_malformed_schema(tmp_path, bad_record):
    path = write_result(tmp_path / "result.json", bad_record)
    assert_error(run(tmp_path, path), "invalid eval result schema")


@pytest.mark.parametrize("payload", [b"not gzip", gzip.compress(b"{}")[:-4],
    gzip.compress(b"{}")[:-8] + b"\x00" * 8])
def test_corrupt_gzip(tmp_path, payload):
    path = tmp_path / "result.json.gz"
    path.write_bytes(payload)
    assert_error(run(tmp_path, path), "cannot read eval result")


@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
@pytest.mark.parametrize("payload", [b"{broken json", b"\xff"])
def test_invalid_json_or_encoding(tmp_path, suffix, payload):
    path = tmp_path / f"result{suffix}"
    path.write_bytes(gzip.compress(payload) if suffix.endswith(".gz") else payload)
    assert_error(run(tmp_path, path), "cannot read eval result")


def test_missing_explicit_file(tmp_path):
    assert_error(run(tmp_path, tmp_path / "missing.json.gz"), "cannot read eval result")


def test_unsupported_extension(tmp_path):
    assert_error(run(tmp_path, tmp_path / "result.txt"), "expected a .json or .json.gz file")
