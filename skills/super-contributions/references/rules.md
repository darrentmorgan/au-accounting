# Calculation order and edge cases: super-contributions

All amounts come from the tools; this file explains the order the tools follow so answers can be explained.

## concessional_cap_position
1. Total concessional contributions = employer (incl. SG) + salary sacrifice + personal deductible (only with a valid, acknowledged notice of intent) + other.
2. If the total exceeds the general concessional cap and TSB at the prior 30 June is below `super.carry_forward_tsb_limit`, apply unapplied unused amounts from the previous five years, earliest first, only as far as needed.
3. Excess = total less the increased cap. Excess is assessable, gets the offset at `super.excess_concessional_offset_rate`, may be released (up to `super.excess_concessional_release_divisor` of it), and if not released counts as non-concessional.
4. Unused cap this year (general cap less total, if positive) is carried forward; the oldest year in the window expires at year end.
5. Replay mode (`prior_years`): the tool rebuilds the unused amounts from 2018-19 on; a year whose contributions exceeded its cap needs that year's prior-30-June TSB. Earlier years not given are assumed to have left nothing used later.

## bring_forward_nonconcessional
1. Existing period (triggered in one of the two previous years and still running): cap = period length x trigger-year annual cap, less contributions already made in the period; nil if TSB at the prior 30 June is at or above the general transfer balance cap.
2. Otherwise nil if TSB at the prior 30 June is at or above the general transfer balance cap.
3. Otherwise cap space = general transfer balance cap less TSB. Under 75 at any time in the year and cap space above the annual cap: a period can be triggered (two years if cap space is not more than twice the annual cap, three otherwise). The period starts only if contributions exceed the annual cap.
4. Anything above the applicable cap is an excess non-concessional contribution; the release-or-tax election is escalated (AU-SUPER-003).

## div293_tax
Income = taxable income + reportable fringe benefits + total net investment loss (less any s301-20(3) amount). Low tax contributions = concessional contributions less excess concessional contributions. Taxable contributions = lesser of low tax contributions and (income + low tax contributions less the threshold). Tax = taxable contributions x the Div 293 rate.

## div296_tax
1. Not in force before 2026-27.
2. Exemptions: child recipient of an income stream, structured settlement contribution, death during 2026-27.
3. Reference TSB: 2026-27 closing TSB only; later years the greater of opening and closing (closing is nil after death).
4. Percentages above the large and very large balance thresholds, each rounded to two decimal places, half up.
5. Taxable super earnings = total super earnings x percentage above the large balance threshold (nil if earnings are not above nil). Very large component = total earnings x percentage above the very large threshold.
6. Tax = taxable super earnings x lower rate + very large component x additional rate.
7. Earnings of excluded interests (judges' pensions and similar) are nil but their value still counts in TSB.

## co_contribution and low_income_super_tax_offset
- Total income = assessable income + reportable fringe benefits + reportable employer super (less excess concessional contributions), less business deductions (not for the ten per cent test).
- Co-contribution = lesser of matched amount and the tapered maximum; minimum payment applies; rounded up to the nearest five cents.
- LISTO = concessional contributions x the LISTO rate, capped at the maximum, floor at the LISTO minimum.

## spouse_offset
Offset = spouse offset rate x lesser of (maximum contribution base less spouse income above the reduction threshold) and contributions made; capped at the maximum offset; nil at or above the cut-out.

## downsizer_contribution
Limit = lesser of (per-person cap less earlier downsizer contributions) and (capital proceeds less other downsizer contributions from the same sale). Any amount above the limit is an ordinary non-concessional contribution.

## Edge cases
- A personal contribution with no notice of intent is non-concessional: check both caps.
- Contributions made in the last days of June count in the year received by the fund.
- For a member aged 74 on 1 July the bring forward is still available that year (under 75 at some time in it).
- TSB for carry forward and the NCC cap is at the prior 30 June; for Division 296 in 2026-27 it is the closing TSB.
