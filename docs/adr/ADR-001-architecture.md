# ADR-001: Plugin architecture

Date: 2026-09-29. Status: accepted.

## Context
We need a holistic Australian tax and accounting skill package for client work. Third-party guides were reviewed for layout ideas only; their content is licence-restricted and unreviewed, with duplicated files and figures embedded in prose.

## Decision
- Single Claude Code plugin `au-accounting`; one skill per obligation or domain; shared router skill added in Phase 3.
- Figures only in `data/rates/<income-year>.yaml` with per-figure status and primary source.
- All arithmetic in a uv-managed Python package (`src/au_tax`) exposed as `au-tax` CLI with JSON in/out; skills call it via `${CLAUDE_PLUGIN_ROOT}`.
- Refusals and risk flags are data files, tested.
- Review status is derived from review records with content hashes.
- Quality measured with `claude plugin eval` (with-plugin vs baseline) plus pytest.

## Consequences
- Annual update is a data change plus eval re-run, not a prose rewrite.
- Skills require `uv` on the machine running Claude Code.
- Evals must grant Bash so skills can run the calculator.
