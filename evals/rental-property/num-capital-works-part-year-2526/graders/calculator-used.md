---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:capital_works_deduction|rental_property_result)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: capital_works_deduction, rental_property_result (skills must not do tax arithmetic in prose).
