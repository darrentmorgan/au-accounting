---
type: llm
criteria: |
  PASS only if the answer covers ALL of the following, correctly:
  1. ABN registration (mentioning the TFN is optional), and optionally a business name with ASIC if trading under a name.
  2. GST registration is required (not optional) because expected turnover of $120,000 is at or above the $75,000 threshold; register within 21 days of knowing (in practice from the 1 October 2026 start).
  3. PAYG withholding registration before the first wage payment to the employee (who starts on 2 November 2026; any stated or assumed first payday on or after that date is fine), plus Single Touch Payroll reporting on or before each payday.
  4. Super: 12% super guarantee on qualifying earnings under Payday Super, paid every payday and received by the employee's fund within 7 business days (for a new employee's first contribution the extended 20-business-day window is also correct) (no quarterly super due dates); super choice form for the new employee.
  5. SA workers compensation: register with ReturnToWorkSA within 14 days of employing (expected wages of about $21,000 for 2026-27 exceed the $16,806 threshold, so registration is needed).
  6. Payroll tax: not payable or registerable because wages are far below the SA $1.5 million threshold.
  7. 2026-27 quarterly BAS due dates: December 2026 quarter (Q2, first BAS since GST starts 1 October) due 28 February 2027 (a Sunday; Monday 1 March 2027 is WA Labour Day, a public holiday for the whole of a State, so the rolled date is Tuesday 2 March 2027; either 28 February 2027 stated with a next-business-day roll, or 2 March 2027, is acceptable; 1 March 2027 is not), March 2027 quarter due 28 April 2027, June 2027 quarter due 28 July 2027 (also correct if the answer gives the two-week online lodgment concession dates, 12 May 2027 and 11 August 2027, as long as the standard 28 April and 28 July dates or the concession basis are stated). The 28 October 2026 September quarter date is either omitted or explained as not applicable because GST registration starts 1 October (a note that the ATO may issue a first BAS is acceptable).
  8. 2026-27 income tax return due 31 October 2027 for self-lodgers (31 October 2027 is a Sunday, so Monday 1 November 2027 is also correct) (or later via a registered tax agent), and mention that PAYG instalments may commence after the first return.
  FAIL if any of items 2, 3, 4, 5, 7 is missing or wrong, if it says GST registration is optional, if it says quarterly super due dates (28 October etc.) apply under Payday Super, or if it invents a payroll tax obligation. The answer should be a working paper with figures used, assumptions, risk flags and any escalations.
focus: last_message
---

Judge the final answer against the criteria.

<!-- Coordinator 2026-09-30: Payday Super gives an extended 20-business-day deadline for a new employee's first contribution (ATO payment deadlines for Payday Super); accepted. -->

<!-- Orchestrator 2026-09-30 (v0.3 gate 3): item 7 corrected. Primary sources: TAA 1953 s 8AAZMB(1) and Sch 1 s 388-52 with the 'business day' definition in s 8AAZMB(2) (a public holiday for the whole of any State is not a business day); ATO 'Lodgment and payment dates on weekends or public holidays' table lists 1 Mar 2027 (Labour Day WA) and gives 2 Mar 2027. See docs/research/due-dates-public-holidays.md. -->

<!-- Orchestrator 2026-09-30 (v0.3 gate 14): split in run 20260930T014955 (FAIL then PASS on answers with the same content). Items 7 and 8 widened: ATO BAS due dates page gives the two-week concession for quarterly BAS lodged online (Q3 and Q4); 31 Oct 2027 is a Sunday, so TAA 1953 Sch 1 s 388-52 moves the return due date to Mon 1 Nov 2027. Both are primary-source-correct answers the old wording could be read to reject. -->

<!-- Orchestrator 2026-09-30 (v0.3 judge round 1 fix M4): items 1 and 3 reworded. The prompt gives 2 November 2026 as the start date, not a pay date, so an answer that assumes a first payday after the start is correct; the TFN was never part of the expectation. Split in run 20260930T074656 (FAIL PASS FAIL on an answer meeting every item). -->
