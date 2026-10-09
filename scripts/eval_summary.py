"""Summarise an eval result: per-case scores and failing grader evidence.

Usage: uv run scripts/eval_summary.py [result.json | result.json.gz]
Default: latest .eval-results/<stamp>/result.json (or result.json.gz).
Archived docs/eval-results inputs are historical, not a current evaluation.
"""

import argparse
import gzip
import json
import sys
import zlib
from pathlib import Path


def summary(path: Path, d: dict) -> str:
    """Render before printing so a malformed record cannot emit a partial summary."""
    a = d["aggregates"]
    lines = [
        f"{path} | cases {a['casesPassed']}/{a['casesTotal']} | score {a['overallScore']:.3f} | "
        f"delta {a.get('meanDelta')} | cost ${d.get('costUsd', 0):.2f}"
    ]
    if not isinstance(d["cases"], list):
        raise ValueError("'cases' must be a list")
    for c in d["cases"]:
        ag = c["aggregates"]
        mark = "PASS" if ag.get("passRate", 0) >= 1 else "FAIL"
        lines.append(f"  {mark} {c['name']:<50} with {ag['score']:.2f}  without {ag.get('scoreWithout', '-')}  delta {ag.get('delta', '-')}")
        if mark == "FAIL":
            runs = c["arms"]["with"]
            if not isinstance(runs, list):
                raise ValueError("'arms.with' must be a list")
            for r in runs:
                graders = r.get("graders", [])
                if not isinstance(graders, list):
                    raise ValueError("'graders' must be a list")
                for g in graders:
                    if g.get("scored") and not g.get("passed"):
                        lines.append(f"      x {g['name']}: {g.get('explanation', '')[:160]}")
                        lines.append(f"        evidence: {str(g.get('evidence', ''))[:300]!r}")
    parts = path.resolve().parts
    if ("docs", "eval-results") in zip(parts, parts[1:]):
        lines.insert(0, "Historical archived result; not a current evaluation.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args(argv)
    path = args.path
    if path is None:
        paths = sorted({*Path(".eval-results").glob("*/result.json"),
                        *Path(".eval-results").glob("*/result.json.gz")})
        if not paths:
            print("eval_summary: no local results in .eval-results/*/result.json[.gz]; "
                  "provide an explicit .json or .json.gz path", file=sys.stderr)
            return 1
        path = paths[-1]
    if not (path.name.endswith(".json") or path.name.endswith(".json.gz")):
        print(f"eval_summary: {path}: expected a .json or .json.gz file", file=sys.stderr)
        return 1
    try:
        opener = gzip.open if path.name.endswith(".json.gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, EOFError, zlib.error, UnicodeError, ValueError) as exc:
        print(f"eval_summary: {path}: cannot read eval result: {exc}", file=sys.stderr)
        return 1
    try:
        output = summary(path, d)
    except KeyError as exc:
        print(f"eval_summary: {path}: invalid eval result schema: missing field {exc}", file=sys.stderr)
        return 1
    except (TypeError, AttributeError, ValueError) as exc:
        print(f"eval_summary: {path}: invalid eval result schema: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
