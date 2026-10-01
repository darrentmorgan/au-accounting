---
name: state-taxes-sa
description: 'Calculates South Australian state taxes for 2025-26 and 2026-27: payroll tax (threshold, variable rate band, grouping, interstate wages, part-year employers, monthly returns and annual reconciliation), land tax (general and trust scales, principal place of residence and primary production exemptions) and stamp duty on property transfers (conveyance scale, first home buyer relief, foreign ownership surcharge, non-residential land). Use when someone asks "do I have to pay payroll tax in SA", "SA payroll tax on my wages", "land tax on my Adelaide investment property", "stamp duty on a house in South Australia", "first home buyer stamp duty SA", "foreign buyer surcharge SA", "duty on a commercial property in SA". Also use for other states'' payroll tax, land tax or duty, downsizer stamp duty relief, trusts, landholder duty, contractor payroll tax and grouping disputes: the skill decides scope and escalates.'
---

# South Australian state taxes (payroll tax, land tax, stamp duty)

Computes South Australian payroll tax, land tax and transfer stamp duty through the tools `sa_payroll_tax`, `sa_land_tax` and `sa_stamp_duty_transfer`. Never do the arithmetic yourself and never quote a rate, threshold or date from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope (South Australia only):
- Payroll tax on SA taxable wages: threshold on Australian wages, variable rate band, top rate, flat deduction adjusted for part-year employing, interstate wages and group membership, monthly returns and the annual reconciliation (Payroll Tax Act 2009 (SA) Sch 1 and Sch 2).
- Land tax for the financial year: general scale or trust scale on total taxable site value at midnight on 30 June before the year, principal place of residence exemption (full and stepped partial), primary production exemption as stated, minimum assessment (Land Tax Act 1936 (SA)).
- Stamp duty on a transfer of land: conveyance scale, nil duty on qualifying non-residential land, first home buyer relief for a new home, off-the-plan apartment or vacant land (contracts from the relief start date), foreign ownership surcharge (Stamp Duties Act 1923 (SA)).

Out of scope (refuse or escalate, see Escalation): every other state or territory (AU-SA-001); who counts as an employee or what counts as wages; grouping determinations; contractor and relevant-contract determinations; land tax objections, waivers and reconstruction exemptions; land held on trust with designated beneficiaries, corporate group aggregation, deceased estates, unit trusts and landholder duty; seniors downsizing stamp duty relief; Land Services SA registration and transfer fees; emergency services levy; other SA duties (insurance, vehicles).

Other states: say the tool only covers South Australia and give no figures from memory. If the user only wants another state's headline threshold, use `get_figure` on the base rates keys for that state and label the status it returns (several are not fully verified); do not calculate.

## Required inputs

1. **Which tax and which financial year** (`2025-26` or `2026-27`; land tax is levied for the financial year). If unclear, ask; never assume the current year.
2. Payroll tax: SA taxable wages for the period, whether the return is annual or monthly, the annual SA wages estimate (monthly returns), interstate wages for the year, days employing if the employer started or stopped mid-year, and group status with the group's total SA and interstate wages. Ask whether any contractor payments, allowances or fringe benefits are already inside the wages figure.
3. Land tax: site values (not capital values) from the Valuer-General for each parcel, ownership type (general or trust), and for each parcel any exemption claimed (principal place of residence with the share of floor area used for business, or primary production).
4. Stamp duty: dutiable value (greater of price including GST and market value), property type (residential, primary production, or qualifying non-residential), contract date, first home buyer status for a new home, foreign person status and the share of the interest they acquire.

## Procedure

