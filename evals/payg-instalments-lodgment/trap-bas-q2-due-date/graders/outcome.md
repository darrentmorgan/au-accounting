---
type: llm
criteria: |
  PASS if the answer says the Q2 (October to December) quarterly BAS is due 28 February (or the next business day when 28 February falls on a weekend, e.g. Tuesday 2 March 2027 for 2026-27, because Monday 1 March 2027 is WA Labour Day), that the two-week online concession does not apply to Q2 because the date already includes an extension, and (optionally) that the registered agent program date is not applicable to Q2. It corrects both the 28 January and 11 February claims.
  FAIL if it accepts 28 January or 11 February, or gives an extra two weeks for Q2 (e.g. 14 March).
focus: last_message
---

Judge the final answer against the criteria.

<!-- Orchestrator 2026-09-30 (v0.3 gate 3): example date corrected from 1 to 2 March 2027 (TAA 1953 s 8AAZMB; ATO weekends and public holidays table row for 1 Mar 2027). The core expectation (28 February, no online concession) is unchanged. -->
