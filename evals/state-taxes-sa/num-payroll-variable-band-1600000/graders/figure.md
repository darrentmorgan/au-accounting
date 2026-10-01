---
type: regex
pattern: '(?<![\d,])\$?\s?24,?750(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Wages 1,600,000 sit in the $1.5m to $1.7m band, rate = 4.95% x (1,600,000 - 1,500,000) / 200,000 = 2.475%. Deduction $600,000 (RevenueSA's own example: $1.6m less $600,000, tax calculated on $1m). Tax = 1,000,000 x 2.475% = 24,750.
The linear shade-in formula is from the Payroll Tax Act 2009 Sch 2 cl 5(1a) (formula image not readable in the text version; see RevenueSA). Not a 4.95% flat charge (would give 49,500) and not nil.
Primary sources: https://www.revenuesa.sa.gov.au/payroll-tax/how-is-payroll-tax-calculated ; http://classic.austlii.edu.au/au/legis/sa/consol_act/pta2009155/sch2.html
-->
The answer states $24,750.