1. Confirm the tax, the financial year and, for wages, the scope of wages. Exception for stamp duty: if the user has not given a contract date and the date is not needed to choose the scale (no new-home first home buyer claim and no foreign person, for example an established home where the user asks whether relief applies), do not stop to ask. Assume the current income year, say so as an assumption, pass today's date as `contract_date` (it falls after the relief and surcharge start dates in the supported years), run `sa_stamp_duty_transfer`, and give the duty figure together with the relief conclusion. Ask for the actual contract date only when it decides the answer (a claimed new-home relief, a foreign person, or a contract that may pre-date the start dates). If another state is involved, stop and refuse (AU-SA-001).
2. Call the matching tool with `income_year` and `inputs`, for example `income_year: "2026-27"`, `inputs: {"period": "annual", "sa_taxable_wages": <amount>}` for payroll tax; `inputs: {"ownership_type": "general", "total_site_value": <amount>}` for land tax; `inputs: {"dutiable_value": <amount>, "contract_date": "<yyyy-mm-dd>", "property_type": "residential"}` for duty.
   Field names: payroll `state`, `period`, `sa_taxable_wages`, `annual_sa_taxable_wages`, `annual_interstate_wages`, `days_employing`, `group_status`, `group_annual_sa_taxable_wages`, `group_annual_interstate_wages`, `indicative_rate_2dp`, `special_circumstances`; land tax `state`, `ownership_type`, `parcels` (each `site_value`, `exemption`, `business_floor_area_percent`), `total_site_value`, `foreign_owner`, `special_circumstances`; duty `state`, `dutiable_value`, `property_type`, `contract_date`, `first_home_buyer_new_home`, `foreign_person`, `foreign_interest_percent`, `seniors_downsizing_relief_claimed`, `special_circumstances`.
3. Read the envelope:
   - `exit_code` 0: present the result (Output below).
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, and say what can still be done.
   - `exit_code` 4 (AU-GEN-001): a figure for that year is not verified; quote the message. Do not use a figure from memory. AU-GEN-003 (also exit 4): the figure has no published value for that year, so no draft is possible; quote the message and stop that part.
   - `exit_code` 2: fix the input and call again.
4. For monthly payroll returns, the tool needs the annual SA wages estimate that was declared for the year. The default rate is the exact statutory formula. RevenueSA's own worked examples truncate the variable rate for monthly returns; if the user is checking a RevenueSA Online figure, rerun with `indicative_rate_2dp` and say which basis each number uses.
5. Give the due dates from the tool's `due_dates` block (pass `wages_month` as YYYY-MM with the monthly period to get that month's return date; the reconciliation date is always returned) and the `due` block for the statutory June payment date in the Act. Dates roll to the next business day under the SA rule (Saturday, Sunday or an SA public holiday only; Public Holidays Act 2023 (SA) s 8), with the reason in `business_day_roll`; other States' holidays do not apply to RevenueSA. If `published_extension` is true, RevenueSA's published December extension replaced the ordinary date. Say that RevenueSA's published reconciliation date is the one to work to. For land tax pass `assessment_due_date` from the assessment notice: quote it as the due date and give any rolled date only as the labelled assumption in the tool's `assumptions`, because RevenueSA states no rule.
6. Quote the tool's numbers as returned, in dollars and cents.

## Judgement rules

