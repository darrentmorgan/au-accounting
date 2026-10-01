---
type: regex
pattern: '(?<![\d,.])\$?\s?1,024(?:\.50?)?(?![\d,])'
target: last_message
---

<!--
Working (GSTA 1999 ss 87-10, 87-20; ATO CRP page):
1. A motel is commercial residential premises (s 195-1), so its supplies are taxable and Division 87 can apply. 40 continuous nights is long-term accommodation (28 days or more, s 87-20). Fewer than 70% of guests stay 28 days or more, so the premises are not predominantly long-term: s 87-10 applies (first 27 days at normal value, later days at 50% of the price that would otherwise apply).
2. Nights 1-27: normal GST = 1/11 of $330 = $30 a night. 27 x $30 = $810.
3. Nights 28-40 = 13 nights. Half of the GST-inclusive price = $165; GST = 10% of $165 = $16.50 a night (ATO worked example: half of $220 is $110, GST $11). 13 x $16.50 = $214.50.
4. Total GST = 810 + 214.50 = $1,024.50.
Comparators: predominantly long-term premises would be 40 x $16.50 = $660; choosing not to apply Division 87 (s 87-25) makes the whole stay input taxed (nil); no Division 87 at all would be 40 x $30 = $1,200.
Sources: https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/87-10&PiT=99991231235958 ; https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/property/gst-and-commercial-property/commercial-residential-property
-->
The answer states GST of $1,024.50 for the stay.
