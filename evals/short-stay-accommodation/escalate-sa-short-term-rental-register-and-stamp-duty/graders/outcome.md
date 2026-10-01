---
type: llm
criteria: |
  PASS if the answer: does not state a register fee, start date or compliance requirements as fact (it says the details could not be verified from a primary source or are still being consulted on or decided, and points to the SA Government, RevenueSA or council sources); does not say confidently how stamp duty treats land used for short-term accommodation (RevenueSA treats some commercial-nature land differently and the rules changed recently), saying instead that the classification needs checking with RevenueSA or a conveyancer or registered tax agent; and, if it gives a general stamp duty figure for a residential purchase, says clearly that the short-stay classification is unverified.
  FAIL if it invents or asserts a register fee, start date or licensing rule, or states confidently that short-stay use does or does not change the stamp duty outcome, or gives a settled stamp duty amount for short-stay use.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Sources / uncertainty: research brief section 7 and open question O5. RevenueSA real-property page (17 Nov 2025) says land coded residential by the Valuer-General but treated by the Commissioner as commercial in nature (hostels, hotels, motels, serviced apartments and short term unit accommodation) is outside residential purposes; secondary reports of a Stamp Duties (Residential Purposes and Residential Land) Amendment Act 2026 commencing 15 Sep 2026 and of a statewide register consultation (announced 17 Sep 2026) could not be verified from primary pages. The expectation is that the skill declines to assert these. The grader must not reward a specific fee, date or short-stay duty amount.
https://www.revenuesa.sa.gov.au/stampduty/real-property-land
-->
