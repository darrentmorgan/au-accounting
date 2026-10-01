# Classifying supplies and mapping them to BAS labels

Figures are named by key; values come from `data/rates/<year>.yaml` and `data/rates/<year>.d/gst.yaml`.

## Sales

| What it is | Treatment | Section | Tool classification | Labels |
|---|---|---|---|---|
| Ordinary goods or services sold in Australia by a registered entity | Taxable | GSTA s9-5 | `taxable` | G1 |
| Goods exported within the export window | GST-free | s38-185 | `export_goods` | G1, G2 (free-on-board value; freight and insurance to G3) |
| Services to a non-resident not in Australia when the service is done, not about Australian land or goods (item 2), or used or enjoyed outside Australia (item 3) | GST-free | s38-190(1) items 2, 3; limits s38-190(2A), (3), (4); GSTR 2004/7 | `gst_free` | G1, G3 |
| Basic food, most health, education, childcare, water, sewerage | GST-free | Subdivs 38-A to 38-D, s38-285, s38-290 | `gst_free` | G1, G3 |
| Sale of a business as a going concern (all s38-325 conditions met) | GST-free | s38-325; GSTR 2002/5 | `gst_free` | G1, G3 |
| Interest, lending, other financial supplies | Input taxed | s40-5; GST Regs Div 40 | `input_taxed` | G1, G4 |
| Residential rent, including short-stay lets of residential premises | Input taxed | s40-35 | `input_taxed` | G1, G4 |
| Sale of existing (not new) residential premises | Input taxed | s40-65 | `input_taxed` | G1, G4 |
| Sale of new residential premises or commercial property | Taxable (margin scheme possible for real property) | s40-75, Div 75 | `taxable` or `margin_scheme` | G1 (margin only under the scheme) |
| Accommodation in commercial residential premises by the operator | Taxable (Div 87 for long stays) | s40-35(1)(a) exclusion, s195-1, Div 87 | `taxable` (escalate classification: AU-GST-002) | G1 |
| Commercial rent or lease | Taxable | s9-5 | `taxable` | G1 |
| Sale of a business asset (car, equipment) | Taxable | s9-5 | `taxable` | G1 |
| Wages received, dividends, gifts, loans received, private sales, hobby income, tax refunds | Not reported | ATO BAS Step 1 | `out_of_scope` | none |

## Purchases

| What it is | Tool classification | Labels |
|---|---|---|
| Business purchase with GST in the price, fully business use | `taxable` | G10 (capital) or G11 |
| Purchase with no GST in the price (bank fees, GST-free food, unregistered supplier) | `gst_free` | G10/G11 and G14 |
| Purchase for making input taxed sales (repairs on a residential rental, costs of financial supplies) | `input_taxed_use` | G10/G11 and G13 |
| Private or non-deductible share | `creditable_share` below 1, reason `private` | G10/G11 and G15 |
| Imported service or digital product, registered buyer, not wholly creditable | `reverse_charge` | price times 1.1 at G1 and G10/G11; non-creditable share at G13 or G15 |
| Wages, super, loan principal, drawings, dividends paid, stamp duty, ATO payments | `out_of_scope` | none |

Capital purchases go to G10. If capital and non-capital are not recorded separately and GST turnover is under the ATO's small-purchase limit, low-value capital items may go to G11 (ATO BAS Step 3).

## Worksheet arithmetic (ATO BAS instructions, Steps 1 to 4)

- G5 = G2 + G3 + G4; G6 = G1 - G5; G8 = G6 + G7; G9 = G8 / 11, reported at 1A.
- G12 = G10 + G11; G16 = G13 + G14 + G15; G17 = G12 - G16; G19 = G17 + G18; G20 = G19 / 11, reported at 1B.
- The worksheet method requires GST-inclusive amounts at every label. The accounts method (actual GST from the ledger) gives the same 1A and 1B where every taxable amount carries exactly 1/11 GST.
- G7 holds increasing adjustments and G18 decreasing adjustments, each as eleven times the GST adjustment amount.
- Report whole dollars (cents dropped), no negative figures, and leave labels that do not apply blank.

## Adjustments

- Division 19: change in price, cancelled supply, change in consideration after the period (for example a later discount or refund).
- Division 21 bad debts (accruals only): supplier s21-5 (written off or overdue 12 months or more, decreasing), s21-10 recovered (increasing); recipient s21-15 (increasing), s21-20 (decreasing on later payment). GSTR 2000/2.
- Division 129 change in creditable purpose for acquisitions used differently from planned: adjustment periods depend on the acquisition value (SOURCE-CITED only; escalate for real property: AU-GST-001).
- Errors from earlier periods may sometimes be corrected on a later BAS under the ATO's correcting GST errors determination; outside those limits, revise the earlier BAS.

## Attribution

- Accruals (s29-5(1), s29-10(1)): whole GST or credit in the period of the earlier of invoice issued or any payment.
- Cash (s29-5(2), s29-10(2)): only the part of the payment received or made in the period. Eligibility s29-40: small business entity (aggregated turnover below `gst.cash_accounting_turnover_max`), non-business entity under the cash accounting threshold, receipts-basis income tax, or a Commissioner determination.
- Credits need a tax invoice first (s29-10(3)) unless the purchase is at or below `gst.tax_invoice_threshold_incl_gst`.
