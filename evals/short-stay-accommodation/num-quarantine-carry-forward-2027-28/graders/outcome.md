---
type: llm
criteria: |
  PASS only if the answer gets all of these: (1) the 2027-28 excess of $12,000 is not deductible against the salary (the quarantine in ITAA 1997 s 26-155 applies because the dwelling was acquired after 7.30 pm ACT time on 12 May 2026 and is an established dwelling, not a new residential dwelling), so the 2027-28 rental result is nil (income $40,000 fully offset by $40,000 of deductions) and $12,000 is carried forward; (2) in 2028-29 the deductions plus the carried amount are $50,000 against $45,000 income, so $45,000 is deducted, net nil, and $5,000 carries forward; (3) the carried amounts can only be used against future income from residential dwellings (and, in the CGT method statement, residential capital gains), not the salary; (4) it treats a short-stay apartment as a residential dwelling for this purpose (short-term letting is not carved out; hotels, motels, inns, hostels and boarding houses are). It may flag that whether a dwelling is a new residential dwelling depends on an instrument, and recommend registered agent review, but must still give the figures on the stated established-dwelling assumption.
  FAIL if it lets the $12,000 loss offset salary, says short-stay letting takes the apartment outside the quarantine, gets the carry-forward figures wrong, or refuses to give any figures.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working: ITAA 1997 s 26-155(1) (inserted by Treasury Laws Amendment (Tax Reform No. 1) Act 2026, No. 49 of 2026, Sch 2; Act text read): where deductions for using or holding residential dwellings as residential accommodation exceed the assessable income from them, the excess is not deductible for the year and is carried into the next year. Applies from the 2027-28 income year. Exceptions (s 26-155(2)): interest last acquired before 7.30 pm ACT time on 12 May 2026 (contract time counts, s 26-155(3)); new residential dwelling; ministerial class. A contract on 3 Sep 2026 is after the cut-off, and an established 2004 dwelling is not new.
2027-28: excess = 52,000 - 40,000 = 12,000 not deductible; deduct 40,000; net nil; carry forward 12,000.
2028-29: available = 38,000 + 12,000 = 50,000 against income 45,000; deduct 45,000; net nil; carry forward 5,000.
The Explanatory Memorandum (paras 2.20-2.21) says short-stay apartments can be residential dwellings. Definition s 26-160(1) excludes caravans, hotels, motels, inns, hostels, boarding houses, student accommodation and boats.
Source: https://www.legislation.gov.au/C2026A00049/asmade/2026-06-26/text/original/pdf
Uncertainty: rental-property refusal AU-RENT-002 says the tool refuses when a 2027-28 year is requested. The expectation is correct on the Act; the skill may present the figures with the AU-RENT-002 caveat and registered-agent review.
-->
