---
name: fbt
description: 'Works out Australian fringe benefits tax (FBT) for an employer for an FBT year (1 April to 31 March): car fringe benefits (statutory formula and operating cost method), FBT payable with type 1 and type 2 gross-up, reportable fringe benefits amount, employee loans at low or no interest, electric car exemption (with plug-in hybrids and the proposed 1 April 2027 changes, not law), ute and work vehicle exemption, car parking, meal entertainment, minor benefits, and return and payment due dates. Use when someone asks "FBT on a company car", "novated lease FBT", "is my EV exempt from FBT", "do I pay FBT on a ute", "FBT payable", "reportable fringe benefits on the payment summary", "interest-free loan to an employee", "is a small gift exempt from FBT", "FBT due date". Also use for salary packaging in not-for-profit, charity or hospital employers, living-away-from-home allowances, remote area housing, entertainment beyond simple methods, and benefits to shareholder-directors: the skill decides scope and escalates.'
---

# Fringe benefits tax (Australia)

Computes an employer's FBT for one FBT year through the `au-tax` tools. Never do the arithmetic yourself and never quote a rate, threshold or date from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope (tool in brackets):
- Car fringe benefit, statutory formula method (`car_fringe_benefit_statutory`, FBTAA 1986 s 9) and operating cost method (`car_fringe_benefit_operating_cost`, s 10).
- FBT payable from taxable values with type 1 and type 2 gross-up, instalments, return and payment due dates (`fbt_payable`).
- Reportable fringe benefits amount for one employee (`reportable_fringe_benefits_amount`, s 135P and the reporting threshold).
- Loan fringe benefits at the benchmark interest rate, including the otherwise deductible rule (`loan_fringe_benefit`).
- Electric car exemption (s 8A) with plug-in hybrid grandfathering and date-effective treatment (`ev_exemption_check`).
- Ute and work vehicle exemption (s 8(2)) and the ATO safe harbour PCG 2018/3 (`work_vehicle_exemption_check`).
- Car parking fringe benefits (s 39A) (`car_parking_fringe_benefit`).
- Meal entertainment by the 50/50 split or the 12-week register (`meal_entertainment_taxable_value`).
- Minor benefits screen (s 58P, TR 2007/12) (`minor_benefit_screen`).
- Judgement-only (no tool): work-related items exemption (s 58X), relocation, the otherwise deductible rule for expense payments, on-premises and other exempt benefits.

Out of scope (stop and escalate, see Escalation): salary packaging in public benevolent institutions, health promotion charities, hospitals, ambulance services and rebatable not-for-profit employers (exemption and rebate caps); living-away-from-home allowances; remote area and other employer housing; recreation, entertainment facility leasing and salary-packaged meal entertainment; cars under a pre-May-2011 commitment; benefits to people whose employee status is doubtful. Also not covered: superannuation guarantee and payroll tax (use payroll-sg), PAYG withholding, and income tax deductions for the employer.

## FBT year and income year

- The FBT year runs 1 April to 31 March. Label it `FBT2027` for 1 April 2026 to 31 March 2027.
- The tools take `income_year` and use the FBT year that ENDS inside it: `2026-27` means `FBT2027`; `2025-26` means `FBT2026`. State both labels in the answer.
- FBT2028 and later have no published rates in the data. If asked for a later year, the tool refuses with AU-GEN-003 (no draft possible): say so, do not extrapolate. Say what is known to apply from 1 April 2027 (see Law changes) without inventing figures.
- The reportable fringe benefits amount for an FBT year goes on the income statement for the income year that ends the following 30 June (FBT2027 goes on 2026-27).

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.
1. FBT year (or the dates of the benefit) and employer type (standard taxable employer, or a charity, hospital, not-for-profit or government body).
2. The benefit kind and its facts (below), and whether each benefit was provided under a salary packaging arrangement.
3. Whether the employer was entitled to a GST credit on the benefit (type 1) or not (type 2). If unknown, ask; for loans use type 2.
4. Employee contributions (after-tax payments to the employer, or car costs the employee paid and was not reimbursed for).

## Procedure

1. Confirm the FBT year and that nothing out of scope is present. If it is, go to Escalation before any calculation.
2. Value each benefit with the matching tool, passing `income_year` and `inputs`:
   - Cars: ask base value, days available for private use, contributions, and whether a logbook exists. Run `car_fringe_benefit_statutory`; if a logbook and running costs exist run `car_fringe_benefit_operating_cost` as well and use whichever gives the lower taxable value (the operating cost election is due by the return due date).
   - Electric cars: run `ev_exemption_check` first (vehicle type, first held and first used dates, luxury car tax facts, recipient, plug-in hybrid facts). If `exempt` is true pass `ev_exempt: true` to the car tool so the reportable value is still produced.
   - Utes and vans: run `work_vehicle_exemption_check`; if not exempt value it as a car benefit.
   - Loans, parking, meal entertainment and minor benefits: run the matching tool.
