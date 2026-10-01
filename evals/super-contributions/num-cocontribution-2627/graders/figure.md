---
type: regex
pattern: '(?<![\d,.])\$?\s?250(?:\.00)?(?![\d,])'
target: last_message
---

<!--
2026-27 co-contribution thresholds (ATO): lower $49,293, higher $64,293 (higher = lower + $15,000), maximum $500, 50% matching on up to $1,000 contributed.
Income above lower threshold = 56,793 - 49,293 = 7,500. Reduction = 7,500 x (500/15,000) = 250. Entitlement = 500 - 250 = 250 (rounded up to 5c: 250.00).
Primary source: https://www.ato.gov.au/tax-rates-and-codes/key-superannuation-rates-and-thresholds/government-contributions
-->
The answer states a co-contribution of $250.