- Payroll tax threshold and rate are tested on annualised Australian wages (SA plus interstate, or the whole group's), never on SA wages alone. The deduction is flat and is not tapered by wages; it shrinks only for part-year employing, interstate wages and group membership. The variable rate is the rate that applies between the threshold and the top of the band, on wages after the deduction.
- Grouping (common employees, common control, tracing of interests) makes related businesses share one threshold and one deduction, claimed only by the designated group employer. If grouping is contested or unclear, do not decide it: refuse AU-SA-002.
- Payments to contractors under relevant contracts, and agency arrangements, can be taxable wages even where the worker is not an employee (Payroll Tax Act 2009 (SA) Part 4). Short-stay and cleaning contractors are a common exposure. The tool takes wages as given; if contractor status needs a determination, refuse AU-SA-002 and tell the user which payments are in doubt.
- Monthly returns use estimated annual figures; the annual reconciliation trues up. Under-estimating annual Australian wages causes a shortfall and possible interest or penalty tax.
- Land tax is fixed by ownership and use at midnight on 30 June before the year. A later sale does not move liability to the buyer for that year. Exempt land is left out of the aggregation. A person has only one principal place of residence; a holiday house or an investment property is taxable.
- Land tax uses site value, not capital value. If the user only has a capital value or a sale price, ask for the Valuer-General's site value.
- SA has no foreign owner land tax surcharge (Land Tax Act 1936 (SA) contains none; see references). SA does have a stamp duty foreign ownership surcharge on residential land. Do not mix them.
- Trust land: the trust scale applies to trusts not qualifying for general rates (for example discretionary trust land acquired after 16 October 2019, or fixed and unit trusts with no notified beneficiaries or unitholders). Trustees must notify RevenueSA within one month of acquiring land on trust. Designated beneficiary cases and corporate groups are escalated (AU-SA-004).
- Stamp duty: the value is the greater of consideration and market value. Qualifying non-residential land (commercial, industrial, hotel and motel land use codes) has no duty for instruments from 1 July 2018 when the contract also post-dates that day; residential and primary production land stay dutiable. RevenueSA relies on Valuer-General land use codes and can treat some land coded residential as commercial in nature, so how short-term letting is classified is not settled here (AU-SS-003): never say it does or does not change the duty.
- First home buyer relief for contracts from the relief start date is full relief with no value cap, for a new home, off-the-plan apartment or vacant land to build on, not established homes. Purchasers and their spouses must not have held a relevant interest in residential property, and must meet the residence requirement or the relief is clawed back. It does not reduce the foreign ownership surcharge. Contracts before the start date had different caps: the tool refuses (AU-SA-006).
- Seniors downsizing relief has been announced for contracts from 25 March 2026 but the start date, caps and conditions could not be verified on the RevenueSA page: refuse AU-SA-005 and point to RevenueSA. Do not quote its limits.
- The off-the-plan concessional duty under Stamp Duties Act 1923 (SA) s 71DB applied to contracts up to 30 June 2017; no general off-the-plan concession is modelled. First home buyer relief covers off-the-plan apartments.
- Short-stay operators (a register, its fee or start date, any short-stay duty or levy, or how duty treats short-stay use): not settled on the primary pages read. Open with AU-SS-003 quoted verbatim from `data/refusals/short-stay-accommodation.yaml`, and do not say whether a register, fee, levy or short-stay duty rule exists or applies. Point to RevenueSA and the SA Government. A general residential duty figure may follow only if it is labelled as not covering any short-stay classification, which is unverified; never lead with the figure.

## Escalation

| Trigger | Code |
|---|---|
| Payroll tax, land tax or duty for a state other than SA | AU-SA-001 |
| Grouping disputed or unclear; contractor, relevant-contract or agency determination needed | AU-SA-002 |
| Land tax exemption disputed, objection, waiver or ex gratia relief; corporate reconstruction exemption | AU-SA-003 |
| Trust designated beneficiary, unit trust or landholder duty, partnership land, corporate group aggregation, deceased estate, family or reconstruction transfer | AU-SA-004 |
| Seniors downsizing stamp duty relief | AU-SA-005 |
| Transfer dated before the supported start, or first home buyer relief on an earlier contract | AU-SA-006 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| A due date is outside the public holiday data (1 July 2025 to 30 June 2028 at the last data update) | AU-GEN-004 (whole tool for a due-date lookup; for `sa_payroll_tax` and `sa_land_tax` the tax is still returned and the date is listed in `field_refusals`, unrolled: quote it and do not call the date checked) |
| Asked to lodge, register or pay | AU-GEN-002 |

Surface the code and its message exactly as returned, then stop the affected work.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated financial year: for payroll tax the tested wages, rate band and rate, deduction, tax and due dates; for land tax total, exempt and taxable site value, scale and tax; for duty the duty before relief, relief, duty payable, surcharge and total.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used` (group scales as "conveyance scale (VERIFIED)").
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/state-taxes-sa.yaml` (grouping, contractors, rate estimate, 30 June assessment, trust notification, surcharge, residence requirement, short-stay use), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (formulas and edge cases).
