---
type: regex
pattern: '(?<![\d,])\$?\s?6,73[12](?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
2025-26. Residential building, construction started after 15 Sep 1987, so 2.5% of construction cost (not the $780,000 purchase price).
Annual = 360,000 x 2.5% = 9,000. Income-producing days 1 Oct 2025 to 30 Jun 2026 inclusive = 31+30+31+31+28+31+30+31+30 = 273 (ATO's Meg example counts 1 Mar to 30 Jun as 122, same inclusive method).
Claim = 9,000 x 273/365 = 6,731.51 (ATO rounds to whole dollars: 6,732). Regex accepts 6,731 or 6,732 with optional cents.
Primary source: https://www.ato.gov.au/individuals-and-families/investments-and-assets/property-and-land/residential-rental-properties/rental-expenses/capital-expenses/work-out-your-capital-works-deductions
-->
The answer states a capital works deduction of about $6,731 (or $6,732).
