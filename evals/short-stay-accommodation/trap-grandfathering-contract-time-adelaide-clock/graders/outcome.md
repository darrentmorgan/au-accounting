---
type: llm
criteria: |
  PASS only if the answer: says the grandfathering cut-off in ITAA 1997 s 26-155(2)(a) is 7.30 pm by legal time in the Australian Capital Territory on 12 May 2026, not local Adelaide time; works out that on 12 May Adelaide is on Central Standard Time (half an hour behind ACT time, which is on Eastern Standard Time), so 7:10 pm Adelaide time is 7:40 pm ACT time, after the cut-off; says the relevant moment is the contract time (s 26-155(3)), so the July settlement date does not help; concludes the apartment is not grandfathered on the stated facts, so from 2027-28 the excess of deductions over income from it would be quarantined and carried forward (short-stay apartments can be residential dwellings), unless another exception applies (for example a new residential dwelling); and recommends confirming the exact contract time from the contract, and with a registered tax agent.
  FAIL if it says the contract is grandfathered because it was signed before 7.30 pm, ignores the time zone difference, or says settlement date decides.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working: s 26-155(2)(a) (Act 49 of 2026 Sch 2, Act text read): an ownership interest last acquired before 7.30 pm, by legal time in the ACT, on 12 May 2026 is outside the quarantine. s 26-155(3): for a dwelling acquired under a contract the interest is held from the time the contract is entered into (so settlement is irrelevant). On 12 May the ACT is on AEST (UTC+10); Adelaide is on ACST (UTC+9:30) (daylight saving for both starts in October). 7:10 pm ACST = 9:40 UTC = 7:40 pm AEST in the ACT: 10 minutes after the cut-off. Not grandfathered on this basis. 12 May 2026 was a Tuesday (calendar check).
Sources: https://www.legislation.gov.au/C2026A00049/asmade/2026-06-26/text/original/pdf ; repo key rental.negative_gearing_grandfather_date (20260512, 7.30 pm ACT).
Uncertainty: none on the Act text; the skill may hedge under AU-RENT-002, which is acceptable if the time-zone point and the not-grandfathered conclusion are stated.
-->
