---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:capital_gain|net_capital_gain|crypto\w*)'
target: trace
arm: with-only
---

A CGT or crypto calculator must be called for the crypto disposals (capital_gain, net_capital_gain or a crypto ledger tool). The discount and loss ordering must come from the tool, not from prose arithmetic.
