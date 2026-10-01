---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|simplified_depreciation)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: individual_income_tax, simplified_depreciation (skills must not do tax arithmetic in prose).
