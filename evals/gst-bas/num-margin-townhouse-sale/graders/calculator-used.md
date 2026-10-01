---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:margin_scheme_gst|bas_gst_worksheet)'
target: trace
arm: with-only
---

One of these au-tax calculators must be called for the figure: margin_scheme_gst, bas_gst_worksheet (skills must not do tax arithmetic in prose).
