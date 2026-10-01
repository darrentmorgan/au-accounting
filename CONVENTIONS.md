# Conventions

Rules every contributor (human or agent) follows. Where this file and a skill disagree, this file wins. Background: `docs/research/skill-authoring-and-evals.md`, ADR-001.

## 1. Sources and provenance

- Primary sources only: legislation.gov.au, ato.gov.au (incl. the legal database), treasury.gov.au, courts (hcourt.gov.au, fedcourt, AustLII), asic.gov.au, state revenue offices, fwc.gov.au.
- Secondary sources (firms, blogs, news) may be used to find a primary page, never as the citation.
- Never copy text, tables or worked examples from any third-party or commercial guide. Write from the primary source in our own words.
- Citation format in prose: `ITAA 1997 s 115-100`, `GSTA 1999 s 38-190`, `TR 2026/1`, `PCG 2026/3`, with a URL in the skill's `references/sources.md`.

## 2. Figures

- Every rate, threshold, cap, fee and date that changes over time lives ONLY in `data/rates/<income-year>.yaml`. Keys look like `individual.resident_brackets`, `super.concessional_cap`.
- Each figure carries `value`, `unit`, `status`, `source`, `as_at`, optional `notes`.
- Status: `VERIFIED` (read on a primary page), `SOURCE-CITED` (cited but not re-read), `SUSPECT` (conflict, stale, or not found). `value: null` is allowed only with `SUSPECT`. From 2026-27 a null figure also carries `checked_at` (the date its `source` URL was checked and found not to publish the figure); the validator requires it. Figures not yet published for a year (for example the next July's indexed amounts) stay null; nothing is indexed forward or estimated.
- Skill prose refers to figures by key or by name ("the concessional cap"), never by amount. A lint (`scripts/lint_skills.py`) rejects, outside code fences and URLs, dollar amounts, percentages, amounts with a thousands separator (`3,430`), business-day counts, and day counts equal to a day-count figure in the rates files. Statutory constants are allowlisted with a reason in `data/lint_allowlist.yaml` (for example the 50% CGT discount).
- Public holidays are a separate data class in `data/holidays/au.yaml` (per-date rows with jurisdiction, status and source; validated by `scripts/validate_holidays.py`). Due-date calculators read them through the shared loader, never from a hard-coded list. Rule and jurisdiction regimes: `docs/research/due-dates-public-holidays.md`.
- Law-change watch: `scripts/law_watch.py` fingerprints the primary-source pages in `data/law_watch/pages.yaml` and reports changes (`docs/law-watch.md`; run in step 12 of `docs/RUNBOOK-JULY.md`). It only alerts: a figure still enters `data/rates/` by the verification rules in this section, and a page added to the watch list needs a `why` naming the figure keys or skills that depend on it. Scheduling it needs the project owner's approval.
- One fact, one key: never add a figure that duplicates an existing key in the base file or an overlay.
- Calculators refuse to use a non-`VERIFIED` figure unless called with `--allow-draft`, and then mark the output `draft: true` and list the figure keys.

## 3. Income years

- Income year label: `YYYY-YY` (e.g. `2026-27` = 1 Jul 2026 to 30 Jun 2027). FBT year label: `FBT2027` (1 Apr 2026 to 31 Mar 2027).
- Every skill output states the income year it applied. If the user's year is ambiguous, the skill asks; it never assumes the current year silently.
- Law changes with a start date (e.g. CGT indexation from 1 Jul 2027) are modelled as date-effective rules in the calculator, not as prose caveats.

## 4. Skills

- One skill per obligation or domain. One slug, one folder, no numbered twins, no generated copies.
- Layout: `skills/<slug>/SKILL.md`, optional `references/*.md` (one level deep), optional `scripts/` only for skill-specific wrappers. Shared logic lives in `src/au_tax/`.
- Frontmatter: `name` (kebab-case, max 64 chars), `description` (third person, says what it does AND when to use it, with the phrases a user would actually say; max 1024 chars), `allowed-tools` when needed.
- SKILL.md body under 500 lines. Order: scope and out-of-scope, required inputs, procedure (numbered, with the exact script command), judgement rules with citations, escalation triggers, output format.
- Consistent terms across all skills (use the glossary in `docs/GLOSSARY.md`). `scripts/lint_skills.py` rejects the banned synonyms listed in `data/glossary_banned.yaml`, outside code fences, inline code and URLs, and names the preferred term. To add a term to the glossary or a synonym to the list, edit both files together.
- Skills never compute by hand. If the au-tax tools are unavailable, the skill says so, quotes AU-GEN-001 and stops; it never reads figures from the rates files to do the arithmetic itself.
- SessionStart hook: `hooks/hooks.json` runs `cat` on `hooks/session-context.json` at session start, which injects a short instruction to load the matching au-accounting skill before answering any Australian tax question and to use the au-tax tools for figures. It needs no Bash grant and no network. Keep it one short paragraph; edit `session-context.json`, not the hook command.
- No time-sensitive prose ("from next year"); use dated statements ("from 1 Jul 2027").

## 5. Calculators

- Python package `src/au_tax/` (uv). One module per domain in `src/au_tax/calculators/<domain>.py`.
- Register with `@calculator("<tool_name>", InputModel)` from `au_tax.registry`; the function signature is `fn(figures: Figures, inputs: InputModel) -> dict`; its docstring is the tool description the model sees (say what it computes, inputs, and when to use it). Modules are auto-discovered; never edit a shared registry.
- Figures only via `figures.get("<domain>.<key>")`. Domain-specific figures go in overlay files `data/rates/<year>.d/<domain>.yaml` (same schema, no `meta`, no key collisions with the base file).
- Refuse with `raise Refusal("<code>", "<detail>")`; the code must exist in `data/refusals/*.yaml` (add it there first: general `AU-GEN-*` codes in `au.yaml`, domain codes in `<domain>.yaml`).
- Skills reach calculators through the bundled MCP server `au-tax` (tools appear to the model as `mcp__plugin_au-accounting_au-tax__<tool_name>`). Skills name tools by `<tool_name>`; they never shell out.
- The `au-tax <tool_name> --year 2026-27 --json '<input>'` CLI exists for humans and tests.
- Envelope returned (CLI and MCP alike): `exit_code`, `income_year`, result fields, `figures_used` (key, value, status, source), `draft`, plus `refusal` when refused. Calculators should also return `assumptions` and `warnings` lists.
- Input models reject unknown keys (`extra="forbid"`, applied to every input model and nested model by `@calculator`), so a misspelt field is exit code 2, never silently ignored.
- Figure refusals: `AU-GEN-001` when a figure has a value but is not VERIFIED (a draft with `allow_draft` is possible); `AU-GEN-003` when the figure has no published value (no rates file, key absent or null), so no draft is possible.
- Exit codes: 0 ok, 2 invalid input, 3 refused, 4 missing or unverified figure without `allow_draft`.
- Every calculator has pytest tests in `tests/unit/test_<domain>.py` with expected values from an ATO calculator, ATO worked example, or a hand computation shown step by step in the test. Never generate expected values by running our own code.
- Evals: `scripts/run_evals.sh --case '<slug>/*'`. Cases live in `evals/<slug>/<case>/` (prompt.md + graders/*.md). MCP tool grader name: `mcp__plugin_au-accounting_au-tax__<tool_name>`.

## 6. Refusals and escalation

- Refusal codes live in `data/refusals/*.yaml`: `au.yaml` holds the general `AU-GEN-*` codes (and `AU-IND-*`); each domain has its own `<domain>.yaml`. The loader reads every file. Fields: `code`, `trigger` (plain description), `message` (fixed text shown to the user), `route` (who should handle it: registered tax agent, BAS agent, lawyer, actuary). Codes are unique across all files (`scripts/lint_refusals.py`).
- Skills must surface the code and message verbatim when a trigger fires, then stop the affected part of the work.
- Never invent a refusal code; add it to the data file first.

## 7. Risk flags

- Risk flags live in `data/risk_flags/*.yaml` (`au.yaml` general, `<domain>.yaml` per domain): structured audit risk points (`id`, `topic`, `description`, `citations`, `skills`). Skills list relevant flags in their output. Replaces free-text "AUDIT FLASH POINT" markers.

## 8. Output contract

Every skill that produces a working paper ends with:
1. Result (figures, with income year).
2. Figures used (key, value, status, primary source URL from `figures_used`).
3. Assumptions made.
4. Risk flags triggered.
5. Refusals or escalations.
6. Review line: "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use."

## 9. Review status

- `data/reviews/<slug>.yaml` records reviewer, registration number, date and a content hash of the skill folder. Status "reviewed" is derived by CI from the hash; any edit reverts the skill to draft. Nothing is labelled reviewed without a record.

## 10. Evals

- `claude plugin eval` suites under `evals/<slug>/<case>/`.
- Case types per skill: numeric (regex grader on the figure), judgement (llm grader with a PASS/FAIL rubric), trap (year boundary, recent law change), refusal (verbatim code expected), trigger (skill fires on natural phrasing; `tool_used: Skill`).
- Eval cases are written by a different agent from the skill author, from primary sources, without reading the skill.
- Eval runs: LLM graders use Sonnet (`scripts/run_evals.sh` sets `--judge-model`, override with `EVAL_JUDGE_MODEL`). Iterate with `--ablation none --runs 1` on the affected cases only; after a fix, rerun those cases and the suites whose skills or calculators changed. Run the full two-arm sweep once, at the final gate.
- Gate to merge a skill: unit tests green; with-plugin score at least 0.9 on numeric cases and 0.8 overall; positive mean delta over baseline.

## 11. Git

- Work on branches; `main` only via merge. Parallel domain work uses worktrees under `.claude/worktrees/`.
- No secrets, no client data in the repo. Client fixtures are synthetic.
