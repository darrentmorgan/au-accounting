---
type: regex
pattern: '(?<![\d,.])\$?\s?80,000(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Working (GSTA 1999 ss 23-5, 188-10, 188-15; ATO Registering for GST page, threshold $75,000, register within 21 days):
1. Residential premises rent is input taxed (s 40-35(1)(a); s 195-1 applies regardless of term of occupation) and input taxed supplies are excluded from GST turnover (s 188-15(1)(a)). So the $180,000 does not count.
2. Management fees for other owners are taxable supplies of a service and count: $20,000. Consulting $60,000 counts.
3. GST turnover = 60,000 + 20,000 = $80,000, at or above $75,000 on both current and projected measures, so registration is required within 21 days.
4. Registering does not change the rent: it stays input taxed (s 9-30(2)) and no credits on its costs (s 11-15(2)(a)); credits only for costs of the consulting and management activity, with apportionment for shared overheads.
Also acceptable to note the management activity may be a business of letting management, which raises escalation points.
Sources: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/registering-for-gst ; https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/188-15&PiT=99991231235958
-->
The answer states a GST turnover of $80,000.
