---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__(?:bas_gst_worksheet|gst_registration_check|bas_due_date)'
target: trace
arm: with-only
---

A GST calculator must be called for the figures: bas_gst_worksheet for the BAS, gst_registration_check for the threshold, or bas_due_date for the due date (skills must not do tax arithmetic in prose).
