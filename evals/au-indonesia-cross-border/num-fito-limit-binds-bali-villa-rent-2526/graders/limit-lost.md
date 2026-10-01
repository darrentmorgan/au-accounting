---
type: llm
criteria: |
  PASS only if the answer gives $6,400 as the usable offset and says the remaining A$600 of Indonesian tax gets no Australian offset (it is not refunded and not carried forward).
  FAIL if it allows $7,000, or says the excess carries forward to a later year or is refunded.
focus: last_message
---

<!--
ATO FITO guide 'Calculate your FITO or offset limit': non-refundable, no carry-forward. ITAA 1997 s 770-75(1): if the offset exceeds the limit, reduce it by the excess. Expected excess = 7,000 - 6,400 = 600.
-->
Judge the final answer against the criteria.
