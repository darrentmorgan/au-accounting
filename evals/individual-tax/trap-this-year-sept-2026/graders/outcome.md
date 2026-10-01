---
type: llm
criteria: |
  PASS only if all hold:
  1. The answer explicitly names the income year it used (e.g. "2026-27", 1 July 2026 to 30 June 2027) or asks which year is meant while also stating a default.
  2. If it computes for 2026-27 it uses the 2026-27 resident scale (15c second bracket, $4,020 at $45,000): tax $4,020 + 30c x 35,000 = $14,520 before Medicare. If it computes for 2025-26 it must say so and use 16c: $4,288 + 0.30 x 35,000 = $14,788.
  3. It does not silently mix 2025-26 and 2026-27 figures.
  FAIL if no income year is stated, or the figures do not match the stated year.
focus: last_message
---

Judge the final answer against the criteria.
