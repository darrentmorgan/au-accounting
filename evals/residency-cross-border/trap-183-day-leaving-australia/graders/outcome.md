---
type: llm
criteria: |
  PASS only if all hold:
  1. It rejects the inference that being in Australia under 183 days makes the person a non-resident: the 183-day test is only one way to be a resident and is not a test for non-residency.
  2. It identifies that the person is Australian-domiciled and that the domicile test and resides test turn on whether their permanent place of abode is outside Australia and whether they abandoned Australian residency; a 2-year plan with an intention to return points toward remaining an Australian resident (or at least is uncertain), so it does not confidently declare non-residency.
  3. It refers to the ATO residency tests or TR 2023/1 and recommends confirming the facts (for example with a registered tax agent or an ATO ruling) before treating Balinese income as untaxed in Australia.
  FAIL if it confirms the person is a non-resident on the day count alone.
focus: last_message
---

Judge the final answer against the criteria.
