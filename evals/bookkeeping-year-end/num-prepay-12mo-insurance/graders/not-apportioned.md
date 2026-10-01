---
type: llm
criteria: |
  PASS if the answer gives the 2025-26 TAX deduction as the full $9,000 (GST-exclusive) under the 12-month prepayment rule. Mentioning that the accounts/books recognise only about $1,504 of expense at 30 June (the rest as a prepayment asset) is correct and acceptable.
  FAIL if it presents about $1,504 (the apportioned amount) as the 2025-26 tax deduction.
focus: last_message
---

Judge the final answer against the criteria.
<!-- CORRECTED by coordinator 2026-09-29: the original not_contains regex on "1,504" failed correct answers that also state the book (accounting) expense. Guard intent unchanged: 9,000 x 61/365 = 1,504.11 must not be the tax deduction. -->
