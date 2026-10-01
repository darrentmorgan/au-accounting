---
name: gst-bas
description: 'Australian GST and BAS working papers - GST registration, classifying sales and purchases (taxable, GST-free, input taxed), GST credits, BAS labels G1 to G20, 1A, 1B, Simpler BAS, W1 to W5, cash vs accrual, tax invoices, bad debt adjustments, the margin scheme, GST at settlement, reverse charge on imported services, and BAS due dates. Use when someone says "do my BAS", "what goes at G1 / 1A / 1B", "how much GST do I owe this quarter", "do I need to register for GST", "GST threshold", "should I charge GST to an overseas client", "is rent GST-free", "margin scheme", "GST on selling a new house or unit", "sale of a business as a going concern", "when is my BAS due". Also use for GST on Airbnb or short-stay accommodation, serviced apartments, property development, GST groups or branches, financial supplies and complex international supplies: the skill decides what is in scope and escalates to a registered tax or BAS agent.'
---

# GST and BAS (Australia)

Prepares GST working papers and BAS label figures through four tools. Never do the GST arithmetic yourself and never quote a threshold, due date or rate from memory: every number comes from a tool's `figures_used` or from `get_figure`.

| Tool | Use for |
|---|---|
| `bas_gst_worksheet` | A BAS period from a list of sales, purchases and adjustments: labels G1 to G20, 1A, 1B, Simpler BAS, W1 to W5, net GST |
| `margin_scheme_gst` | GST on a property sale under the margin scheme, the G1 and 1A figures, GST at settlement withholding |
| `gst_registration_check` | Must the entity register, from current and projected GST turnover |
| `bas_due_date` | Lodge-and-pay due date for a quarter or month, with online and agent concessions |

## Scope

In scope: registration (GSTA s23-5, s23-15 thresholds by key `gst.registration_threshold` and `gst.registration_threshold_nfp`, taxi and ride-sourcing always (s144-5), GST turnover rules in Div 188); classification of supplies; attribution on a cash or accruals basis (Div 29); tax invoices; creditable acquisitions and simple apportionment; adjustments (Div 19, bad debts Div 21); reverse charge on imported services where the split is simple (s84-5); margin scheme (Div 75); GST at settlement (TAA 1953 Sch 1 s14-250) awareness; BAS labels and due dates; PAYG withholding labels W1 to W5.

Awareness only (explain, do not compute): PAYG instalments T1 to T11 (use the payg-instalments skill), fuel tax credits (AU-GST-007), low value imported goods, electronic distribution platform rules, Division 129 change of use. Short-stay accommodation (residential premises v commercial residential premises, Division 87 long stays, platform reporting) is handled by the short-stay-accommodation skill, which hands its registration inputs to `gst_registration_check` here.

Crypto: digital currency (bitcoin, ether and similar fungible coins) is input taxed rather than taxable, but an NFT is not digital currency (GSTA 1999 s 195-1) and its supply is taxable unless GST-free. For NFT creation or sales, or sales for crypto, do not run `gst_registration_check` to conclude registration from a rough income figure: the crypto skill escalates it (AU-CRYPTO-006) and overseas buyers are AU-GST-005.

Escalate (see Escalation): property development positions, commercial residential premises determinations for short-stay operators, financial supply apportionment beyond a simple split, GST groups and branches, complex international supplies.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Period and income year**: which quarter or month (the income year runs 1 July to 30 June, written `2026-27`). If "this quarter" is ambiguous, ask.
2. **Registration**: registered for GST? GST turnover (sets Simpler BAS vs full reporting, and monthly vs quarterly).
3. **Accounting basis**: cash or accruals (cash needs eligibility: small business entity by `gst.cash_accounting_turnover_max`, or the other s29-40 limbs).
4. **Transactions**: for each sale or purchase, amount, whether it includes GST, what it is (to classify it), capital or not, business-use share, whether a tax invoice is held for purchases above the tax invoice threshold, and the date.
5. For registration: current GST turnover (this month plus the previous 11), projected GST turnover (this month plus the next 11), non-profit or not, taxi or ride-sourcing, and any input taxed sales (such as residential rent) inside those figures.

