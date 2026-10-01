# Rules and edge cases: state-taxes-sa

## Payroll tax (Payroll Tax Act 2009 (SA) Sch 1 and Sch 2)
- Tested wages: this employer's SA taxable wages plus interstate wages (a group tests the group total). At or below the threshold pro-rated by days employing over days in the year, nothing is payable.
- Annualised wages: tested wages times days in the year over days employing. Above the top of the variable band the top rate applies. Inside the band the rate is the top rate times (annualised wages minus threshold) over the band width.
- Deduction: the maximum annual deduction times SA wages over total Australian wages times days employing over days in the year. Monthly return: one twelfth of that. Flat, not tapered by wages. Non-designated group members get none; the designated group employer claims the group's deduction using the group's SA share, and any unused part can be allocated to members at the annual reconciliation.
- Tax: (SA wages for the period minus deduction, not below nil) times the rate. If the deduction is at least the wages for the month, nothing is payable that month.
- RevenueSA worked examples truncate the variable rate to two decimal places of a percent for monthly returns; the Act's formula has no rounding. Sch 2 cl 21 says cents are disregarded in formula calculations; treat cents as indicative.
- Business days: RevenueSA moves a payroll tax date that falls on a weekend or an SA public holiday to the next business day (Public Holidays Act 2023 (SA) s 8; Legislation Interpretation Act 2021 (SA) s 44(2)). Only SA public holidays count, and part-day holidays (Christmas Eve, New Year's Eve) do not; other States' holidays do not move SA state tax dates, unlike ATO dates. RevenueSA publishes an extension for the December return over Christmas and New Year; the tool uses the published date where the rates file has one and warns where it has none. Land tax: RevenueSA and the Acts give no roll rule, so the tool shows the assessment date and the next business day under Public Holidays Act 2023 (SA) s 8(2) only as a labelled assumption.
- Dates: monthly return and payment by the seventh day after month end. RevenueSA publishes the annual reconciliation due date and includes June in it; the Act (s 9(1)(b)) puts June tax on the July day in `state.sa.payroll_tax_june_payment_due_day_act`. Use RevenueSA's published date and mention the statute.
- Wages: the tool does not decide what is wages. Wages taxable in SA follow the nexus rules in s 11 (services performed wholly in SA, or based in SA where work spans jurisdictions). Wages for services wholly performed overseas for over six months can be exempt (s 66A).

## Land tax
- Base: total taxable site value of all land under the same ownership at midnight on 30 June before the year. Scale: fixed base for the band plus a rate for each hundred dollars or part of a hundred above the band's lower bound. Exempt land is excluded.
- Minimum assessment: no assessment where calculated tax is under the minimum amount.
- Principal place of residence: owned and occupied by a natural person on an ongoing basis at 30 June, buildings predominantly residential. Business use under the lower limit of floor area: full exemption. Between the limits: taxable value reduced in steps by business share. Above the upper limit: no exemption.
- Primary production: at least the minimum area, used wholly or mainly for a business of primary production; land inside the defined rural area also needs the owner-based conditions in s 5(10)(g).
- Trust scale: applies to trusts not qualifying for general rates; the first band starts at the trust threshold with a base as printed by RevenueSA, and every base reconciles to the previous base plus rate times band width.
- Foreign owners: no SA land tax surcharge exists in the Act or on RevenueSA pages. The 2017-18 off-the-plan land tax relief was not extended to foreign purchasers.

## Stamp duty
- Base: greater of consideration (including GST) and market value. Scale: base plus rate for each hundred dollars or part of a hundred above the band's lower bound.
- Qualifying land: non-residential, non-primary-production land (by land use code) has no duty on instruments from 1 July 2018 arising from later contracts; hotels and motels count as qualifying.
- First home buyer relief: contracts from the start date, full relief, new home, off-the-plan apartment or vacant land to build on; purchasers and spouses have no prior relevant interest; six continuous months residence within the window (12 months of settlement for a new home; for vacant land the earlier of 12 months from lawful occupation and 36 months from settlement); repay duty if the conditions fail. Not applied to the foreign ownership surcharge.
- Foreign ownership surcharge: residential land, a foreign person's share of the value, from instruments on or after 1 January 2018; joint tenants are treated as equal tenants in common; payable with the duty.
- Not modelled: landholder duty, unit trusts, partnership transfers, exempt family or reconstruction transfers, downsizer relief.
