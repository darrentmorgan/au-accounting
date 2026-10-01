---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:sa_payroll_tax|super_guarantee)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: sa_payroll_tax, super_guarantee (skills must not do tax arithmetic in prose).