3. Add up taxable values by gross-up type and run `fbt_payable` with `type1_taxable_value` and `type2_taxable_value` (or the `benefits` list), `lodgment`, `instalments_paid` and `prior_year_fbt` if known.
4. For each employee whose benefits may exceed the reporting threshold run `reportable_fringe_benefits_amount` (include exempt electric car values); pass the result to the individual-tax skill as `reportable_fringe_benefits` if the employee's tax is being worked out.
5. Read the envelope: `exit_code` 0 present the result; `exit_code` 3 with `refusal` quote the code and message verbatim and stop that part; `exit_code` 4 (AU-GEN-001) a figure is not verified, quote the message; `exit_code` 4 (AU-GEN-003) a figure or the year has no published data, no draft is possible, quote the message; `exit_code` 2 fix the input.
6. Quote the tool's numbers as returned, in dollars and cents.

## Judgement rules

- Garaged at home: a car kept at or near the employee's home is available for private use even if policy forbids private use (FBTAA s 7). Only removing custody and control avoids a car benefit.
- Statutory versus operating cost: the choice is made per car and per FBT year, not once for the fleet or for all years. The employer elects the operating cost method in relation to a particular car for a year of tax (FBTAA 1986 s 10(1)); without an election the statutory formula applies to that car for that year, and a different choice can be made for the same car in a later year or for another car. The operating cost method needs a written election by the return due date, a logbook in a logbook year and deemed depreciation and interest; without records no business use reduction is allowed. Compare both.
- Type 1 versus type 2: type 1 only where the provider is entitled to a GST credit. Do not default to type 1.
- Reportable amount: always grossed up at the lower (type 2) rate whatever the benefit type; the threshold test is on taxable value, so exactly the threshold is not reportable. Exempt electric car benefits are still reportable (s 135P(3)).
- Electric cars: eligibility needs a zero or low emissions car first held and used on or after 1 July 2022, a current employee or associate, and no luxury car tax ever payable, judged at the threshold for the year of first sale. Plug-in hybrids lost eligibility from 1 April 2025 unless already in exempt use and under a financially binding commitment that continues unchanged; delivery delays do not extend the date.
- Utes and vans: exempt only if private use is limited to home to work, incidental work travel and minor, infrequent and irregular use. A school run or regular family use loses it. Dual cabs qualify only if not designed principally to carry passengers.
- Minor benefits: the value test is per benefit and is "less than", but the benefit must also be unreasonable to treat as a fringe benefit. Regular, salary-packaged or associated-benefit-heavy items usually fail. The screen is not a determination.
- Meal entertainment: the 50/50 and 12-week methods tax spend on clients too and switch off other exemptions; compare with the actual method.
- Work-related items (s 58X): exempt when primarily for use in employment and, for portable electronic devices, limited to one item per employee per FBT year of substantially identical function unless the employer is a small business or it is a replacement. State the year: the rule changes for FBT years starting on or after 1 April 2027.
- Otherwise deductible rule: reduces an expense payment or loan benefit by the part the employee could have deducted, needs an employee declaration by the return due date.
- Shareholder-directors and trust directors: whether they are employees and whether the benefit is in respect of employment is fact-specific (SEPL Pty Ltd v Commissioner of Taxation [2026] FCAFC 36). Escalate rather than assume.

## Law changes to state correctly

- Electric car exemption: current law keeps the full exemption for eligible cars. The Budget 2026 proposal to wind it back from 1 April 2027 (a base value limit with a discounted statutory rate above it, then a discount for all eligible cars from 1 April 2029) is an exposure draft only and is NOT law. Never apply it as law; `ev_exemption_check` returns it as information with `proposal_not_law`. Do not attribute it to the Treasury Laws Amendment (Tax Reform No. 1) Act 2026.
- That Act (Schedule 4 Part 2) IS law: for FBT years starting on or after 1 April 2027, salary sacrificed work-related items lose the s 58X exemption and the otherwise deductible rule no longer reduces salary sacrificed expense payment benefits covered by the standard deduction. It does not affect FBT2027.

## Escalation

| Trigger | Code |
|---|---|
| PBI, health promotion charity, hospital, ambulance service, rebatable NFP or salary packaging caps | AU-FBT-001 |
| Living-away-from-home allowance or benefit | AU-FBT-002 |
| Employer housing, remote area housing | AU-FBT-003 |
| Recreation, entertainment facility leasing, salary-packaged meal entertainment, mixed entertainment elections | AU-FBT-004 |
| Car under a pre-10-May-2011 commitment | AU-FBT-005 |
| Doubtful employee status (shareholder-directors, trust beneficiaries, associates) | AU-FBT-006 |
| A figure not verified | AU-GEN-001 |
| Year with no published figures, or a figure with no value | AU-GEN-003 |
| A due date or business-day count is outside the public holiday data | AU-GEN-004 |
| Asked to lodge or pay | AU-GEN-002 |

Pass the trigger in `special_circumstances` or `employer_type` so the tool refuses, then quote the code and message exactly as returned and stop the affected part. Offer what can still be done (for example the standard-employer benefits).

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated FBT year and income year: each benefit's taxable value; gross-up type and grossed-up value; FBT payable; reportable amounts per employee; due dates (self-lodged and agent).
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tools' `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/fbt.yaml` (for example `FBT-YEAR-END`, `FBT-GROSS-UP-TYPE`, `FBT-EV-EXEMPTION-CONDITIONS`), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tools' `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (calculation order and edge cases).
