---
name: payroll-sg
description: 'Works out Australian employer payroll obligations for 2025-26 and 2026-27 - PAYG tax to withhold from wages (ATO Schedule 1, tax-free threshold, no TFN, HELP, no-ABN supplier withholding), super guarantee on each pay run under Payday Super from 1 July 2026 (qualifying earnings, the business-day receipt deadline, maximum contribution base) or quarterly before, the super guarantee charge for late super, STP timing, minimum wage, and employee vs contractor. Use when someone asks "how much tax do I withhold from my employee''s pay", "PAYG on a fortnightly wage", "staff didn''t give a TFN", "subbie has no ABN", "how much super for my casual staff", "is super still quarterly", "super on overtime or salary sacrifice", "I paid super late", "is my cleaner a contractor", "super for a contractor with an ABN". Also use for sham contracting disputes, award pay rates, redundancy or termination payments, payroll tax and fringe benefits on staff: the skill decides scope and escalates.'
---

# Payroll and super guarantee (employer obligations)

Employer-side payroll for one Australian income year: PAYG withholding, super guarantee (SG), SG charge (SGC), STP timing and worker status. All arithmetic goes through the calculator tools; never compute withholding or SG yourself and never quote a rate, threshold, cap or wage from memory. Every figure comes from a tool's `figures_used` or from `get_figure`.

## Scope

In scope:
- PAYG withholding from regular weekly, fortnightly, monthly or quarterly pay (TAA 1953 Sch 1 s12-35; Schedule 1 statement of formulas NAT 1004), including no-TFN withholding (scale 4), foreign residents, Medicare full or half exemption, tax offsets on a Withholding declaration, and the Schedule 8 study and training support loan component (HELP, VSL, SSL, AASL). Tool: `payg_withholding`.
- No-ABN withholding from payments to suppliers (TAA 1953 Sch 1 s12-190). Tool: `no_abn_withholding`.
- Super guarantee: Payday Super for qualifying earnings paid from 1 Jul 2026; quarterly OTE regime for quarters to 30 Jun 2026. Tool: `super_guarantee`.
- SG charge estimates under both regimes. Tool: `sg_charge_estimate`.
- Employee vs contractor indicators for PAYG and SG, including the SG extended definition. Tool: `worker_status_indicators`.
- STP Phase 2 obligations, national minimum wage (figure `payroll_wages.national_minimum_wage_hourly`), SG eligibility rules.

Out of scope (escalate, see Escalation): sham contracting disputes, award or enterprise agreement interpretation, termination payments, payroll tax, FBT, TPAR, withholding schedules other than Schedule 1 and 8, SGC penalties and objections, special SG cases.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year and pay date.** PAYG schedules and the SG regime are date-effective: payments made 1 Jul 2025 to 30 Jun 2026 use income year `2025-26`; payments from 1 Jul 2026 use `2026-27`. The SG regime follows the day earnings are paid, not the period worked. "This year" or "now" is ambiguous; confirm the pay date.
2. **PAYG**: gross pay for the period (including taxable allowances), pay period, whether a TFN was quoted, residency, tax-free threshold claimed with this employer, Medicare levy variation, study loan debt, offsets on a Withholding declaration.
3. **SG**: each pay date and the split of the pay into ordinary time earnings (including paid leave, casual loading, shift penalties, ordinary-hours bonuses and commissions), commissions for work entirely outside ordinary hours, salary-sacrificed amounts, overtime, and other excluded amounts; earnings already paid this year (maximum contribution base); whether it is the first contribution for a new employee or to a new fund. Public holidays come from the public holiday data; ask for `public_holidays` only to override it.
4. **SGC**: QE day (or quarter for 2025-26), each employee's earnings, contributions received on time, late contributions with the date the fund received them, choice of fund failures, voluntary disclosure date, ATO-initiated SGC assessments in the prior 24 months, assessment date if known.
5. **Worker status**: the written contract terms first, then control, delegation, basis of payment, tools, risk, goodwill, presentation, and whether the contract is principally for the person's labour; whether the worker is an individual or an entity.

## Procedure

