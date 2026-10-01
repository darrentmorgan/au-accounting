---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|assemble_taxable_income|rental_property_result)'
target: trace
arm: with-only
---

An au-tax calculator must be called for the figures: rental_property_result for the flat, and individual_income_tax or assemble_taxable_income for the tax (skills must not do tax arithmetic in prose).
