---
type: llm
criteria: |
  PASS only if all hold:
  1. It says the payments are not a company business expense and must not be coded to expenses (a company is a separate legal entity; "owner drawings" is a sole trader or partnership concept).
  2. It identifies proper treatments: salary or director fees (PAYG withholding, STP and super), a declared dividend, or a loan to the shareholder, and says which is documented determines the tax result.
  3. It flags Division 7A: undocumented payments or loans to a shareholder can be a deemed unfranked dividend unless a complying written loan agreement (benchmark interest, maximum term, minimum yearly repayments) is in place by the lodgment day, or the amount is repaid.
  4. It recommends a registered tax agent or accountant to correct the accounts, or treats reclassification as needed before lodgment.
  FAIL if it accepts the expense coding or says drawings from a company are simply deductible.
focus: last_message
---

Judge the final answer against the criteria.
