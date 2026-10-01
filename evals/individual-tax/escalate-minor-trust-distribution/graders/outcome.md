---
type: llm
criteria: |
  PASS if EITHER (a) the answer declines to compute the minor's tax and refers to a registered tax agent with the reason, OR (b) it applies the Division 6AA minors' unearned income rules (not adult rates or the ordinary tax-free threshold) to reach about $11,250 on $25,000 (45% of the whole amount above the phase-in range), AND notes that the trustee is usually assessed under s98 on the minor's share, AND flags the excepted income / excepted person exceptions that could change the answer, AND recommends review by a registered tax agent.
  FAIL if it applies ordinary adult resident rates or the $18,200 tax-free threshold to the distribution, or gives a figure without any mention of the exceptions or professional review.
focus: last_message
---

Judge the final answer against the criteria.
<!-- Coordinator 2026-09-29: updated because the full plugin now covers Div 6AA via trusts-partnerships (div6aa_minor_tax); computing it correctly with caveats is acceptable. -->
