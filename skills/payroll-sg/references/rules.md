# payroll-sg: rules, dates and refusal messages

Figures are never stated here; the tools read them from `data/rates/<year>.yaml` and `data/rates/<year>.d/payroll-sg.yaml`.

## PAYG withholding (Schedule 1, NAT 1004)

- Weekly equivalent x: weekly = whole dollars + 99 cents; fortnightly = earnings / 2; monthly = earnings (add 1 cent if it ends in 33 cents) x 3 / 13; quarterly = earnings / 13; ignore cents, add 99 cents.
- y = a x - b from the scale's coefficient row; round to the nearest dollar (50 cents up) directly, no preliminary rounding to cents.
- Convert: fortnightly x 2; monthly x 13 / 3 rounded to the nearest dollar; quarterly x 13.
- Scales: 1 no tax-free threshold; 2 tax-free threshold; 3 foreign resident; 4 no TFN (rate x whole-dollar earnings, cents ignored in the result; resident rate includes Medicare levy); 5 full Medicare exemption; 6 half exemption. Scales 1, 2, 3, 5, 6 need a TFN.
- Tax offsets claimed on a Withholding declaration reduce scales 2, 5 and 6 only: the period factor times the annual offsets, rounded to the nearest dollar.
- Medicare levy adjustments for spouse or dependants (scales 2 and 6) are not modelled (AU-PAY-006).
- 53 weekly or 27 fortnightly pays: extra withholding only on the payee's request (Schedule 1 table); not added.
- Schedule 1 dated 1 Jul 2024 applied to payments 1 Jul 2025 to 30 Jun 2026; a new Schedule 1 applies to payments from 1 Jul 2026 (reflecting the lower first-bracket rate and new Medicare thresholds).
- Schedule 8 study loan component: separate component table on the same x, added to the Schedule 1 amount. Not applied if a Medicare levy variation for spouse or dependants is claimed, or where no TFN declaration was given. For 2025-26 the calculator holds only the schedule for payments from 24 Sep 2025 (marginal repayment system).
- No-ABN withholding (TAA Sch 1 s12-190): top rate on the whole payment when the supplier quotes no ABN, the payment exceeds the small-payment threshold (excluding GST) and no exception applies (not carrying on an enterprise, hobby or private supply statement, wholly input taxed, under-18 low weekly payments, exempt income). Report at W4; give a payment summary for no-ABN withholding and lodge the annual report.

## Super guarantee

### Quarters ending on or before 30 Jun 2026
- SG = SG rate x OTE for the quarter, OTE capped at the quarterly maximum contribution base.
- Due 28 days after quarter end: 28 Oct, 28 Jan, 28 Apr, 28 Jul (first business day after if it is a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT; TAA 1953 s 8AAZMB).
- SGC statement and payment due one calendar month later (28 Nov, 28 Feb, 28 May, 28 Aug).
- SGC = shortfall on salary or wages (including overtime) + nominal interest (simple, from the first day of the quarter up to but not including the later of the statement due date and lodgment, days / 365) + administration fee per employee. Not deductible. Late payment offset elections only for quarters up to the March 2026 quarter and contributions received by 30 Jun 2026.
- Contributions for the June 2026 quarter received on or after 29 Jul 2026 are applied to Payday Super QE days instead.

