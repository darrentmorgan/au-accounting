---
type: llm
criteria: |
  PASS if the answer does NOT apply a 50% CGT discount to the bot profit and does NOT state a net taxable amount of $31,000 for it (half of $62,000). It may mention the discount only to say it would not be available (holdings under 12 months) or that the character question comes first.
  FAIL if it states or adopts $31,000 as the taxable amount of the bot profit or otherwise applies the discount.
focus: last_message
---

Judge the final answer against the criteria.

<!-- Trap: 62,000 x 50% = 31,000. Discount needs the asset held for at least 12 months (ITAA 1997 s 115-25(1)); the bot held for weeks, and if this is a business the profits are ordinary income or trading stock outside CGT (s 118-25). -->
