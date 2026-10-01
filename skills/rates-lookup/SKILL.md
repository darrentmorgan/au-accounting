---
name: rates-lookup
description: Looks up a current Australian tax rate, threshold, cap, fee or due-date figure for a given income year (2025-26, 2026-27) from the plugin's verified rates files, with its status and primary source. Use when someone asks "what is the concessional cap", "Div 7A benchmark rate this year", "car cents per km 2026-27", "GST registration threshold", "SA payroll tax threshold", "penalty unit value", or any single Australian tax figure.
---

# Australian rates lookup

Answers single-figure questions from `data/rates/<income-year>.yaml`. Never answer a figure from memory.

## Procedure

1. Work out the income year. Australian income years run 1 July to 30 June and are written `2026-27`. If the user gives no year, use the income year containing today's date and say so. FBT figures belong to the FBT year ending 31 March; say which one.
2. Call the `list_figures` tool (au-tax MCP server) with the income year and find the matching key.
3. Call the `get_figure` tool with the income year and key.
4. If the tool returns refusal code `AU-GEN-001` (figure has a value but is not verified), tell the user, quote the refusal message, and offer a draft by calling `get_figure` again with `allow_draft: true`. A draft answer must say "unverified" next to the number.
5. If the tool returns refusal code `AU-GEN-003` (no published value for that year), quote the refusal message and stop: no draft is possible. Do not give a figure from memory or from another year as the answer.

## Output

1. Result: the figure with its unit and income year (FBT year for FBT figures).
2. Figures used: key, value, status, source URL (VERIFIED / SOURCE-CITED / SUSPECT) and the primary source URL from `figures_used`. Status line: "Status: VERIFIED" or, for a draft, "Status: <status> (unverified draft)".
3. Assumptions: the income year used if the user gave none; one line of context only if the figure has conditions (e.g. a threshold that phases in).
4. Risk flags: none for a single-figure lookup unless the user's question raises one.
5. Refusals: AU-GEN-001 or AU-GEN-003 code and message verbatim, if returned.
6. Review line: "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.
