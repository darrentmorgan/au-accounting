---
type: llm
criteria: |
  PASS if the answer says a company-owned property is outside the individual passive-investor model the rental guidance covers (TR 2026/1, PCG 2026/2 and PCG 2026/3 do not apply to entities), says the directors' private use raises other issues (for example Division 7A, fringe benefits tax, and s 26-50 holiday home denial), names or quotes the AU-RENT-001 escalation (or clearly hands off), refers the user to a registered tax agent, and gives no quantified deduction or apportionment for the company.
  FAIL if it applies the individual time-based method or PCG 2026/2 percentages to the company and gives a dollar deduction, or treats the directors' stays as having no tax consequence.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Sources: TR 2026/1 para 5, PCG 2026/2 para 5 (read), PCG 2026/3 para 10: the guidance does not cover entities that are not individuals. s 26-50 is expressed as applying to 'you' with no entity exclusion (research brief 4.8, an inference). Private use of company property by shareholders or directors may be a Division 7A payment or a fringe benefit; that is beyond this skill. Expected code AU-RENT-001.
https://www.ato.gov.au/law/view/document?docid=COG%2FPCG20262%2FNAT%2FATO%2F00001
-->