## Procedure

1. Confirm period, basis and registration. If a special situation in the Escalation table is present, surface the code first.
2. Classify each item using the rules below and `references/classification.md`. State each classification with its section; where it is doubtful, say so and ask.
3. Call the tool:
   - BAS: `bas_gst_worksheet` with `income_year` and `inputs`, for example `{"accounting_basis": "accrual", "gst_turnover": <amount>, "transactions": [{"kind": "sale", "amount": <amount>, "gst_inclusive": true, "classification": "taxable"}, {"kind": "purchase", "amount": <amount>, "classification": "taxable", "capital": false, "creditable_share": 1}], "adjustments": [{"gst_amount": <gst>, "reason": "bad_debt_written_off_by_supplier"}], "payg_withholding": {"w1": <amount>, "w2": <amount>}}`.
     Sale classifications: `taxable`, `export_goods` (G2), `gst_free` (G3, including GST-free services to non-residents and going concerns), `input_taxed` (G4), `margin_scheme` (give `margin`), `out_of_scope`. Purchase classifications: `taxable`, `gst_free` (G14), `input_taxed_use` (G13), `private` (G15), `reverse_charge`, `out_of_scope` (wages, super, loan repayments, drawings, dividends). Mixed use: `creditable_share` with `non_creditable_reason` `private` or `input_taxed_use`. Cash basis part payments: `amount_paid`. Dates with `period_start` and `period_end` filter attribution.
   - Property sale: `margin_scheme_gst` with `sale_price`, `margin_basis` (`consideration` or `valuation`), `acquisition_price` or `approved_valuation`, `written_agreement`, `acquired_via_fully_taxable_supply`, `special_acquisition`, `residential_withholding`.
   - Registration: `gst_registration_check` with `entity_type`, `current_gst_turnover`, `projected_gst_turnover`, `input_taxed_sales_included`, `projected_capital_asset_sales_included`, `supplies_taxi_or_ride_sourcing`, `amounts_include_gst`.
   - Due dates: `bas_due_date` with `cycle`, `quarter` or `month`, `lodgment` (`paper`, `online_self`, `registered_agent`), `gst_turnover`.
4. Read the envelope. `exit_code` 0: present the result. `exit_code` 3: quote the refusal code and message verbatim and stop that part. `exit_code` 4 with `AU-GEN-001`: the figure is not verified for that year; say so, and offer a draft with `allow_draft: true` clearly labelled unverified. `exit_code` 4 with `AU-GEN-003`: the figure has no published value, so no draft is possible; quote the message and stop that part. `exit_code` 2: fix the input and call again.
5. Report BAS labels exactly as `bas_labels_whole_dollars` returns them (whole dollars, cents dropped, no negatives). Show the cents figures from `worksheet` as the working. Never round differently.
6. **If the au-tax tools are not available in this session**, say so, quote AU-GEN-001 and its message verbatim, and stop. Do not compute GST by hand and do not read figures from the rates files yourself: a hand calculation bypasses the verification gate.
7. Always state the headline answer in dollars when a tool returns one (for example "net GST payable: $X", "G1: $X") and dates in full ("11 November 2026").

## Judgement rules

- **Taxable supply** (s9-5): made for consideration, in the course of an enterprise, connected with Australia, by a registered (or required to be registered) entity, and not GST-free or input taxed. GST is 10% of the value (s9-70), which is 1/11 of a GST-inclusive price.
- **GST-free** (Div 38): basic food, most health, education, childcare, exports of goods (s38-185; G2 is goods only), water (s38-285), and:
  - **Exports of services, s38-190(1) item 2**: the recipient is a non-resident who is **not in Australia when the thing supplied is done**, and the supply is neither work physically performed on goods in Australia nor directly connected with Australian real property (or the non-resident acquires it for its enterprise and is not registered). This is not a "consumed outside Australia" test; that is item 3 (effective use or enjoyment outside Australia). Not GST-free if the service is provided to another entity in Australia (s38-190(3)). GST-free services go to G3, not G2.
  - **Going concern, s38-325**: three conditions in s38-325(1): the supply is for consideration, the recipient is registered or required to be, and both parties agree in writing that it is a supply of a going concern; plus the two-limb definition in s38-325(2): the supplier supplies all things necessary for continued operation of the enterprise, and carries it on until the day of supply. GSTR 2002/5.
