---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:foreign_income_tax_offset|indonesia_dta_check)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: foreign_income_tax_offset, indonesia_dta_check (skills must not do tax arithmetic in prose).
