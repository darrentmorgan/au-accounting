# Domain build brief (Phase 2)

Every domain agent follows this brief. `CONVENTIONS.md` is binding. The finished `individual-tax` slice is the reference implementation: copy its shape, not its content.

## Deliverables per domain `<slug>`
1. `src/au_tax/calculators/<domain>.py`: calculators registered with `@calculator`, typed pydantic inputs, docstrings that tell the model when to use each tool. Only where the domain has arithmetic.
2. `tests/unit/test_<domain>.py`: expected values from ATO calculators, ATO worked examples in rulings/guides, or hand computations written step by step in comments. Never from running our code.
3. `data/rates/<year>.d/<domain>.yaml`: any figures missing from the base files, each read on a primary page (VERIFIED) or marked SOURCE-CITED/SUSPECT honestly. No edits to the base files.
4. `data/refusals/<domain>.yaml`: your refusal codes, `AU-<DOMAIN>-NNN`, same schema as `au.yaml` (general codes AU-GEN-* live there; do not edit it).
5. `data/risk_flags/<domain>.yaml`: structured risk flags (`id`, `topic`, `description`, `citations`, `skills`), under a top-level `risk_flags:` list. Do not edit other domains' files.
6. `skills/<slug>/SKILL.md` plus `references/sources.md` (primary URLs) and optional `references/*.md` one level deep. Description written for triggering. Output contract per CONVENTIONS section 8. No figures in prose.
7. Checks: `scripts/check_all.sh` green in your worktree.

## Eval suite (written by a different agent)
`evals/<slug>/<case>/`: about 12 to 16 cases: numeric (regex), trap (year boundary, 2026 law changes), escalation, judgement (llm rubric), trigger. Expected values computed from primary sources with working shown.

## Gate
- pytest green, lints green.
- `scripts/run_evals.sh --case '<slug>/*'` with default two arms: with-plugin score at least 0.9 on numeric cases, 0.8 overall, positive mean delta.
- Iterate on the skill and calculator (never on the eval expectations, unless the eval author's expectation is shown wrong against a primary source, in which case document the correction in the case's grader body).

## Sources
Primary only: legislation.gov.au, ato.gov.au, treasury.gov.au, courts, asic.gov.au, revenuesa.sa.gov.au and other state revenue offices. Use `docs/research/verification-federal-2026-09.md` and the other primary verification notes in `docs/research/` as a map. Never read or copy third-party guide files.

## Lessons from the individual-tax slice (read before starting)
- Eval `--case` filters by case NAME, not path. Tag every case with your slug and run `scripts/run_evals.sh --tag <slug> -j 3`. Summarise with `uv run scripts/eval_summary.py`.
- Plain Claude already gets simple arithmetic right, so the plugin's value shows in traps, recent law, unpublished figures, combinations and escalations. Eval authors: weight towards those.
- Escalation cases fail when the skill never fires. The SKILL.md description must name the out-of-scope situations too ("also use for X: the skill decides scope and escalates").
- Unpublished figures: refuse (AU-GEN-001) or use a documented safe screen; never guess. Verified corrections to the base rates files are allowed if read on a primary page (say so in your report).
- Reference files do not need frontmatter. URLs are ignored by the figure lint.
- Iterate on the skill description and procedure first; the calculator second; never the eval expectations unless proven wrong against a primary source.
- SKILL.md frontmatter: quote the description (single quotes) if it contains ": ". Max 1024 chars; lint enforces both.
