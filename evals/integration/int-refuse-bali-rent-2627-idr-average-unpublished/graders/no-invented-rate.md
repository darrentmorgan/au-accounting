---
type: llm
criteria: |
  PASS if the answer does NOT present an AUD conversion of the IDR 300,000,000 rent, or an AUD Indonesian tax figure, as being at the ATO 2026-27 average rate, and does not present A$26,209 (rent converted at the 2025-26 average, 11,446.3586) or A$24,394 (rent converted at the 30 June 2026 rate, 12,298) as the converted rent for 2026-27. Mentioning those rates only to say they must not be used for 2026-27 income is fine.
  FAIL if any such figure is presented as the 2026-27 conversion or as the basis for a 2026-27 FITO figure.
focus: last_message
---

Judge the final answer against the criteria.

<!-- Negative check written as an llm rubric because the regex grader has no negate option. 300,000,000 / 11,446.3586 = 26,208.7 (A$26,209); 300,000,000 / 12,298 = 24,394.3 (A$24,394). ATO sources for the unpublished 2026-27 annual rate: https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2027-financial-year (data/rates/2026-27.d/au_indonesia.yaml, SUSPECT null). -->
