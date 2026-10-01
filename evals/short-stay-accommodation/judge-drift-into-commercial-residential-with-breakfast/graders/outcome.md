---
type: llm
criteria: |
  PASS only if the answer: says length of stay does not decide the question; explains that whether premises are commercial residential premises (hotel, motel, inn, hostel, boarding house or similar) is a question of fact and degree under GSTR 2012/6 using indicators such as business-like operation, several unrelated guests at once, being held out to the public, central management and reception, and services such as daily cleaning and meals; says the two furnished rooms with linen only were the kind of arrangement the ATO treats as residential premises (input taxed), while a three-bedroom bed and breakfast with breakfast and daily cleaning is the kind the ATO's own example treats as commercial residential premises; says the new set-up moves towards commercial residential premises (taxable) but does not give a final determination and recommends a registered tax agent and, for certainty, an ATO private ruling; and says registration would then depend on the GST turnover from the taxable accommodation supplies reaching the registration threshold (input taxed supplies excluded).
  FAIL if it confidently says the new arrangement is still input taxed, or confidently says it is now taxable and registration is required, without the fact-based caveat and escalation.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working / sources: GSTR 2012/6 para 12 (characteristics of hotel-like premises), para 41 (features pointing away), Example 3 paras 51-52 (house with two furnished spare rooms, linen only: not CRP, input taxed), Example 2 paras 49-50 (B&B with three bedrooms, communal dining, on-site owner, daily cleaning, breakfast: CRP). s 195-1 CRP definition; s 188-15 turnover. Draft GSTR 2012/6DC (Nov 2025) is not final; the ATO says its view is unchanged. Repo refusal AU-GST-002 is the expected escalation.
https://www.ato.gov.au/law/view/document?docid=GST%2FGSTR20126%2FNAT%2FATO%2F00001
-->
