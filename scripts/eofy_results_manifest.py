"""Offline EOFY result inventory. Records supplied local evidence, never runs scenarios.

No installed-model/professional results or signatures can be issued by this helper.
JSON paths are relative to --evidence-root; output is canonical UTF-8 with a final LF.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA = "bounded-individual-eofy-results-v1"
SCENARIOS = tuple(f"E{i:02}" for i in range(1, 19))
EVIDENCE = ("prompt", "input", "output", "trace", "expected_authority")
ROW_KEYS = {
    "scenario_id", "variant", "year", "candidate_commit", "run_at_utc", "versions",
    "evidence", "evidence_tier", "local_result", "installed_model_result",
    "professional_disposition", "comments",
}


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def template(candidate: str) -> dict:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", candidate)), "candidate_commit must be a full Git SHA")
    rows = []
    for scenario in SCENARIOS:
        years = ("2026-27", "2027-28") if scenario == "E17" else ("2025-26",)
        for year in years:
            rows.append({
                "scenario_id": scenario, "variant": "base", "year": year,
                "candidate_commit": candidate, "run_at_utc": None, "versions": {},
                "evidence": dict.fromkeys(EVIDENCE), "evidence_tier": "not-run",
                "local_result": "not-run", "installed_model_result": "not-run",
                "professional_disposition": "not-run", "comments": "",
            })
    return {"schema": SCHEMA, "candidate_commit": candidate, "rows": rows}


def inventory(document: dict, root: Path, *, verify: bool = False) -> dict:
    """Validate records; freeze fills absent hashes, verify requires exact saved hashes."""
    document = copy.deepcopy(document)
    require(isinstance(document, dict) and set(document) == {"schema", "candidate_commit", "rows"},
            "expected schema, candidate_commit and rows only (no assurance/signature fields)")
    require(document["schema"] == SCHEMA, "unknown schema")
    candidate = document["candidate_commit"]
    require(isinstance(candidate, str) and bool(re.fullmatch(r"[0-9a-f]{40}", candidate)),
            "candidate_commit must be a full Git SHA")
    rows = document["rows"]
    require(isinstance(rows, list), "rows must be a list")
    root = root.resolve(strict=True)
    require(root.is_dir(), "evidence root must be a directory")
    seen = set()
    coverage = set()
    for row in rows:
        require(isinstance(row, dict) and set(row) == ROW_KEYS, "invalid result row fields")
        scenario, year, variant = row["scenario_id"], row["year"], row["variant"]
        require(isinstance(scenario, str) and scenario in SCENARIOS, "unknown scenario ID")
        years = ("2026-27", "2027-28") if scenario == "E17" else ("2025-26",)
        require(isinstance(year, str) and year in years, f"{scenario}: year outside scenario scope")
        require(isinstance(variant, str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]*", variant)),
                "variant must be a nonempty lowercase slug")
        key = (scenario, year, variant)
        require(key not in seen, f"duplicate scenario ID/year/variant: {key}")
        seen.add(key)
        coverage.add((scenario, year))
        require(row["candidate_commit"] == candidate, "row candidate differs from manifest candidate")
        require(row["installed_model_result"] == "not-run", "offline helper requires installed-model not-run")
        require(row["professional_disposition"] == "not-run", "offline helper requires professional not-run")
        require(isinstance(row["comments"], str), "comments must be text")
        require(row["local_result"] in ("not-run", "pass", "fail"), "invalid local result")
        require(isinstance(row["versions"], dict) and all(
            isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
            for k, v in row["versions"].items()), "versions must map names to nonempty version strings")
        evidence = row["evidence"]
        require(isinstance(evidence, dict) and set(evidence) == set(EVIDENCE), "invalid evidence fields")
        if row["local_result"] == "not-run":
            require(row["evidence_tier"] == "not-run" and row["run_at_utc"] is None
                    and row["versions"] == {}, "not-run cannot claim a run time, versions or result tier")
            require(evidence["output"] is None and evidence["trace"] is None,
                    "not-run cannot claim output or trace evidence")
        else:
            require(row["evidence_tier"] in ("synthetic", "local"), "local result needs synthetic/local tier")
            stamp = row["run_at_utc"]
            require(isinstance(stamp, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp)),
                    "run_at_utc must be YYYY-MM-DDTHH:MM:SSZ")
            datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            require(bool(row["versions"]), "local run requires supplied software versions")
            require(all(evidence[k] is not None for k in EVIDENCE), "local run requires all evidence files")
        for kind, ref in evidence.items():
            if ref is None:
                continue
            require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, f"{kind}: expected path and sha256")
            path = ref["path"]
            require(isinstance(path, str) and bool(path), f"{kind}: empty evidence path")
            relative = Path(path)
            require(not relative.is_absolute() and ".." not in relative.parts
                    and relative.as_posix() == path, f"{kind}: use a canonical relative evidence path")
            file = (root / relative).resolve(strict=True)
            require(file.is_relative_to(root) and file.is_file(), f"{kind}: evidence must be a file inside root")
            actual = sha256(file.read_bytes())
            saved = ref["sha256"]
            require(saved is None or (isinstance(saved, str) and bool(re.fullmatch(r"[0-9a-f]{64}", saved))),
                    f"{kind}: invalid SHA-256")
            require(not verify or saved is not None, f"{kind}: missing frozen hash")
            require(saved is None or saved == actual, f"{kind}: modified evidence: {path}")
            ref["sha256"] = actual
    expected = {(s, y) for s in SCENARIOS for y in (
        ("2026-27", "2027-28") if s == "E17" else ("2025-26",))}
    require(coverage == expected, "missing required scenario/year rows; retain explicit not-run entries")
    document["rows"] = sorted(rows, key=lambda row: (row["scenario_id"], row["year"], row["variant"]))
    return document


def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field: {key}")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("template", help="emit all required not-run rows")
    init.add_argument("--candidate", required=True, help="full committed candidate SHA (not inferred)")
    for command in ("freeze", "verify"):
        sub = commands.add_parser(command)
        sub.add_argument("records", type=Path)
        sub.add_argument("--evidence-root", type=Path, required=True)
        if command == "verify":
            sub.add_argument("--sha256", required=True, help="externally retained manifest digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            sys.stdout.write(canonical(template(args.candidate)))
        else:
            raw = args.records.read_bytes()
            if args.command == "verify":
                require(sha256(raw) == args.sha256, "results manifest digest mismatch")
            document = json.loads(raw, object_pairs_hook=unique_object)
            result = inventory(document, args.evidence_root, verify=args.command == "verify")
            if args.command == "freeze":
                sys.stdout.write(canonical(result))
            else:
                require(raw == canonical(result).encode("utf-8"), "manifest is not canonical")
                print(f"verified results manifest {args.sha256}; file integrity only, no assurance")
    except (ValueError, OSError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
