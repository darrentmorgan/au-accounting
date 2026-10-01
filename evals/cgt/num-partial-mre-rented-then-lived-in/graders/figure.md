---
type: regex
pattern: '(?<![\d,])150,0(?:3\d|8\d)(?![\d])'
target: last_message
---

<!--
Ownership period 1 Sep 2018 to 31 Aug 2026 inclusive = 2,922 days. Not main residence (rented, from acquisition so the home-first-used-to-produce-income rule does not apply) 1 Sep 2018 to 31 Aug 2021 inclusive = 1,096 days.
Taxable = 400,000 x 1,096 / 2,922 = 150,034. Event before 1 July 2027 so 50% discount applies (held over 12 months): net capital gain 75,017.
Regex accepts 150,03x (inclusive count) and 150,08x (exclusive count 2,921 gives 150,086).
Primary: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/property-and-capital-gains-tax/your-main-residence---home/using-your-home-for-rental-or-business ; https://www.ato.gov.au/forms-and-instructions/capital-gains-tax-guide-2022/part-a-about-capital-gains-tax/real-estate-and-main-residence
-->
The answer states a taxable pre-discount gain of about $150,034.
