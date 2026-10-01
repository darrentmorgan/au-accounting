"""Summarise a claude plugin eval result.json: per-case scores, failing grader evidence.
Usage: uv run scripts/eval_summary.py [.eval-results/<stamp>/result.json]  (default: latest)"""

import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(Path(".eval-results").glob("*/result.json"))[-1]
d = json.loads(path.read_text())
a = d["aggregates"]
print(f"{path} | cases {a['casesPassed']}/{a['casesTotal']} | score {a['overallScore']:.3f} | "
      f"delta {a.get('meanDelta')} | cost ${d.get('costUsd', 0):.2f}")
for c in d["cases"]:
    ag = c["aggregates"]
    mark = "PASS" if ag.get("passRate", 0) >= 1 else "FAIL"
    print(f"  {mark} {c['name']:<50} with {ag['score']:.2f}  without {ag.get('scoreWithout', '-')}  delta {ag.get('delta', '-')}")
    if mark == "FAIL":
        for r in c["arms"]["with"]:
            for g in r.get("graders", []):
                if g.get("scored") and not g.get("passed"):
                    print(f"      x {g['name']}: {g.get('explanation', '')[:160]}")
                    print(f"        evidence: {str(g.get('evidence', ''))[:300]!r}")
