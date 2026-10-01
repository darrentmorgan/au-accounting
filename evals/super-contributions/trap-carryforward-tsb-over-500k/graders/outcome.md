---
type: llm
criteria: |
  Background: carry-forward requires TSB below $500,000 at 30 June of the previous financial year. Here TSB at 30 June 2026 was $540,000, so the unused amounts cannot be used for 2026-27. The 2026-27 cap is $32,500, so $60,000 would leave about $27,500 of excess concessional contributions (taxed at marginal rate with a 15% offset and counted towards the non-concessional cap unless released).
  PASS if the answer says carry-forward is NOT available because TSB is $500,000 or more at 30 June 2026, states the cap is $32,500, and warns that $60,000 would produce excess concessional contributions (around $27,500).
  FAIL if it says the $60,000 is allowed under carry-forward or otherwise applies unused caps despite the $540,000 balance.
focus: last_message
---

Judge the final answer against the criteria.
