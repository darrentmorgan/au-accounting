# au-accounting

Claude Code plugin: Australian tax and accounting skills for self-preparers and for tax and accounting practitioners preparing working papers.

- Rules are written from primary sources (legislation.gov.au, ato.gov.au, state revenue offices) with citations and as-at dates.
- Every number is produced by a tested Python script reading versioned rates files; the model never does tax arithmetic.
- Quality is measured with `claude plugin eval` against a no-plugin baseline.

> Not tax advice. The operator is not a registered tax or BAS agent (Tax Agent Services Act 2009): outputs are working papers only. Giving tax advice or BAS services to others for a fee requires a registered agent to provide or review them. Outputs are working papers for review by a registered tax or BAS agent before they are relied on, lodged or used with any client.

Version 0.3.0.

## Coverage

- **Income years:** rates files exist for 2025-26, 2026-27 and 2027-28 (`data/rates/`). 2027-28 is partial: only figures legislated or published are verified, and a figure not yet published is refused rather than estimated.
- **Narrower skills:** `state-taxes-sa` covers 2025-26 and 2026-27 only. `company-div7a`, `payg-instalments-lodgment`, `payroll-sg`, `rates-lookup`, `rental-property`, `sole-trader-business`, `super-contributions` and `trusts-partnerships` state 2025-26 and 2026-27 in their descriptions (`rental-property` also previews the 2027-28 loss quarantine), and `bookkeeping-year-end` takes 2025-26 or 2026-27. `individual-tax`, `short-stay-accommodation`, `au-indonesia-cross-border` and the router accept 2027-28 within the partial rates above. Each `SKILL.md` states its own years.
- **State taxes:** South Australia only (payroll tax, land tax, stamp duty). Other states are refused and escalated.
- **Treaty analysis:** Australia-Indonesia only. For any other country, the generic foreign income tax offset (`foreign_income_tax_offset`) applies, with no treaty analysis.
- **Indonesia cross-border (`au-indonesia-cross-border`)** is an optional vertical. Skip it if Indonesia is not relevant to you.

The [bounded individual EOFY reviewer pack](docs/eofy-reviewer-pack.md) defines the 2025–26 preparation contract, canonical prompt, exclusions and required scenarios. It is not professionally reviewed and does not grant whole-return or all-year assurance.

## Requirements

- `uv` on your PATH: the bundled `au-tax` MCP server (`.mcp.json`) starts with `uv run`.

## Install

The repo is its own marketplace (`.claude-plugin/marketplace.json`). To enable it for a project, check
this into that project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "au-accounting": { "source": { "source": "github", "repo": "darrentmorgan/au-accounting", "ref": "main" } }
  },
  "enabledPlugins": { "au-accounting@au-accounting": true }
}
```

Or from a terminal in that project: `claude plugin marketplace add darrentmorgan/au-accounting --scope project`,
then `claude plugin install au-accounting@au-accounting --scope project`.

## How it fits together

- Skills in `skills/<slug>/` define scope, judgement rules, refusals and the output contract.
- Calculators in `src/au_tax/calculators/` are exposed as typed tools by the stdio MCP server `au-tax`.
- Figures live in `data/rates/<year>.yaml` plus overlays in `data/rates/<year>.d/`; refusal codes in `data/refusals/*.yaml`; risk flags in `data/risk_flags/*.yaml`.
- SessionStart hook: `hooks/hooks.json` prints `hooks/session-context.json` at session start, telling the model to load the matching au-accounting skill before answering an Australian tax question and to use the au-tax tools for all figures. It only runs `cat`; no Bash grant or network is needed.
- Law-change watch: `uv run scripts/law_watch.py check` fingerprints the primary-source pages listed in `data/law_watch/pages.yaml` and reports which changed; some sites (ato.gov.au, RevenueSA) refuse scripted requests, so their pages are checked from saved copies. Not scheduled. See [docs/law-watch.md](docs/law-watch.md) and step 12 of [docs/RUNBOOK-JULY.md](docs/RUNBOOK-JULY.md).
- Checks: `scripts/check_all.sh` (pytest, rates validation, holidays validation, skill lint, refusal lint, risk-flag lint).

## Provenance

Contains information sourced from the Australian Taxation Office and legislation.gov.au, used under Creative Commons Attribution 4.0 (CC BY 4.0) where applicable. Not endorsed by the ATO.

No content is copied from any third-party or commercial guide. Third-party guides were reviewed for topic coverage and layout ideas only.
