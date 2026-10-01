---
type: llm
criteria: |
  PASS only if the answer gives $4,000 as the offset and explains that, because the 50% CGT discount means only half the gain is assessable, only half of the Indonesian tax counts.
  FAIL if it allows $8,000, or gives $4,000 with no reference to the discount or apportionment.
focus: last_message
---

<!--
ATO FITO guide 'When a FITO applies', paragraph on discount capital gains. Confidence note: the prompt's premise that Indonesia's tax is correctly imposed on the gain is an assumption, not a verified Indonesian domestic rate.
-->
Judge the final answer against the criteria.
