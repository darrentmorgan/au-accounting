---
type: llm
criteria: |
  PASS if the answer: says the rent from letting houses to holiday guests is generally input taxed residential rent (length of stay does not turn houses into commercial residential premises), so no GST is charged to guests; says input taxed supplies are excluded from GST turnover, so the $310,000 does not trigger the $75,000 registration threshold on its own; says no GST credits are available on the costs of the rental; and does not tell the user they must register merely because the income comes through a platform. It may acknowledge the ATO page wording and suggest confirming with a registered tax agent or the ATO, may note that registration depends on other taxable turnover, and may note that many houses or hotel-like services raise a separate commercial residential premises or business question.
  FAIL if it says the user must register or must charge GST on the rent, or that the platform income alone requires registration.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working: GSTA 1999 s 40-35(1)(a), (2)(a): supplies of residential premises are input taxed; s 195-1 residential premises applies regardless of the term of occupation. s 188-15(1)(a): current GST turnover excludes input taxed supplies. s 23-5: registration is required only if you carry on an enterprise and your GST turnover meets the registration turnover threshold (ATO Registering for GST page: $75,000; 21 days). ATO page "Renting out all or part of your home": you don't need to pay GST on residential rent; consider GST only if you carry on an enterprise renting out commercial residential premises. The ATO "Registering for GST" page (read 2026-09-29) also lists income through the sharing economy or digital platforms as a case to register; that wording appears to conflict with s 23-5 and the ATO accommodation guidance (research brief open question O1), so the grader does not require the answer to resolve it, only not to assert must-register.
Sources: https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/40-35&PiT=99991231235958 ; https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/188-15&PiT=99991231235958 ; https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/sharing-economy-and-tax/renting-out-all-or-part-of-your-home
-->
