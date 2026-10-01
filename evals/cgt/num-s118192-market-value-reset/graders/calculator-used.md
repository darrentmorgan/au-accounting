---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:main_residence_exemption|capital_gain)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: main_residence_exemption, capital_gain (skills must not do tax arithmetic in prose).
