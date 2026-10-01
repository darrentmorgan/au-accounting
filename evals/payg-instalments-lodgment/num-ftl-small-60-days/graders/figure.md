---
type: regex
pattern: '(?<![\d,])\$?\s?1,?092(?:\.00)?(?![\d,])'
target: last_message
---

<!--
FTL: 1 penalty unit per 28 days or part thereof, max 5; base amount for small entities. 60 days = 3 periods (1-28, 29-56, 57-60) = 3 units. Due date 28 Jul 2026 is after 1 Jul 2026, so unit = $364 (ATO penalty units page). 3 x 364 = 1,092. (Wrong: 3 x 330 = 990.)
Primary sources: https://www.ato.gov.au/individuals-and-families/paying-the-ato/interest-and-penalties/penalties/failure-to-lodge-on-time-penalty ; https://www.ato.gov.au/individuals-and-families/paying-the-ato/interest-and-penalties/penalties/penalty-units ; https://www.legislation.gov.au/F2026N00424/asmade
-->
The answer states an FTL penalty of $1,092.
