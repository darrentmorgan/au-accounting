---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|foreign_income_tax_offset|assemble_taxable_income)'
target: trace
arm: with-only
---

One of the au-tax calculators must be called for the tax figure: individual_income_tax, foreign_income_tax_offset or assemble_taxable_income (skills must not do tax arithmetic in prose).
