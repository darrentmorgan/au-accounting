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

## Bounded workflow review

The status above hashes skill-folder prose only. It does not cover executable/data dependencies, validate a practitioner's registration or signed evidence, or express partial workflow/year assurance. A bounded EOFY opinion must instead name the candidate commit, scope/year, complete dependency-manifest digest and scenario/results digest described in `docs/eofy-reviewer-pack.md`; generate the dependency inventory with `scripts/eofy_manifest.py` on a clean committed candidate. Keep complete skill folders draft unless their entire scope was reviewed. Dependency or scope changes require workflow re-review even if the skill-folder status remains unchanged.
