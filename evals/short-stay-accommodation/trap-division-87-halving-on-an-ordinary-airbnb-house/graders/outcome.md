---
type: llm
criteria: |
  PASS only if the answer says: no GST is charged or reported, because a house let to guests is residential premises whose rent is input taxed whatever the length of stay; the Division 87 long-term accommodation rules (28 days or more) apply only to commercial residential premises such as a hotel or motel, not to this house; the $8,400 rent is still assessable income to be declared in the income tax return (gross before Airbnb fees); the host is not required to register for GST on this income and cannot claim GST credits on costs.
  FAIL if it calculates or applies half GST or any GST to the booking, or says the host must register.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working: GSTA 1999 s 40-35(1)(a), (2)(a) and s 195-1 residential premises 'regardless of the term of occupation'; s 87-15 (read) defines 'commercial accommodation' as accommodation in commercial residential premises, so Division 87 applies to taxable supplies of commercial accommodation only (ATO CRP page; research brief rule D7). 42 x $200 = $8,400 gross income.
Sources: https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/40-35&PiT=99991231235958 ; https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/87-15&PiT=99991231235958
-->
