---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:net_capital_gain|capital_gain)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: net_capital_gain, capital_gain (skills must not do tax arithmetic in prose).
