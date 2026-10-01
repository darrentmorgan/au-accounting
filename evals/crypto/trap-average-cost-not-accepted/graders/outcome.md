---
type: llm
criteria: |
  PASS only if all hold:
  1. It does not accept average cost across parcels bought on different days as the method (it says average cost is not acceptable, or not supported by the ATO's approach for identical assets acquired at different times).
  2. It applies first-in first-out as the default when the parcels cannot be identified: cost base $3,000, gain $3,000, discounted (held over 12 months) to a net capital gain of $1,500.
  3. If it mentions choosing a specific parcel (for example the highest-cost one), it says that needs contemporaneous records showing which units were disposed of, which the user says they lack.
  FAIL if it adopts the $4,000 average (gain $2,000 or net $1,000) as its answer, or picks the highest-cost parcel without the records caveat.
focus: last_message
---

<!--
TD 33 (considered view of the ATO, https://www.ato.gov.au/law/view/document?DocID=CGD%2FTD33%2FNAT%2FATO%2F00001&PiT=99991231235958): where identical holdings cannot be individually distinguished the Commissioner accepts first-in first-out or the taxpayer's own selection supported by adequate records; average cost is not accepted unless units are of the same company acquired the same day with identical rights. Note (i) extends this to other identical assets such as coins. Applying it to crypto is by analogy (no crypto-specific ATO statement; brief R-20, R-21, Q-04), so the grader does not demand TD 33 by name.
FIFO: first parcel 10 Jan 2024, cost 3,000. Proceeds 6,000. Gain 3,000. Held over 12 months. Discount 50% (cgt.discount_individual_trust) = 1,500 net capital gain.
For reference only: parcel 2 (15 Mar 2025, 5,000): gain 1,000 -> 500; parcel 3 (20 Jul 2025, 4,000): gain 2,000 -> 1,000; each held over 12 months at 25 Aug 2026. Average cost (wrong): 2,000 -> 1,000.
-->
Judge the final answer against the criteria.
