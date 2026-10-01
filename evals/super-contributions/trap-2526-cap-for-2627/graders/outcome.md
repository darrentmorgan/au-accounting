---
type: llm
criteria: |
  Background: the concessional cap is $30,000 for 2024-25 and 2025-26 and $32,500 from 1 July 2026 (2026-27). Carry-forward is unavailable because TSB is not under $500,000.
  PASS if the answer says the 2026-27 cap is $32,500 (not $30,000), so there is $2,500 of headroom, and does not tell the user that $30,000 is the limit for 2026-27. It may also mention that carry-forward is unavailable at a $1.2m balance and that contributions count when the fund receives them.
  FAIL if it says the 2026-27 cap is $30,000, or does not state a cap for 2026-27.
focus: last_message
---

Judge the final answer against the criteria.
