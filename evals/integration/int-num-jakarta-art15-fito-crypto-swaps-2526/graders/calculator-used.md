---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:individual_income_tax|foreign_income_tax_offset|indonesia_dta_check)'
target: trace
arm: with-only
---

An au-tax calculator must be called for the figures: individual_income_tax, foreign_income_tax_offset, or indonesia_dta_check for the treaty day test (skills must not do tax arithmetic in prose).
