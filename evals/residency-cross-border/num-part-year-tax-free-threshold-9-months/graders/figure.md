---
type: regex
pattern: '(?<![\d,])\$?\s?17,?016(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
ATO (Living overseas and becoming a foreign tax-resident; Tax-free threshold for newcomers): part-year threshold = $13,464 + ($4,736 / 12 x months resident, counting the month of leaving).
Resident months July 2025 to March 2026 = 9. Threshold = 13,464 + 4,736 x 9/12 = 13,464 + 3,552 = 17,016.
Tax on 30,000 at resident rates above that threshold (16c bracket): 0.16 x (30,000 - 17,016) = 2,077.44.
Wrong: 13,650 (18,200 x 9/12) or 18,200.
Primary sources: https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/living-overseas-and-becoming-a-foreign-tax-resident ; https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/coming-to-australia/tax-free-threshold-for-newcomers-to-australia
-->
The answer states a tax-free threshold of $17,016.