- **Input taxed** (Div 40): no GST on the sale and no credits for related purchases (s11-15): financial supplies (s40-5), residential rent (s40-35), sales of residential premises other than new residential premises (s40-65). Report input taxed sales at G1 and G4 (G4 is worksheet only).
- **Residential vs commercial residential premises**: rent of residential premises is input taxed even for short stays; accommodation in commercial residential premises (s195-1: hotel, motel, inn, hostel, boarding house, caravan park and anything similar) by the entity that owns or controls them is taxable. The test is the overall impression (GSTR 2012/6; draft update GSTR 2012/6DC of 5 Nov 2025 pending, Commissioner's view said to be unchanged). A single apartment or house let short term is residential premises, even inside a complex. Anything turning on the classification of an operation: AU-GST-002; use the short-stay-accommodation skill for the screen. Division 87 (long-term stays of at least `gst.div87_long_term_days` continuous days) applies only to commercial residential premises; see `references/short-stay.md`.
- **New residential premises** (s40-75): sale is taxable (usually with the margin scheme); the purchaser withholds GST at settlement (TAA Sch 1 s14-250; `gst.settlement_withholding_margin_scheme_rate` or `gst.settlement_withholding_standard_fraction` of the contract price) and the seller still reports the sale in the BAS for the settlement period. Developer positions: AU-GST-001.
- **Margin scheme** (Div 75): needs a written agreement on or before the supply (s75-5(1), (1A)); not available if the seller acquired the property through a taxable supply worked out without the margin scheme (s75-5(3)). Margin = price less acquisition consideration (s75-10(2)) or an approved valuation (s75-10(3)). GST is 1/11 of the margin. **G1 shows the margin, not the price**; nothing at G1 if the margin is nil or negative. The buyer gets no credit.
- **Changing basis** (Div 159): moving from accruals to cash, anything already attributed under accruals (invoices issued but unpaid, purchases invoiced but unpaid) is not attributed again when paid (s159-20); moving from cash to accruals, amounts not yet attributed fall into the first accruals period (s159-5, s159-10). Invoices attributed under accruals and written off after the switch still get a Division 21 adjustment (s159-25). Cash basis helps cash flow with slow payers because GST follows receipts, but credits also wait for payment. Keep the basis consistent for at least a year of periods and change through the ATO.
- **Attribution** (Div 29): accruals basis attributes GST to the period of the earlier of invoice or any payment; cash basis to the period of payment, part by part. A credit needs a tax invoice before it is claimed (s29-10(3)) unless the purchase is at or below `gst.tax_invoice_threshold_incl_gst`; invoices at or above `gst.tax_invoice_buyer_identity_threshold` must show the buyer identity or ABN.
- **Credits** (Div 11): only for a creditable purpose. Private or non-deductible share goes to G15; purchases for input taxed sales go to G13. Car credits are capped at `gst.max_gst_credit_car_limit`. Wages, super, loan principal, drawings and dividends are not reported at G10 or G11.
- **Bad debts** (Div 21, GSTR 2000/2): accruals basis only (s21-5(2)). The supplier has a decreasing adjustment when the debt is written off as bad **or** overdue 12 months or more (s21-5); the recipient has an increasing adjustment on the same triggers (s21-15). Recoveries reverse them (s21-10, s21-20). The 12-month limb applies to both parties. Increasing adjustments go to G7, decreasing to G18.
- **Imported services** (Subdiv 84-A): the recipient reverse charges GST only if registered and the purchase is not wholly for a creditable purpose (s84-5); report the price times 1.1 at G1 and G10 or G11. **Electronic distribution platforms** (Subdiv 84-B): s84-55 (operator treated as supplier), s84-60 (extension by agreement), s84-65 (inbound intangible consumer supply), s84-70 (meaning of EDP). Accommodation in Australian real property is not an inbound intangible consumer supply, so Airbnb or Booking.com do not become the supplier of the stay (inference from those sections and LCR 2018/2). Low value imported goods sit in Subdiv 84-C.
- **Registration**: GST turnover meets the threshold when current turnover is at or above it (unless the ATO is satisfied projected turnover is below) or projected turnover is at or above it (s188-10). GST turnover excludes input taxed sales (residential rent, interest and other financial supplies) and supplies not made in connection with an enterprise (s188-15). Capital asset sales and wind-down sales are disregarded only in **projected** turnover (s188-25); they still count in current turnover. Where current turnover meets the threshold only because of a one-off asset sale and projected turnover is below it, say registration is required unless the ATO is satisfied projected turnover is below the threshold. Register within `gst.registration_deadline_days` days. Taxi and ride-sourcing: always (s144-5). Fuel tax credits need registration.
- **Reporting**: Simpler BAS (G1, 1A, 1B) below `gst.simpler_bas_turnover_max`; full reporting adds G2, G3, G10, G11. Monthly lodging is compulsory at or above `gst.monthly_reporting_turnover_min`. BAS figures are whole dollars, cents dropped, no negative figures.
- **Due dates**: quarterly on the 28th of the month after the quarter, quarter 2 on 28 February; monthly on the 21st. The online concession adds two weeks to **lodge and pay** for quarters 1, 3 and 4 only, not monthly or large business. Registered agent program dates are later still. A due date that is a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT rolls to the first business day after (TAA 1953 s 8AAZMB and Sch 1 s 388-52), wherever the taxpayer is; `bas_due_date` returns the original date, the due date and the reason in `business_day_roll`. If it warns that the ATO's printed date differs from the statute, quote both. AU-GEN-004 means the date is outside the public holiday data: the tool refuses rather than guess, because the date is the answer. Always use `bas_due_date`.
- **PAYG withholding labels**: W1 gross payments, W2 withheld from W1, W4 no-ABN withholding, W3 other withholding, W5 = W2 + W4 + W3 (W1 not included), copied to label 4.

## Escalation

| Trigger | Code |
|---|---|
| Property development, new residential premises developer, subdivision, s75-11 margin scheme cases, 5-year rental rule, Div 129/135 on real property | AU-GST-001 |
| Short-stay, serviced apartment or head-lease operator where the answer turns on commercial residential premises | AU-GST-002 |
| Financial supplies or input taxed apportionment beyond a simple split; financial acquisitions threshold | AU-GST-003 |
| GST groups, branches, joint ventures | AU-GST-004 |
| Complex international supply (s38-190(3), recipient location unclear, non-resident supplier, EDP, complex reverse charge) | AU-GST-005 |
| Margin scheme not available on the facts | AU-GST-006 |
| Fuel tax credit calculation | AU-GST-007 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| A due date or business-day count is outside the public holiday data | AU-GEN-004 |
| Asked to lodge or pay | AU-GEN-002 |

When a trigger fires, quote the code and its message exactly as in `data/refusals/gst.yaml` (or as the tool returns it), stop that part, and say what can still be done. For AU-GST-002 still explain the tests (see `references/short-stay.md`) and suggest a private ruling. The calculators also accept `special_circumstances` so the refusal comes back from the tool.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated period and income year: classification of each item with its section; the BAS labels to report (whole dollars) and the worksheet working; net GST payable or refundable; due date if asked.
2. **Figures used**: key, value, status, source URL for each `figures_used` entry.
3. **Assumptions**: the tool's `assumptions` plus your own (for example, a classification you made).
4. **Risk flags**: ids from the tool's `risk_flags` and any relevant entries in `data/risk_flags/gst.yaml`, or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/classification.md` (supply types and BAS labels), `references/short-stay.md` (residential vs commercial residential premises, Division 87, platforms), `references/sources.md` (primary sources).
