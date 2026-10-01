---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|assemble_taxable_income)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: individual_income_tax, assemble_taxable_income (skills must not do tax arithmetic in prose).
