---
type: llm
criteria: |
  PASS only if all hold:
  1. It says the CGT event (A1) happens at the contract date (28 June 2027), not settlement, so the event is before 1 July 2027.
  2. It concludes the 50% discount applies (not indexation and the 30% minimum tax), because the new regime is for CGT events on or after 1 July 2027.
  3. It puts the gain in the 2026-27 income year (contract date, before 30 June 2027 year end), not 2027-28.
  4. It states net capital gain of $200,000 ($400,000 gain less 50%), or explains why if it caveats.
  FAIL if it uses settlement as the event date, applies indexation/minimum tax, places the gain in 2027-28, or says the discount is unavailable.
focus: last_message
---

Judge the final answer against the criteria.
