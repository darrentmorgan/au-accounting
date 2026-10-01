# Calculation steps and worked checks

Figures are named by key; values come from the rates files. Section references are ITAA 1936 unless stated.

## trust_distribution_shares
1. Net income (s95) nil or negative: no Div 6 shares; the loss stays in the trust (Sch 2F).
2. Adjusted net income (Div 6E) = net income less net capital gain, franked distributions net of directly relevant expenses, and franking credits. Negative means the streaming amounts need rateable reduction: refused (AU-TRUST-008).
3. Adjusted trust income = trust income less the capital gains and franked distributions any beneficiary is specifically entitled to (capital gains only if the deed makes them income).
4. Adjusted Division 6 percentage = beneficiary's present entitlement less their own specific entitlements (that are trust income), over adjusted trust income. The trustee's percentage is what is left.
5. Share of ordinary net income = percentage times adjusted net income.
6. Share of each capital gain and franked distribution = specific entitlement plus percentage times the part nobody is specifically entitled to. The fraction of the gross amount gives the attributable net capital gain (grossed up where the trust applied the discount), the attributable franked distribution (net of expenses) and the franking credit share.
7. Trustee's s99A amount = trustee's percentage applied the same way. Tax = amount times `trusts.s99a_rate`, plus `medicare.levy_rate`.
8. No resolution by 30 June: every beneficiary's percentage and specific entitlement is nil; the trustee is assessed on everything (subject to any default beneficiary clause, a deed question).

Worked check: ATO Lang Trust example reproduces exactly (see tests).

## div6aa_minor_tax
1. Prescribed person: under 18 on 30 June and not an excepted person (s102AC).
2. Eligible taxable income (ETI) = unearned income less its deductions. At or below `trusts.minor_eti_threshold`, Div 6AA does not apply and ordinary rates cover all income.
3. Above it: other income is taxed at `individual.resident_rates` as if it were the whole taxable income (ITRA Sch 11 cl 1); ETI at `trusts.minor_eti_rate` on the whole amount (cl 2).
4. Phase-in (ITRA s13(2)): while ETI does not exceed the phase-out limit, the ETI tax is capped at the greater of `trusts.minor_phase_in_rate` times the excess over the threshold, and the extra ordinary tax the ETI would cost as the top slice of taxable income. Phase-out limit (s13(10)) = threshold times phase-in rate over (phase-in rate less the top resident rate), rounded down.
5. LITO (`individual.lito`) is worked out on taxable income but only reduces tax on other income (ITAA 1997 s61-115).
6. Medicare levy on taxable income as for any resident individual; not computed when that year's low-income thresholds are not set (warning, not refusal).

## partnership_shares
1. Net income = assessable income less deductions, adding back partner salaries or interest on capital that were expensed.
2. Positive net income: salaries and interest on capital first, to the extent of net income (pro rata between partners if short); residual shared in profit ratios. Unfunded salary = drawings in advance of future profits.
3. Nil or loss: salaries ignored (cannot create or increase a loss); loss shared in loss ratios (default profit ratios).

Worked checks: TR 2005/7 Examples 1, 2 and 3 reproduce exactly (see tests).