1. Confirm the income year from the pay date. If the user describes paying super "quarterly" for pay dates from 1 Jul 2026, correct it: Payday Super applies (see Judgement rules).
2. Call the tool with `income_year` and `inputs`:
   - `payg_withholding`: `{"gross_earnings": <amount>, "period": "fortnightly", "tfn_provided": true, "residency": "resident", "tax_free_threshold_claimed": true, "medicare_exemption": "none", "study_loan_debt": false, "withholding_declaration_offsets": 0, "payment_date": "YYYY-MM-DD", "special_circumstances": []}`.
   - `no_abn_withholding`: `{"payment_ex_gst": <amount>, "abn_quoted": false, "exception": "none", "worker_may_be_employee": false}`.
   - `super_guarantee`: `{"payments": [{"pay_date": "YYYY-MM-DD", "ordinary_time_earnings": <amount>, "commissions_outside_ordinary_hours": 0, "salary_sacrificed_ote": 0, "overtime": 0, "other_excluded": 0}], "ytd_base_before": 0, "first_contribution_new_employee": false, "first_contribution_new_fund": false, "public_holidays": []}`.
   - `sg_charge_estimate` (2026-27): `{"qe_day": "YYYY-MM-DD", "calculation_date": "YYYY-MM-DD", "employees": [{"name": "...", "qualifying_earnings": <amount>, "on_time_contributions": 0, "late_contributions": [{"amount": <amount>, "received": "YYYY-MM-DD"}], "non_choice_compliant_contributions": 0}], "vds_lodged": null, "commissioner_assessment_in_prior_24_months": false}`. For 2025-26 give `quarter_end` instead of `qe_day`, salary or wages (including overtime) as `qualifying_earnings`, and `sgc_statement_lodged`.
   - `worker_status_indicators`: `{"worker_is_individual": true, "right_to_control_how_work_done": "yes|no|unknown", "must_perform_personally": "...", "paid_by_time": "...", "paid_for_result": "...", "provides_significant_tools_equipment": "...", "bears_commercial_risk": "...", "builds_own_goodwill": "...", "presents_as_part_of_engager_business": "...", "contract_principally_for_labour": "...", "has_abn": true, "labelled_contractor": true}`.
3. Special payees (working holiday makers, seniors, daily or casual table, back pay or bonus lump sums, termination payments, Medicare levy family adjustments): pass them in `special_circumstances`; the tool refuses with AU-PAY-006.
4. Read the envelope:
   - `exit_code` 0: present the result (Output below). Quote amounts exactly as returned.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, offer what can still be done.
   - `exit_code` 4 with AU-GEN-001: a figure is not verified; quote the message and offer a draft only if the user wants one. With AU-GEN-003: a figure (often a future GIC rate) is not yet published, so no draft is possible. Quote the message. For SGC you may rerun with `gic_annual_rate_override` only if the user accepts a clearly labelled estimate.
   - `exit_code` 2: fix the input and call again.
5. For the minimum wage or other single figures, call `get_figure` (e.g. `payroll_wages.national_minimum_wage_hourly`, `super.sg_rate`, `super.max_contribution_base_annual`, `super.max_contribution_base_per_quarter`).
6. For worker status, present the indicators and the lean; never state a definitive answer where the tool reports mixed or insufficient facts.

## Judgement rules

