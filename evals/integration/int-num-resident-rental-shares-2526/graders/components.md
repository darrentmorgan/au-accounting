---
type: llm
criteria: |
  PASS if the answer shows the component figures needed to reach the final number, specifically: taxable income $108,000 (salary 110,000, rental loss -8,000, discounted net capital gain 6,000), income tax before Medicare $23,188, Medicare levy $2,160, and that no Medicare levy surcharge applies. It should also note the rental loss is deductible because the property was acquired before 12 May 2026 (grandfathering under the 2026 negative gearing changes).. It must also satisfy: The answer is laid out as a working paper for review by a registered tax agent, with clearly identifiable sections for: (a) figures used (with the source or table each came from), (b) assumptions, (c) risk flags, and (d) refusals/escalations (or an explicit statement that none are needed).
  FAIL if the final figure appears without the components, or if the working-paper sections (figures used, assumptions, risk flags, refusals/escalations) are missing.
focus: last_message
---

Judge the final answer against the criteria.
