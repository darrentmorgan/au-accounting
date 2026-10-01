---
type: llm
criteria: |
  The net GST and G1 figures are checked by separate regex graders; judge the reasoning only. PASS unless the answer makes one of these errors:
  1. Says the room rent counts towards GST turnover, or that registration was required because of the rooms or platform income (registration was required because the consulting alone is $82,800 projected, at or above the $75,000 threshold; GSTA 1999 s 188-15(1)(a) excludes input taxed supplies).
  2. Says GST must be charged on the room rent, or treats the rooms as commercial residential premises (two furnished rooms in the owner's home with linen only are residential premises, input taxed: GSTR 2012/6 Example 3).
  3. Includes the $200 GST on the cleaner and laundry in 1B (no credit for input taxed supplies: GSTA s 11-15(2)(a)), or gives 1A other than $2,070 or 1B other than $150.
  4. Leaves the room rent out of G1.
  5. Gives 1 March 2027 as the due date (28 February 2027 with a next-business-day roll, or Tuesday 2 March 2027, is correct).
  6. Has no working-paper structure (figures used, assumptions, risk flags, refusals or escalations or an explicit "none").
  Wording about whether "the accountant is right" does not matter; judge the substance.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Hand computation, 2026-27. The registration threshold is data/rates/2026-27.yaml gst.registration_threshold = 75,000 (VERIFIED, ATO Registering for GST page).
Sources: GSTA 1999 s 23-5 (registration), s 23-15 (21 days), s 188-10 and s 188-15(1)(a) (GST turnover excludes input taxed supplies) https://www.ato.gov.au/law/view/print?DocID=PAC/19990055/188-15&PiT=99991231235958 ; s 40-35 and s 195-1 (residential premises, input taxed) ; GSTR 2012/6 Example 3 https://www.ato.gov.au/law/view/document?docid=GST%2FGSTR20126%2FNAT%2FATO%2F00001 ; s 11-15(2)(a) (no credit for input taxed supplies) ; ATO Registering for GST https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/registering-for-gst ; BAS G1 rule (input taxed sales ARE reported at G1) https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/managing-gst-in-your-business/reporting-paying-and-activity-statements/completing-your-bas-for-gst/complete-your-bas/step-1-sales ; due-date rule TAA 1953 Sch 1 s 388-52 with s 8AAZMB (business day excludes a public holiday for the whole of any State) and ATO "Lodgment and payment dates on weekends or public holidays" (same convention as int-onboard-sa-sole-trader-2627, correction of 2026-09-30, docs/research/due-dates-public-holidays.md).

Note the unsettled O1 point (the ATO Registering for GST page lists sharing economy income among must-register cases) is not needed: registration here is required on the consulting turnover alone under s 23-5, so the case does not depend on it.

1. Turnover: consulting 6,900 x 12 = 82,800 >= 75,000. Rooms 4,500 x 12 = 54,000 excluded (input taxed). Had the consulting been under 75,000 (say 60,000), registration would not be required even with 114,000 total receipts.
2. Sales: 3 x 6,900 = 20,700; GST 3 x 690 = 2,070 = 1A; taxable sales incl GST 22,770. Rent 13,500, no GST. G1 = 22,770 + 13,500 = 36,270 (GST-inclusive). GST-exclusive alternative = 20,700 + 13,500 = 34,200.
3. Credits: consulting-only purchases GST 150 -> 1B = 150. Cleaner/laundry GST 200 relates to input taxed rent: nil credit.
4. Net = 2,070 - 150 = 1,920 payable. (Wrong: 1B 350 -> 1,720; GST on rent 1,227.27 added; G1 22,770.)
5. Due: Oct-Dec quarter -> 28 Feb 2027 (Sunday, per calendar). Monday 1 Mar 2027 is Labour Day in WA -> next business day Tuesday 2 Mar 2027.

6. Orchestrator 2026-09-30 (v0.3 gate 14): wording clarified after a split (run 20260930T014955: PASS then FAIL on an answer with every figure and conclusion correct, which said 'your accountant is right that you had to register and wrong about the reason'). Expectation unchanged.
7. Orchestrator 2026-09-30 (v0.3 judge round 1 fix M4): the rubric was changed from a must-cover list ("covers ALL of the following") to a must-not-err list ("PASS unless the answer makes one of these errors"), after repeated judge splits on answers with every figure and conclusion correct (runs 20260930T014955 and 20260930T064346, votes FAIL FAIL PASS). The legal points survive as error conditions and the figures are still checked by figure.md and g1-includes-rent.md. This is a weaker test than before: the answer is no longer required to explain why the accountant's reasoning is wrong, to state the 21-day registration window (s 23-15), or to apportion shared overheads. Those three positive requirements are not checked by any grader.
-->