- **Payday Super (from 1 Jul 2026).** SG is the SG rate times qualifying earnings (SGAA s10A, s17A) for each QE day (the day pay leaves the employer's account). The fund must receive the contribution, allocable, within the usual period after the QE day (`super.payday_super_usual_period_business_days` business days; `super.payday_super_first_contribution_business_days` business days for a first contribution to a new employee or a new fund). Business days exclude weekends and a public holiday for the whole of any state, the ACT or the NT, wherever the employer is (SGAA s6(1); LCR 2026/3 para 4); the tool reads them from the public holiday data (a date outside it is refused, AU-GEN-004), and `public_holidays` is an override only. Paying a clearing house is not receipt. Quarterly due dates no longer apply to earnings paid from 1 Jul 2026; the last quarterly SG (April to June 2026 quarter) was due 28 Jul 2026. The Small Business Superannuation Clearing House closed on 30 Jun 2026 (new users from 1 Oct 2025).
- **Qualifying earnings vs OTE.** Qualifying earnings include all OTE, all commissions (even for work outside ordinary hours) and salary-sacrificed amounts that would otherwise be OTE. Overtime is excluded. SGR 2009/2 was withdrawn from 1 Jul 2026; its OTE views continue through draft LCR 2026/D1. Before 1 Jul 2026 the base was OTE per quarter.
- **Salary sacrifice.** Sacrificed amounts that would otherwise be OTE stay in the SG base (qualifying earnings, SGAA s10A; the same result applied from 1 Jan 2020 under the earlier salary sacrifice rules) and sacrificed contributions do not count towards the employer's SG.
- **Maximum contribution base.** From 2026-27 an annual amount per employer (`super.max_contribution_base_annual`); before, a quarterly amount (`super.max_contribution_base_per_quarter`).
- **SG rate.** Use `super.sg_rate` for the year. Do not use an earlier year's rate for a pay date in 2025-26 or 2026-27.
- **SG eligibility.** No minimum monthly earnings threshold. Under-18s and private or domestic workers need SG only for weeks they work more than 30 hours (SGAA s12(11) for domestic work; under-18 part-time exclusion).
- **SGC under Payday Super.** Assessed by the ATO per QE day; components are the individual final shortfall, notional earnings at the GIC compounded daily, the administrative uplift (reduced for clean history and prompt voluntary disclosure) and choice loading (capped per notice period). Tax deductible. Late contributions reduce the shortfall but not notional earnings or the uplift. Pre-1 Jul 2026 SGC (statement lodged by the employer; nominal interest; administration fee) is not deductible.
- **PAYG withholding.** Scale 4 (no TFN) applies when no TFN is quoted and no exemption applies; foreign residents use scale 3 with no tax-free threshold. Only one employer should have the tax-free threshold claimed. Working holiday makers need Schedule 15 (AU-PAY-006). Study loan component comes from Schedule 8 and is added to the Schedule 1 amount.
- **No-ABN withholding.** Withhold at the top rate from the whole payment if no ABN is quoted and the payment exceeds the small-payment threshold, unless an exception applies (Statement by a supplier). Report at BAS label W4.
- **Employee vs contractor.** For tax and SG the legal rights in a comprehensive written contract govern (CFMMEU v Personnel Contracting [2022] HCA 1; ZG Operations v Jamsek [2022] HCA 2; TR 2023/4). Labels and ABNs do not decide it. For SG an individual on a contract wholly or principally for their labour is an employee (SGAA s12(3); TR 2023/4 Appendix 2, which replaced SGR 2005/1). For Fair Work purposes FW Act s15AA (from 26 Aug 2024) looks at the real substance and practical reality, so the answer can differ.
- **STP Phase 2.** Report each pay event on or before payday, including qualifying earnings and super liability from 1 Jul 2026. Finalisation declaration by 14 July; closely held payees by 30 September (or the payee's return due date for small employers with only closely held payees). Correct errors within 14 days of detection.
- **Minimum wage.** Award/agreement-free adults get at least `payroll_wages.national_minimum_wage_hourly` (from 1 Jul 2026 for 2026-27); casuals add `payroll_wages.casual_loading`. Awards set their own rates (AU-PAY-002).

## Escalation

| Trigger | Code |
|---|---|
| Worker status disputed, sham contracting allegation, or a definitive ruling sought where facts conflict | AU-PAY-001 |
| Modern award or enterprise agreement interpretation (classification, rates, penalties, allowances) | AU-PAY-002 |
| ETPs, redundancy, unused leave on termination | AU-PAY-003 |
| Payroll tax (state) | AU-PAY-004 |
| Fringe benefits tax | AU-PAY-005 |
| Withholding outside the regular Schedule 1 and 8 formulas | AU-PAY-006 |
| SGC objections, penalties, director penalties, partly paid pre-2026 quarters | AU-PAY-007 |
| Dates outside the income year, mixed SG regimes, special SG cases | AU-PAY-008 |
| Taxable payments annual report (TPAR) | AU-PAY-009 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| A due date or business-day count is outside the public holiday data | AU-GEN-004 |
| Asked to lodge, report or pay (STP, SGC, BAS) | AU-GEN-002 |

Surface the code and its message exactly as written in the refusal (the tool returns it; for triggers the tools do not see, quote from `references/rules.md`), then stop the affected work and continue with anything still in scope.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year and pay date: amounts to withhold (with scale), SG per payday with due dates (or per quarter), SGC components, worker status lean and s12(3) result, as applicable.
2. **Figures used**: key, value, status, source URL from `figures_used` (group coefficient tables, e.g. "Schedule 1 scale 2 coefficients (VERIFIED)").
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/payroll-sg.yaml` (e.g. RF-PAY-001 contractor misclassification, RF-PAY-002 late Payday Super), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/rules.md` (rules, dates, refusal messages), `references/sources.md` (primary sources).
