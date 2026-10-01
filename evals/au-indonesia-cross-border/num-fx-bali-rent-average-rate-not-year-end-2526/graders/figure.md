---
type: regex
pattern: '(?<![\d,])\$?\s?20,?967(?:\.\d+)?(?!\d|,\d)'
target: last_message
---

<!--
ATO annual foreign exchange rates, financial year ending 30 June 2026 (https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2026-financial-year, published 13 July 2026; rates from the Reserve Bank of Australia): Indonesia (Rupiah) average rate for the year ended 30 Jun 2026 = 11,446.3586 IDR per AUD (VERIFIED, fetched 2026-09-29; the repo brief agrees).
240,000,000 / 11,446.3586 = 20,967.37 (AUD). Hand check: 11,446.3586 x 20,967.37 is about 240,000,000.
ATO translation rules (https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/translation-conversion-rules): for regular foreign income an average rate over a period of up to 12 months is acceptable where it reasonably approximates the spot rates at the times of receipt. ITAA 1997 s 960-50(6) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F960-50).
Wrong answers: 19,515.37 (year-end 12,298.0000, not allowed for foreign income not received in Australia in the year derived); any answer that says the ATO publishes no rupiah rate.
Alternative acceptable method (not tested here): each month's income at its monthly average gives about 21,027; the prompt names the annual average so the expected figure is fixed.
-->
The answer states A$20,967 (about A$20,967.37).
