"""Freeze the bounded EOFY pack's executable, prose, data and scenario dependencies.

Run on a clean committed candidate: python scripts/eofy_manifest.py > /outside/repo/manifest.tsv
The signed workflow opinion must name the SHA-256 of those exact UTF-8 bytes.
This inventory does not grant review status or professional approval.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Every overlay is loaded for a selected year; every calculator is imported by the registry.
# Freeze all runtime/data, even though positive professional scope is much narrower.
SCOPES = (
    "src/au_tax", "skills", "data/rates", "data/refusals", "data/risk_flags", "data/holidays",
    "data/law_watch", "data/reviews", "data/lint_allowlist.yaml", "data/glossary_banned.yaml",
    ".claude-plugin", ".mcp.json", "hooks", "pyproject.toml", "uv.lock", "mise.toml",
    "scripts", "tests", "CONVENTIONS.md", "README.md", "docs/GLOSSARY.md",
    "docs/eofy-reviewer-pack.md", "docs/law-watch.md", "docs/RUNBOOK-JULY.md",
    "evals/individual-tax", "evals/integration/int-num-resident-rental-shares-2526",
    "evals/rental-property", "evals/cgt", "evals/super-contributions",
    "evals/payg-instalments-lodgment",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest() -> str:
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("freeze requires a clean committed candidate; commit all pack changes first")
    tracked = git("ls-files").splitlines()
    paths: set[str] = set()
    for scope in SCOPES:
        matches = [p for p in tracked if p == scope or p.startswith(scope + "/")]
        if not matches:
            raise ValueError(f"required manifest scope has no tracked files: {scope}")
        paths.update(matches)
    # Future pack-owned evidence/fixtures cannot silently fall outside the manifest.
    paths.update(p for p in tracked if p.startswith("docs/eofy-") or p.startswith("data/eofy/"))
    rows = ["# bounded-individual-eofy-manifest-v1", f"# candidate_commit\t{git('rev-parse', 'HEAD')}",
            f"# candidate_tree\t{git('rev-parse', 'HEAD^{tree}')}",
            "# positive_scope\t2025-26 bounded preparation; see docs/eofy-reviewer-pack.md",
            "# future_years\t2026-27 and 2027-28 planning/refusal only", "sha256\tpath"]
    rows.extend(f"{hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}\t{p}" for p in sorted(paths))
    return "\n".join(rows) + "\n"


def main() -> int:
    try:
        sys.stdout.write(manifest())
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
