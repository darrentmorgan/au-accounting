---
type: llm
criteria: |
  PASS if the answer says residential rent (residential premises let for residential accommodation) is input-taxed: no GST is added to the rent and no GST is reported at 1A for it. It should note rent is still reported in total sales at G1 (and G4 records) or otherwise acknowledge it is outside taxable sales, and that no GST credits can be claimed on costs of the rental.
  FAIL if it tells the user to charge or report GST on the residential rent, or treats it as GST-free (which would allow credits).
focus: last_message
---

Judge the final answer against the criteria.
