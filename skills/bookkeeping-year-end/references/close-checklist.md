# Month end and year end close

Tailor to the entity. Skip steps that do not apply and say so.

## Every month
1. Reconcile every bank, credit card and loan account to the statement; clear the unreconciled list; no stale unreconciled items older than the statement period.
2. Clear suspense and uncategorised to nil. Run `trial_balance_check` on the month-end trial balance.
3. Payroll: wages, PAYG withholding payable and super payable agree to the pay runs and to STP reports. Super for each payday must be received by the fund within the Payday Super window (`super.payday_super_usual_period_business_days` (payroll-sg; from 1 Jul 2026)); anything outside it is late.
4. GST control account: after each BAS, the balance should equal the GST on unlodged periods plus items in transit. Run `gst_control_reconciliation` against the BAS lodged.
5. ATO clearing account agrees to the ATO online statement.
6. Debtors and creditors ledgers agree to control accounts; chase overdue debtors; check supplier statements.

## Year end (30 June)
1. All month-end steps to 30 June, including the last BAS and payroll.
2. Bank and card reconciliations dated 30 June; outstanding cheques and deposits in transit listed.
3. Accruals: unpaid wages, super, bonuses committed by 30 June, supplier invoices for work done, interest, utilities.
4. Prepayments: list every payment covering a period after 30 June (insurance, rent, subscriptions, software, advertising). Run `prepayment_deduction` for each item at or above the excluded amount; below it the item is deductible when incurred.
5. Trading stock: count stock on hand at 30 June, value it, and compare to opening stock. If the entity qualifies and the change is at or below the simplified limit (`bookkeeping.simplified_trading_stock_change_max`) it may skip the stocktake; otherwise account for the change. Record obsolete or damaged stock.
6. Fixed assets: reconcile the asset register to the ledger; record disposals and additions; calculate depreciation, instant asset write-off and pools with sole-trader-business.
7. Bad debts: review debtors, decide and record in writing before 30 June which debts are written off as bad; for a company, check continuity of ownership or business continuity; consider the GST adjustment through gst-bas.
8. Bonuses and director fees: minute the resolution and notify the recipient before 30 June if the deduction is wanted in the year; check withholding and super on payment.
9. Loans: reconcile shareholder, director and related-party loan accounts; compare to Division 7A minimum repayments and benchmark interest with company-div7a.
10. PAYG instalments paid agree to the ATO; reconcile to the year's instalment rate or amount with payg-instalments-lodgment.
11. STP: payroll finalisation figures agree to the ledger (gross wages, withholding, super, reportable fringe benefits, allowances).
12. GST: annual reconciliation of the ledger to the four quarters or twelve months of BAS, with the year total of GST collected and paid.
13. Final trial balance (`trial_balance_check`), profit and loss and balance sheet; produce accounting profit to taxable income reconciliation items (see SKILL.md).
14. Size and reporting: for a company run `large_proprietary_test` on the financial year's consolidated figures; note ASIC annual review and any financial report deadlines.
15. Archive: lock the period, back up the file, store source documents for the retention period.
