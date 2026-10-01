---
type: regex
pattern: '(?<![\d,.])\$?\s?500(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Unpaid and written off = 8,800 - 3,300 = 5,500. Decreasing adjustment under s21-5 = 1/11 x 5,500 = 500 (not 800, which would ignore the part payment). Only available on the accrual (non-cash) basis, and the debt must have been written off as bad or be overdue 12 months or more.
Sources: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/managing-gst-in-your-business/reporting-paying-and-activity-statements/making-adjustments-on-your-activity-statements/types-of-adjustments ; GSTR 2000/2
-->
The answer states a $500 decreasing adjustment.
