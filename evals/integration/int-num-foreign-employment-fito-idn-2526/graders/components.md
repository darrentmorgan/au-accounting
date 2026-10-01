---
type: llm
criteria: |
  PASS if the answer shows the component figures needed to reach the final number, specifically: taxable income $110,000, tax before offsets including Medicare $25,988, the FITO limit test (tax with foreign income $25,988 versus without $19,588, limit $6,400), FITO of $3,000, and net $22,988. It should mention the Australia-Indonesia tax treaty (employment income article and relief article) and that the Indonesian tax must be a creditable foreign income tax; it should flag that conversion to AUD and evidence of the Indonesian tax paid need checking.. It must also satisfy: The answer is laid out as a working paper for review by a registered tax agent, with clearly identifiable sections for: (a) figures used (with the source or table each came from), (b) assumptions, (c) risk flags, and (d) refusals/escalations (or an explicit statement that none are needed).
  FAIL if the final figure appears without the components, or if the working-paper sections (figures used, assumptions, risk flags, refusals/escalations) are missing.
focus: last_message
---

Judge the final answer against the criteria.
