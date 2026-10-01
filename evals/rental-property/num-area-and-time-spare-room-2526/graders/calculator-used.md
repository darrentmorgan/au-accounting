---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:rental_property_result|main_residence_exemption)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: rental_property_result, main_residence_exemption (skills must not do tax arithmetic in prose).
