# Records and chart of accounts

## What to keep
- Everything that records and explains transactions relevant to tax, super and registration: sales and purchase invoices, tax invoices for GST credits, bank and card statements, payroll and STP reports, super payment evidence, asset register, stocktake sheets, loan and related-party agreements, minutes and resolutions (bonuses, director fees, dividends), BAS and working papers.
- Records must be in English or readily convertible, and show the transaction well enough that the tax liability can be worked out (ITAA 1936 s 262A; TR 96/7).
- Retention periods are figures: `bookkeeping.record_retention_years` for tax records (start point differs for FBT and super records), `bookkeeping.company_financial_records_retention_years` for company financial records. Longer for CGT assets, depreciating assets, carried-forward losses, and until the period of review ends for anything a later return relies on.
- Digital: image copies of paper are acceptable if true and clear; entering data into software does not replace keeping the source document; cloud data must be downloaded before a software subscription lapses; keep a written record of routine destruction procedures (TR 2018/2).

## Cash vs accrual
- Income tax: cash (receipts) or accruals (earnings) depends on the taxpayer and the type of income (TR 98/1); a professional or small trader may use receipts. The choice sets when income and, for accruals, deductions are recognised.
- GST: accounting basis is separate. Cash basis is available below the GST cash turnover limit (`gst.cash_accounting_turnover_max`) and by choice (GSTA s 29-40). Note which basis each report uses. Bank-feed-only ledgers are usually cash; invoices in accounting software are accruals.
- Consequences for year end: bad debts and accrued expenses only matter on accruals; prepayments and stock matter on both.

## Chart of accounts for a small business
Structure: assets, liabilities, equity, income, cost of sales, expenses. Keep account numbers stable; add rather than repurpose.

GST code on every account (the ledger, not the memory of the bookkeeper, drives the BAS):
- Income: GST on income (taxable), GST-free income (e.g. eligible exports, basic food), input-taxed income (e.g. residential rent, financial supply), BAS excluded (transfers, loans, owner funds, wages, dividends received).
- Expenses: GST on expenses (credit claimed), GST-free expenses, input-taxed purchases (no credit), capital purchases (a separate code for the capital label), BAS excluded (wages, super, PAYG, bank fees that have no GST, drawings, tax payments).
- Separate income lines by GST status so the BAS is not rebuilt from a single sales account.

Balance sheet accounts that must exist and stay separate:
- GST control (collected, paid, and ATO settlements only). Do not post bank fees or other items directly to it.
- PAYG withholding payable and super payable (accrue at each pay run; clears against ATO and fund payments). Wages expense, super expense and any payroll tax or workers compensation accrual in expenses.
- ATO integrated client account clearing: all ATO payments and refunds pass through it and are then allocated to GST, PAYG withholding, PAYG instalments, income tax and super charge. It should agree to the ATO online statement.
- PAYG instalments paid (asset) and income tax payable or refundable.
- Owner accounts: sole trader drawings and capital; partner current accounts; company director or shareholder loan accounts (Division 7A tracking, see company-div7a); trust beneficiary accounts (see trusts-partnerships).
- Suspense or uncategorised: exists only to be cleared; balance must be nil at each month end.
- Platform clearing accounts (card processors, booking platforms): record income gross, fees as expenses, and the net receipt through clearing, so bank feeds reconcile to the platform reports. Money held for others (owner funds, deposits) sits in liability accounts and, where a statute requires trust accounting, in a separate trust ledger that this skill does not cover.

## Bank feed categorisation rules
- Rules should map counterparties to accounts and GST codes, never to suspense by default. Review any rule that codes above a set size or that touches ATO, payroll, loans, owner or related-party payments.
- Transfers between own accounts, loan drawdowns and repayments, owner draws and card payments are BAS excluded and must not hit income or expenses.
- Split lines where a payment covers GST and non-GST items.
- Review the uncoded and rule-coded lists at each month end.

## Owner drawings, wages and loans
- Sole trader and partnership: drawings are equity movements, not deductions; there are no wages for the owner.
- Company: pay owners as employees (withholding, super), by dividend, or by a loan that satisfies Division 7A. Undocumented withdrawals are loans; record them in the loan account and route to company-div7a before year end.
- Trust: distributions follow the trust deed and resolutions made by year end; see trusts-partnerships.
