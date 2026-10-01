---
type: regex
pattern: '(?<![\d,])\$?\s?2,?500(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Franking credit = dividend x tax rate / (1 - tax rate) = 7,500 x 0.25 / 0.75 = 2,500. (Grossed-up dividend 10,000.) Wrong method: 7,500 x 25% = 1,875.
Primary source: https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/business-and-organisation-payments/franking-credits/franking-account-and-franking-credit-calculations (ITAA 1997 s202-60)
-->
The answer states a maximum franking credit of $2,500.
