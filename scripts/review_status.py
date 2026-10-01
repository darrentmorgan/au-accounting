# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Report reviewed vs draft per skill. Run: uv run scripts/review_status.py [--hash SKILL]"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def content_hash(folder: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder)
        if "__pycache__" in rel.parts or any(part.startswith(".") for part in rel.parts):
            continue
        h.update(rel.as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return "sha256:" + h.hexdigest()


def records(root: Path, skill: str) -> list[dict]:
    out = []
    d = root / "data" / "reviews"
    for p in list(d.glob(f"{skill}.yaml")) + list((d / skill).glob("*.yaml")):
        doc = yaml.safe_load(p.read_text())
        if isinstance(doc, dict) and doc.get("skill") == skill:
            out.append(doc)
    return sorted(out, key=lambda r: str(r.get("date")))


def status(root: Path, skill: str) -> tuple[str, dict | None]:
    recs = records(root, skill)
    if not recs:
        return "draft", None
    cur = content_hash(root / "skills" / skill)
    for r in reversed(recs):
        if r.get("content_hash") == cur:
            return "reviewed", r
    return "stale", recs[-1]


def main() -> int:
    if "--hash" in sys.argv:
        print(content_hash(ROOT / "skills" / sys.argv[sys.argv.index("--hash") + 1]))
        return 0
    counts: dict[str, int] = {}
    for d in sorted((ROOT / "skills").iterdir()):
        if not (d / "SKILL.md").exists():
            continue
        st, r = status(ROOT, d.name)
        counts[st] = counts.get(st, 0) + 1
        who = f" by {r['reviewer']} ({r['registration_number']}) {r['date']}" if r else ""
        print(f"{st:9} {d.name}{who}")
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