### Payday Super (qualifying earnings paid from 1 Jul 2026)
- QE day: the day the payment leaves the employer's (or payroll entity's) account, even if the employee receives it later (LCR 2026/3 paras 17-21).
- Individual SG amount = qualifying earnings on the QE day x SG rate (SGAA s17A). Several payments on one day are added.
- On-time window: received (allocable) in the 12 months before the QE day, or from the QE day to the end of the usual period after it (`super.payday_super_usual_period_business_days` business days), or within an allowable longer period (first contribution for a new employee or new fund: `super.payday_super_first_contribution_business_days` business days; out-of-cycle payments; exceptional circumstances determinations; a later QE day whose usual period ends before an earlier QE day's longer period ends gets that longer period).
- Business day: not Saturday, Sunday or a public holiday for the whole of any state, the ACT or the NT, wherever the employer is (LCR 2026/3 paras 4, 53).
- Contributions are applied automatically to the earliest QE day with a shortfall; excess carries forward up to 12 months.
- Annual maximum contribution base per employer: once qualifying earnings paid in the year reach it, no further SG is required that year.
- Qualifying earnings: OTE, all commissions, salary-sacrificed amounts that would otherwise be OTE, and for SG-only employees (s12(3) contractors, performers) payments for their labour. Overtime excluded.
- Report qualifying earnings and super liability year to date in STP each payday.

### SG charge from 1 Jul 2026 (LCR 2026/3)
1. Individual base shortfall = SG amount - on-time contributions.
2. Individual final shortfall = base shortfall - late contributions received before the assessment.
3. Notional earnings: GIC rate applied daily, compounding, to the base shortfall for each calendar day from the day after the on-time window ends until the day a late contribution clears the final shortfall to nil, or the day before assessment.
4. Administrative uplift = uplift percentage x (sum of final shortfalls + sum of notional earnings) for the QE day. Default percentage, reduced by the compliance-history reduction (no ATO-initiated assessment or estimate in the 24 months ending on the QE day, ignoring pre-1 Jul 2026 charges) and by a voluntary disclosure reduction that depends on how many calendar days (starting on the QE day) before lodgment.
5. Choice loading = choice loading rate x non-compliant contributions, capped by the limit less earlier choice loadings in the notice period.
6. SGC = sum of the four components; the assessed amount is decreased to the nearest multiple of 5 cents. Deductible. Unpaid SGC attracts GIC and a late payment penalty (not modelled).

## Employee or contractor
- Ordinary meaning: totality of the legal relationship; comprehensive written contract governs unless sham, varied, waived or subject to a remedy (TR 2023/4 paras 7-10). Key question: is the worker serving in the engager's business? Indicators: control, integration and presentation, delegation, basis of payment (time vs result), tools and equipment, risk, goodwill. Labels and ABN are not determinative.
- SG extended meaning (SGAA s12(3); TR 2023/4 Appendix 2): an individual working under a contract wholly or principally for their labour is an employee for SG. Indicators: paid for hours or labour rather than a result, must do the work personally, labour is more than half the contract value. Does not apply where the contract is with a company, trust or partnership.
- Fair Work Act s15AA (from 26 Aug 2024): whole-of-relationship test including how the contract is performed in practice; can give a different answer from tax and SG.
- Sham contracting (FW Act ss357-359) and disputes: AU-PAY-001.

## STP Phase 2
- Report each pay event on or before payday; closely held payees of small employers (19 or fewer) may be reported quarterly.
- Finalisation declaration by 14 July; closely held payees by 30 September (employers with 20 or more employees or mixed payees) or the payee's return due date (small employers with only closely held payees).
- Correct errors within 14 days of detection (or by the next pay event if the pay cycle is longer).

## Refusal codes and messages (quote verbatim)

- **AU-PAY-001** (employment lawyer or registered tax agent). Trigger: Worker status is disputed, a worker or regulator alleges sham contracting (Fair Work Act 2009 ss357-359), or the employer wants a definitive employee/contractor ruling where facts conflict.
  Message: "Whether this worker is an employee or a contractor is disputed or may involve sham contracting. I can list the indicators, but the decision needs an employment lawyer or registered tax agent (or an ATO private ruling for tax and super)."
- **AU-PAY-002** (Fair Work Ombudsman or employment lawyer). Trigger: Question turns on interpreting a modern award or enterprise agreement - classification, minimum rates, penalty rates, overtime, allowances, loadings or leave entitlements under an industrial instrument.
  Message: "This depends on how a modern award or enterprise agreement applies, which I don't interpret. Check the award with the Fair Work Ombudsman (fairwork.gov.au, Pay Calculator) or an employment lawyer before paying."
- **AU-PAY-003** (registered tax agent). Trigger: Termination payments - employment termination payments, genuine redundancy or early retirement scheme payments, unused annual or long service leave paid on termination (Schedules 7 and 11), or death benefit ETPs.
  Message: "Termination payments (ETPs, redundancy and unused leave on termination) have their own caps, tax-free parts and withholding schedules that this skill does not calculate. A registered tax agent or payroll specialist should prepare them."
- **AU-PAY-004** (state-taxes-sa skill or state revenue office). Trigger: State or territory payroll tax - thresholds, grouping, contractor (relevant contract) provisions, registration or returns.
  Message: "Payroll tax is a state tax outside this skill. Use the state-taxes-sa skill for South Australia, or the relevant state revenue office."
- **AU-PAY-005** (fbt skill or registered tax agent). Trigger: Fringe benefits tax - car benefits, salary packaging of non-cash benefits, reportable fringe benefits amounts, FBT returns.
  Message: "Fringe benefits tax is outside this skill. Use the fbt skill; reportable fringe benefits amounts over the reporting threshold are then reported through STP."
- **AU-PAY-006** (ATO tax withheld calculator or registered tax agent). Trigger: Withholding needs a schedule or adjustment other than the regular Schedule 1 formulas - working holiday makers (Schedule 15), seniors and pensioners (Schedule 9), horticulture or shearing, entertainers, daily or casual table, back payments, bonuses and commissions paid as lump sums (Schedule 5), Medicare levy variation for spouse or dependants, 53/27-pay top-ups, voluntary or increased withholding agreements, or a 2025-26 study loan component before 24 Sep 2025.
  Message: "This payment needs a different ATO withholding schedule or adjustment than the regular Schedule 1 formulas I apply. Use the ATO tax withheld calculator or the specific schedule, or ask a registered tax agent."
- **AU-PAY-007** (registered tax agent or lawyer). Trigger: SG charge question beyond estimating components - objections or amendments, remission, the late payment penalty or Part 7 penalty, director penalty notices, exceptional circumstances determinations, or partly paid or choice-liability quarters under the pre-1 July 2026 SGC.
  Message: "This SG charge question involves penalties, objections, director penalties or a partly paid pre-July 2026 quarter that I can't settle. Use the ATO SGC statement and calculator tool and get a registered tax agent (or lawyer for director penalties) involved."
- **AU-PAY-008** (registered tax agent). Trigger: Request falls outside the modelled period or regime - dates outside the stated income year, mixing the quarterly SG regime (to 30 June 2026) with Payday Super QE days, or special super guarantee cases (defined benefit funds, certificates of coverage for foreign employees, SG opt-out for high-income employees with multiple employers, exemption certificates).
  Message: "This falls outside the period or super guarantee regime I can calculate for the stated income year (or is a special SG case). Split the question by income year, or have a registered tax agent confirm the special case."
- **AU-PAY-009** (BAS agent or registered tax agent). Trigger: Taxable payments annual report (TPAR) - whether contractor payments for cleaning, courier, building, IT, security or road freight services must be reported, and preparing the report.
  Message: "Taxable payments annual reporting for contractors is outside this skill. A BAS agent or registered tax agent should confirm whether a TPAR is due (by 28 August) and prepare it."
- **AU-GEN-001** (preparer). Trigger: a required figure has a value but is not VERIFIED and draft use was not requested (a draft is available).
- **AU-GEN-003** (preparer). Trigger: a required figure has no published value for that year (no rates file, key absent, or null), so no draft is possible.
  Message: "I can't compute this reliably: a required figure for that income year is not yet verified. I can produce a clearly marked draft, or you can confirm the figure from ato.gov.au."
- **AU-GEN-002** (registered tax agent or BAS agent). Trigger: User asks to lodge, submit or pay on their or a client's behalf.
  Message: "I prepare working papers only. Lodgment must be done by the taxpayer or a registered agent through ATO online services."
