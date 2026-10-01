---
type: llm
criteria: |
  PASS only if all hold:
  1. It explains that for a resident individual holding the ETH on 30 June 2027 there is a deemed sale just before 1 July 2027 at market value ($36,000) and reacquisition at that value, giving a notional gain of $12,000 ($36,000 less $24,000) that is deferred to the year of the actual sale (2027-28).
  2. It says that deferred $12,000 can still get the 50% discount (about $6,000) because the ETH was held for at least 12 months up to the actual sale, ignoring the deemed sale.
  3. It says the gain after 1 July 2027 (at most about $3,000 in nominal terms, $39,000 less $36,000) does not get the 50% discount and is instead subject to indexation of the cost base (for assets held 12 months) and possible minimum tax; it does not compute an exact indexed figure itself (future CPI is not published), or it defers that to the cgt tool.
  4. It says the market value just before 1 July 2027 must be evidenced (keep exchange price data for that time, per parcel), and that its figures are illustrative.
  5. It recommends registered tax agent review and does not present the result as final advice.
  FAIL if it applies the 50% discount to the whole $27,000 gain, ignores the deemed sale, or says the ETH is taxed with no discount at all on the pre-July 2027 growth.
focus: last_message
---

<!--
Treasury Laws Amendment (Tax Reform No. 1) Act 2026 (Act 49 of 2026) as compiled in ITAA 1997 compilation 266 (https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_3/document_3.html): discount only for events before 1 Jul 2027 (s 115-100); indexation for events from 1 Jul 2027 (ss 110-36(1A), 114-10, 114-25); deemed sale at market value just before 1 Jul 2027 for assets a resident individual holds (s 112-155), gain or loss deferred to the year of the real disposal (s 112-160); a deferred gain is a discount gain if held 12 months to the real disposal ignoring the deemed sale (ss 112-160(5), 114-10(9)). Treasurer's release (https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/media-releases/consultation-next-tranche-tax-reform-legislation). Brief R-71 to R-73, T-22, W-08.
Working: deemed proceeds 36,000; notional gain 36,000 - 24,000 = 12,000, deferred; held 5 Mar 2026 to 20 Oct 2027 (about 19 months) so discount 50% = 6,000. Post-July part: proceeds 39,000 less cost base 36,000 indexed from 1 Jul 2027 -> at most 3,000 nominal; no 50% discount; Div 119 minimum tax may apply. Indexation needs CPI numbers not yet published; only the upper bound is asserted. The apportioning method (s 112-155(4)) is aimed at real property and assets with no readily ascertainable market value, so the grader does not require it.
-->
Judge the final answer against the criteria.
