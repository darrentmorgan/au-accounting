---
type: llm
criteria: |
  PASS if the answer gives a reasoned recommendation, states eligibility (GST turnover under $10 million, so the user qualifies), explains that on the cash basis GST on sales is attributed when payment is received and credits when paid (which helps cash flow with slow payers), and covers catches: one-time transition adjustments to the BAS (invoices issued but unpaid at switch, and credits for unpaid purchases), the need to lodge consistently and keep records, bad debt adjustments are not needed (or available) on cash, and that the choice should be confirmed with the user's BAS or tax agent. It should not overstate a single certain outcome.
  FAIL if it says the user is ineligible, confuses the GST cash basis with an income tax basis requirement, or gives no trade-offs.
focus: last_message
---

Judge the final answer against the criteria.
