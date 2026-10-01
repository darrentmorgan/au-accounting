---
type: tool_used
tool: mcp__plugin_au-accounting_au-tax__crypto_parcel_ledger
min: 1
arm: with-only
---

A calculator must be used for the figure (skills must not do tax arithmetic in prose). The crypto parcel ledger computes each disposal through the cgt capital_gain function inside the au-tax server.

<!-- Orchestrator 2026-09-30 (crypto iteration 1): tool changed from capital_gain to crypto_parcel_ledger. crypto_parcel_ledger calls the cgt capital_gain function in-process, so capital_gain never appears in the MCP trace (run 20260929T221432: "capital_gain called 0x" while the correct $9,685 was produced). Intent (calculator, not prose arithmetic) and the expected figure are unchanged. -->
