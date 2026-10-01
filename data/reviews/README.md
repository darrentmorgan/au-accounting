# Skill review records

A skill is `reviewed` only when a registered professional has signed off on its current content. Otherwise it is `draft`.

One file per review: `data/reviews/<skill>/<YYYY-MM-DD>.yaml` (or `<skill>.yaml` for a single latest record).

```yaml
skill: individual-tax          # folder name under skills/
reviewer: Jane Citizen         # full name
registration_number: "12345678"  # registered tax agent (TPB) or other registration
registration_body: TPB         # optional
date: 2026-10-01               # review date, ISO
content_hash: sha256:<hex>     # from `uv run scripts/review_status.py --hash <skill>`
notes: optional free text
```

`content_hash` is a SHA-256 over every file in the skill folder (relative path plus bytes, sorted, ignoring `__pycache__` and dotfiles). Any edit to the skill changes the hash, so the review becomes stale and the skill reverts to `draft` until re-reviewed.

Status: `uv run scripts/review_status.py` prints `reviewed`, `stale` (record exists, hash differs) or `draft` (no record) per skill.
