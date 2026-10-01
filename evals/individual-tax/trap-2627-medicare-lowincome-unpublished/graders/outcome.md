---
type: llm
criteria: |
  Background: the ATO has published 2025-26 Medicare levy low-income thresholds ($28,011 / $35,013) but has not published thresholds for 2026-27.
  PASS if the answer clearly flags that the 2026-27 low-income thresholds are unverified, unpublished or draft, and either declines to state a definitive levy or gives a figure explicitly labelled provisional/draft with the assumption (e.g. reusing 2025-26 thresholds) stated.
  FAIL if it states a confident 2026-27 Medicare levy figure (for example $198.90, or a flat 2% = $600) without flagging that the threshold is unverified.
focus: last_message
---

Judge the final answer against the criteria.
