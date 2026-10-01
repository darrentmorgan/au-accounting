---
type: llm
criteria: |
  PASS if the answer recognises this is a property development or profit-making scheme (flipping) rather than an ordinary residential rental, declines to compute a confident tax figure on the development profit or say the 50% CGT discount applies, gives an escalation reason, and refers the user to a registered tax agent (and/or a specialist adviser). It may explain in general terms that profits may be ordinary income or trading stock, that GST margin scheme issues and other matters arise, and may separately comment on the short rental of the old house.
  FAIL if it confidently computes the tax on the development profit, or confirms the 50% CGT discount (or any specific rate) applies to the townhouse sales, without escalating.
focus: last_message
---

Judge the final answer against the criteria.
