---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|foreign_income_tax_offset)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: individual_income_tax, foreign_income_tax_offset (skills must not do tax arithmetic in prose).
