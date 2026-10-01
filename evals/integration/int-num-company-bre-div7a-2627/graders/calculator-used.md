---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:company_tax|div7a_minimum_repayment)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: company_tax, div7a_minimum_repayment (skills must not do tax arithmetic in prose).
