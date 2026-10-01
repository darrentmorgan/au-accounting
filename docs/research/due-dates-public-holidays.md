# Due dates on weekends and public holidays: rule, jurisdiction, calculator behaviour

Read 2026-09-29 from primary sources only. Data: `data/holidays/au.yaml` (1 Jul 2025 to 30 Jun 2028). Validator: `scripts/validate_holidays.py`. Tests: `tests/data/test_holidays.py`. This brief serves GOAL.md gate 3 (item 12 in section A).

## 1. Bottom line

- If the due date to lodge an approved form or pay a tax debt is not a business day, it is the first business day after. That is law (TAA 1953), not just ATO practice, and the ATO states it for BAS, FBT, tax return lodgment, quarterly super (old regime) and Payday Super.
- Federal "business day" means not a Saturday, not a Sunday, and not a day that is a public holiday for the whole of any State, the ACT or the NT. Where the taxpayer is does not matter. Regional or local days do not count.
- SA state taxes (RevenueSA) use SA public holidays only, and part-day holidays (Christmas Eve, New Year's Eve, 7pm to midnight) do not count.
- The two regimes give different answers on real dates. Example: Mon 7 Jun 2027 is Western Australia Day, so the ATO rolls a due date to Tue 8 Jun, while RevenueSA's own published May 2027 payroll tax due date stays Mon 7 Jun.
- One ATO table row contradicts the statute (section 5). One rule (land tax due dates) has no RevenueSA statement (section 4).

## 2. The rule and where it comes from

| Source | What it says (paraphrased) |
|---|---|
| TAA 1953 s 8AAZMB(1) | Where a tax debt falls due on a day that is not a business day, it is due and payable on the first business day after. GIC is not a "tax debt" for this section (s 8AAZMB(2)). |
| TAA 1953 Sch 1 s 388-52 | Where an approved form is due on a day that is not a business day, it may be given on the first business day after. |
| TAA 1953 s 8AAZMB(2); ITAA 1997 s 995-1(1); SGAA 1992 s 6(1) | Same definition in all three: business day excludes Saturdays, Sundays and any day that is a public holiday for the whole of any State, the ACT or the NT. |
| ATO, Lodgment and payment dates on weekends or public holidays (updated 1 Jul 2026) | Same rule stated for the lodgment program. Public holiday means a day that is a public holiday for the whole of any state or territory, so taxpayers in every jurisdiction move together "even if they don't celebrate that public holiday". Contains a table of holidays and first business days (2026 from 3 Aug, 2027 to 14 Jun). Says dates may change during the year. |
| ATO, Due dates for lodging and paying (updated 2 Mar 2023) | Due on Saturday, Sunday or public holiday: lodge or pay on the first business day after, with no penalty or GIC. |
| ATO, BAS due dates (updated 17 Sep 2026); FBT lodging (10 Sep 2026); Quarterly super due dates (25 Feb 2026, pre-Payday Super) | Same rule for BAS and FBT. The old quarterly super page says the contribution must reach the fund by the next business day. |
| ATO, Payment deadlines for Payday Super (updated 29 Sep 2026); LCR 2026/3 para 4 | Business day as in SGAA s 6(1). A state or territory-wide holiday anywhere is not a business day "even if you are not in that state". A holiday for only part of a state (Royal Hobart Show Day) is still a business day. Worked examples (Picnic Day NT, King's Birthday) are used as tests. |
| Acts Interpretation Act 1901 s 2B, s 36(2) and (3) | Fallback for Commonwealth Acts with no specific rule: a thing due on a Saturday, Sunday or holiday may be done on the next day that is not one. "Holiday" means a public holiday in the place where the thing is to be done (and, for an office, a day it is closed all day). This is place-based, unlike the tax-specific definition. |

Rule hierarchy for the calculators: TAA 1953 provisions decide lodgment and payment dates for anything ATO-administered. The AIA rule only matters for other Commonwealth time limits (for example objection and amendment periods counted in days), which are out of scope for the due-date calculators.

## 3. Which jurisdiction's holidays apply

Decision: two regimes, both in `regimes:` at the top of the data file.

| Regime | Applies to | Non-business day | Part-day holidays |
|---|---|---|---|
| `commonwealth_tax` | Everything the ATO administers | Sat, Sun, or a holiday for the whole of ANY State, the ACT or the NT (all eight jurisdictions pooled) | Count. The ATO table lists Christmas Eve (QLD, NT, SA) and New Year's Eve (NT, SA) as non-business days. The statutory wording ("a day which is a public holiday for the whole of") is ambiguous on part-day holidays, so follow the ATO table. |
| `sa_state_tax` | RevenueSA (payroll tax, land tax) | Sat, Sun, or a public holiday under the Public Holidays Act 2023 (SA) | Do not count (Legislation Interpretation Act 2021 (SA) s 46; Public Holidays Act 2023 (SA) s 8(3)). |

SA sources: Public Holidays Act 2023 (SA) s 3 (fixed days), s 4 (part-day: 7pm to midnight on 24 and 31 December), s 5 (proclaimed extra days), s 8 (obligation to pay or act on a public holiday, bank holiday or Saturday moves to the next day that is not one; Sundays are bank holidays under s 7). Legislation Interpretation Act 2021 (SA) s 4 (business day), s 44(2) (last day not a business day: next business day). RevenueSA says the same for payroll tax: where the 7th falls on a weekend or public holiday it accepts lodgement and payment on the next business day. RevenueSA's published 2026-27 dates reproduce this (tests: 7 Nov 2026 (Sat) to Mon 9 Nov; 7 Mar 2027 (Sun) then Adelaide Cup Day Mon 8 Mar to Tue 9 Mar 2027).

Consequences worth knowing:

- "SA-only holiday" is not a date under the Commonwealth regime. Every whole-day SA holiday in range is also observed by another jurisdiction on the same date (Adelaide Cup Day shares its date with VIC, TAS and ACT; Proclamation Day holiday shares 26 to 28 December with Boxing Day). The SA regime differs the other way: WA Day, Melbourne Cup and other States' days are business days for RevenueSA. Use Adelaide Cup Day (Mon 8 Mar 2027) as the SA regime test and WA Day (Mon 7 Jun 2027) or Melbourne Cup (Tue 3 Nov 2026) as the regime-difference test.
- Payday Super business-day counts (7 or 20 business days) use the Commonwealth regime. Picnic Day (NT) adds a day for every employer in Australia.
- RevenueSA may extend the December return over Christmas and New Year. Its 2026-27 table shows the December 2026 return due Thu 14 Jan 2027, not Thu 7 Jan. Treat 14 Jan 2027 as a published extension, not a roll. RevenueSA has published no 2027-28 table yet.

## 4. Uncertainty recorded

- Land tax: RevenueSA's payment pages say to pay by the due date on the assessment and say nothing about weekends or holidays. Land Tax Act 1936 (SA) and Taxation Administration Act 1996 (SA) have no roll provision (searched the current versions). Public Holidays Act 2023 (SA) s 8(2) probably rolls it, but RevenueSA has not said so. Recommend: use the assessment date, show the s 8(2) roll as a labelled assumption.
- Part-day holidays under the federal regime: ATO table counts them, statute is ambiguous (above).
- WA 2028: WA Government says 2028 dates "will be published when confirmed". The Public and Bank Holidays Amendment Bill 2025 would from 1 Jan 2028 move Labour Day to the second Monday in March (13 Mar 2028), WA Day to the second Monday in November, King's Birthday to the second Monday in June (12 Jun 2028) and add Easter Saturday and Show Day. WA Parliament's current-bills page (read 2026-09-29) still shows it at Legislative Council second reading, last action 23 Oct 2025. Under current law Labour Day would be Mon 6 Mar 2028 and WA Day Mon 5 Jun 2028. Both are in `unresolved` (SUSPECT, null date, candidate dates for flagging).
- VIC Friday before the AFL Grand Final, Sep 2027: Business Victoria says the date follows the AFL schedule (typically the last Friday in September) and is not yet published. In `unresolved` with `expected_month: 2027-09`.
- Proclamations and ministerial orders can add or substitute holidays after the data date (SA Public Holidays Act 2023 s 3(5) and s 5; NSW Public Holidays Act 2010 s 5 and s 6). Re-check every July.
- 2025 dates (Jul to Dec 2025) rest on the Fair Work Ombudsman's 2025 page only; the ATO's current table no longer shows 2025. 2026 and 2027 dates were also checked against state and territory pages, and Aug 2026 to Jun 2027 against the ATO table. 2028 dates come from each jurisdiction's own page or statute (NSW and WA: statute, since neither publishes 2028 yet).

## 5. Discrepancy: ATO table row for Fri 25 Sep 2026

The ATO table gives Mon 28 Sep 2026 as the first business day after the Victorian Friday before the AFL Grand Final (25 Sep). The next row of the same table lists Mon 28 Sep 2026 as King's Birthday (WA), whose first business day is Tue 29 Sep. Under TAA 1953 s 8AAZMB(2), 28 Sep 2026 is not a business day, so the definition gives Tue 29 Sep 2026. Both are recorded in the data (`ato_first_business_day_table`, row with `discrepancy`) and asserted in the tests. Every other row (19 of 20) agrees with the definition applied to our holiday rows. No existing VERIFIED figure is affected.

## 6. Recommended calculator behaviour

1. One shared loader (`src/au_tax/holidays.py`, skill-builder to write) reads `data/holidays/au.yaml` once and offers: `is_business_day(d, regime)`, `first_business_day_on_or_after(d, regime)`, `add_business_days(start, n, regime)` (count starts the day after `start`). Never reimplement rolling in a calculator.
2. Replace the weekend-only helpers: `gst.py` `_next_business_day`, `payg_lodgment.py` `_roll`, `fbt.py` `_next_business_day`, `router.py` `_nbd`. `payroll.py` `business_days_after` takes a caller-supplied holiday list; make the data file the default and keep the list only as an override. `state_sa.py` payroll tax dates use the `sa_state_tax` regime; everything else the `commonwealth_tax` regime.
3. Output for every rolled date: original date, due date, whether it rolled, why (Saturday, Sunday, or the holiday name and jurisdictions), regime, and the rule sources (TAA 1953 s 8AAZMB or Sch 1 s 388-52; RevenueSA page) in `figures_used` style so the output contract's source line is filled.
4. Dates outside the data range: refuse, never fall back to weekends only. Needs a new refusal code added to `data/refusals/au.yaml` first (orchestrator decision).
5. Unresolved items, mapped to the existing conventions: a due date whose rolling path touches a candidate date (WA 6 Mar or 5 Jun 2028) behaves like a non-VERIFIED figure with a value (AU-GEN-001, draft possible with `allow_draft`, marked draft with the alternative date). A due date that lands on a Friday in Sep 2027 (no candidate date) behaves like a figure with no published value (AU-GEN-003).
6. Where the ATO table prints a different first business day from the definition (only 25 Sep 2026 today), return the definition's date and add a warning quoting the ATO's printed date.
7. Do not roll GIC amounts (s 8AAZMB(2)); roll the tax debt due date only.
8. Land tax: show the assessment due date; if it is a non-business day in the SA regime, show the rolled date as an assumption and say RevenueSA has not published a rule.
9. Payday Super: the fund-side 3-business-day allocation window uses a different definition (weekends and public holidays where the fund operates), per an ATO newsroom page seen in a search excerpt only (https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/super-funds-newsroom/business-days-decoded-why-it-matters-for-your-fund); not modelled here, verify before use.

Tests the calculators should add (expected values already checked against sources in `tests/data/test_holidays.py`):

| Case | Expected | Source |
|---|---|---|
| Due Fri 26 Mar 2027 (Good Friday) or Sat 27 Mar, Sun 28 Mar, Mon 29 Mar | Tue 30 Mar 2027 | ATO table (Easter) |
| Due Thu 24, Fri 25, Sat 26 or Mon 28 Dec 2026 | Tue 29 Dec 2026 | ATO table (Christmas) |
| Due Thu 31 Dec 2026, Fri 1 Jan or Sat 2 Jan 2027 | Mon 4 Jan 2027 | ATO table (New Year) |
| SA regime: Feb 2027 payroll tax return, 7 Mar 2027 (Sun) | Tue 9 Mar 2027 (Adelaide Cup Day Mon 8 Mar) | RevenueSA published date |
| SA regime: 7 Nov 2026 (Sat) | Mon 9 Nov 2026 | RevenueSA published date |
| Regime difference: due Mon 7 Jun 2027 | ATO Tue 8 Jun; RevenueSA Mon 7 Jun | ATO table; RevenueSA published date |
| Regime difference: due Thu 24 Dec 2026 | ATO Tue 29 Dec; SA regime stays 24 Dec | ATO table; PHA 2023 s 8(3) |
| Payday Super: QE 9 Jul 2026 plus 20 business days | Fri 7 Aug 2026 | ATO Payday Super example |
| Payday Super: QE 30 Jul 2026 plus 7 business days | Tue 11 Aug 2026 | ATO Payday Super example |
| Payday Super: QE 8 Jun 2027 plus 7 business days | Fri 18 Jun 2027 | LCR 2026/3 para 98 |
| Payday Super: QE 30 Jul 2027 plus 7 business days | Wed 11 Aug 2027 | LCR 2026/3 para 167 |

## 7. Citations

Legislation (read 2026-09-29):
- TAA 1953 s 8AAZMB and Sch 1 s 388-52: https://www.legislation.gov.au/C1953A00001/latest/text (compilation C2026C00393, 27 Aug 2026)
- ITAA 1997 s 995-1(1) "business day": https://www.legislation.gov.au/C2004A05138/latest/text (C2026C00400, 27 Aug 2026)
- SGAA 1992 s 6(1) "business day": https://www.legislation.gov.au/C2004A04402/latest/text (C2026C00272, 1 Jul 2026)
- Acts Interpretation Act 1901 s 2B and s 36: https://www.legislation.gov.au/C1901A00002/latest/text (C2026C00117, 28 Mar 2026)
- Public Holidays Act 2023 (SA): https://www.legislation.sa.gov.au/lz?path=/c/a/public%20holidays%20act%202023 (version 10.9.2026)
- Legislation Interpretation Act 2021 (SA): https://www.legislation.sa.gov.au/lz?path=/c/a/legislation%20interpretation%20act%202021 (version 20.11.2025)
- Payroll Tax Act 2009 (SA) s 9 and s 87 (7 days after month end; 21 days after June): https://www.legislation.sa.gov.au/lz?path=/c/a/payroll%20tax%20act%202009
- Taxation Administration Act 1996 (SA) and Land Tax Act 1936 (SA), no roll provision: https://www.legislation.sa.gov.au/lz?path=/c/a/taxation%20administration%20act%201996 ; https://www.legislation.sa.gov.au/lz?path=/c/a/land%20tax%20act%201936
- NSW Public Holidays Act 2010 s 4: https://legislation.nsw.gov.au/view/html/inforce/current/act-2010-115
- WA Public and Bank Holidays Act 1972 Second Schedule: https://www.legislation.wa.gov.au/legislation/statutes.nsf/main_mrtitle_762_homepage.html
- ACT Holidays Act 1958 s 3: https://www.legislation.act.gov.au/a/1958-19/current/pdf/1958-19.pdf
- Tasmania Statutory Holidays Act 2000 s 4: https://www.legislation.tas.gov.au/view/whole/html/inforce/current/act-2000-096

ATO:
- https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/prepare-and-lodge/registered-agent-lodgment-program/lodgment-and-payment-dates-on-weekends-or-public-holidays
- https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/reports-and-returns/due-dates-for-lodging-and-paying
- https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/business-activity-statements-bas/due-dates-for-lodging-and-paying-your-bas
- https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/fringe-benefits-tax/fbt-registration-lodgment-payment-and-reporting/lodging-your-fbt-return-and-paying
- https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/paying-super-on-payday/payment-deadlines-for-payday-super
- LCR 2026/3: https://www.ato.gov.au/law/view/view.htm?docid=%22COG%2FLCR20263%2FNAT%2FATO%2F00001%22

RevenueSA:
- https://www.revenuesa.sa.gov.au/payrolltax/returns-and-annual-reconciliation/monthly-returns
- https://www.revenuesa.sa.gov.au/payroll-tax/returns-and-annual-reconciliation
- https://www.revenuesa.sa.gov.au/land-tax/ltpay

Holiday lists (each row of the data file cites its own):
- Fair Work Ombudsman 2025, 2026, 2027: https://www.fairwork.gov.au/employment-conditions/public-holidays/2026-public-holidays (and the /2025- and /2027- pages)
- SafeWork SA 2025 to 2028: https://safework.sa.gov.au/resources/public-holidays
- NSW: https://www.nsw.gov.au/about-nsw/public-holidays ; QLD: https://www.qld.gov.au/recreation/travel/holidays/public ; NT: https://nt.gov.au/nt-public-holidays ; TAS: https://worksafe.tas.gov.au/topics/laws-and-compliance/public-holidays
- VIC: https://business.vic.gov.au/business-information/public-holidays/victorian-public-holidays-2028 (and the 2026 and 2027 pages); WA: https://www.wa.gov.au/service/employment/workplace-arrangements/public-holidays-western-australia
- ACT: https://www.act.gov.au/__data/assets/pdf_file/0016/3003712/ACT-Public-Holidays-2028.pdf (and the 2026 and 2027 PDFs)

Not read: the SA authorised PDFs (the current-version RTF text on legislation.sa.gov.au was read instead), and the QLD, NT and WA state pages for 2025 (Fair Work's 2025 page was used).
