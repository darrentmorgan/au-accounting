---
type: llm
criteria: |
  PASS only if all hold:
  1. It puts only the 29 June 2026 sale in the 2025-26 return, with a net capital gain of $3,000 ($6,000 halved by the 50% discount).
  2. It says the 3 July 2026 sale belongs to the 2026-27 income year (1 July 2026 to 30 June 2027), where its discounted gain is $2,000.
  3. It states the income year it applied.
  FAIL if it includes the July sale in 2025-26 (net $5,000), omits the discount, or combines both into one year.
focus: last_message
---

<!--
Income year runs 1 Jul to 30 Jun (CONVENTIONS section 3). CGT event A1 occurs at the contract date/change of ownership (ITAA 1997 s 104-10(3)), 29 Jun 2026 -> 2025-26; 3 Jul 2026 -> 2026-27. Both are held over 12 months and before 1 Jul 2027, so 50% discount (cgt.discount_individual_trust VERIFIED; https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount).
2025-26: 6,000 x 0.5 = 3,000. 2026-27: 4,000 x 0.5 = 2,000.
Times are given in Adelaide local time on purpose: the UTC/local-date convention for events near midnight is unsettled (brief Q-09) and is not tested here.
-->
Judge the final answer against the criteria.
