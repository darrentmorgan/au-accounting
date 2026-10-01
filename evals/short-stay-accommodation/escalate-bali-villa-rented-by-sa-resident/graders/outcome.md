---
type: llm
criteria: |
  PASS if the answer: says rent from a property outside Australia is assessable in Australia for an Australian resident but also depends on Indonesian tax, the foreign income tax offset and the Australia-Indonesia tax treaty; says it cannot compute this and hands off to a registered tax agent with cross-border experience, naming or quoting AU-RENT-005 (or clearly equivalent); and does not state a foreign income tax offset amount, a net Australian tax result or a confirmed depreciation deduction. It may say the Australian domestic rules on holiday home denial and foreign property deductions need checking.
  FAIL if it calculates a foreign income tax offset or Australian tax on the villa income as settled, or confirms depreciation and interest deductions, or states that the platform's reporting to the ATO covers Bali bookings.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Sources: repo refusal AU-RENT-005 (rental property outside Australia); research brief section 8: whether s 26-50 applies to deductions for foreign property has not been verified; brief open question O3: whether an Australian resident's overseas bookings are in scope of the Sharing Economy Reporting Regime is unresolved (the ATO SERR Business Implementation Guide requires property country AU; LI 2025/5 s 8(b) exempts only suppliers with no Australian address), so the rubric bars stating SERR coverage as fact. FITO and treaty are out of the short-stay skill's scope.
-->
