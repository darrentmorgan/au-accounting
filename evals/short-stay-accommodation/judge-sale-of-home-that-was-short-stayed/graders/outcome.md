---
type: llm
criteria: |
  PASS only if the answer: says renting out the home can reduce the main residence exemption (interest deductibility test in ITAA 1997 s 118-190, partial exemption by floor area and time used to produce income); says that where a home first used to produce income after 20 August 1996 would have been fully exempt just before then, its cost base is reset to market value at first income use (s 118-192) so a valuation from that date is needed and the guessed $850,000 should not be relied on without a valuation; describes the ATO method (gain from the market value, multiplied by the floor area share used for income, multiplied by days used to produce income divided by days from first income use to sale); may mention that other exemption rules (such as choosing to treat the home as the main residence during an absence, subject to conditions) need checking by a registered tax agent; hands the arithmetic to the capital gains tax analysis rather than presenting a settled figure; and, if it gives an indicative figure using the user's $850,000 estimate, labels it as provisional pending a valuation (the ATO-method taxable part before any discount on those inputs is about $32,854, using 1,461 days).
  FAIL if it says the whole gain is exempt without addressing the income-producing use, treats the $850,000 guess as a confirmed valuation, or ignores the need for a valuation.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Working (indicative, ATO method, ITAA 1997 ss 118-190, 118-192): market value at first income use $850,000 (needs valuation); gain = 1,000,000 - 850,000 = $150,000; floor area used for income 100%; days from 1 Jul 2022 to 30 Jun 2026 inclusive = 4 x 365 + 1 leap day (29 Feb 2024) = 1,461 (the ATO counts inclusively: its own example counts 1 Jul 2019 to 30 Jun 2025 as 2,192 days); days used for income = 320 nights. Taxable part before discount = 150,000 x 320/1,461 = $32,854.21.
The absence rule (s 118-145) may let the owner treat the home as main residence for up to six years while away and income-producing, which could remove the gain entirely; that is why the rubric does not require the figure and asks only for the method, the valuation caveat and the hand-off. The research brief (Example I) leaves the discount and other choices to the cgt skill.
Sources: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/property-and-capital-gains-tax/your-main-residence-home/using-your-home-for-rental-or-business ; https://www.ato.gov.au/law/view/print?DocID=PAC/19970038/118-192&PiT=99991231235958
-->
