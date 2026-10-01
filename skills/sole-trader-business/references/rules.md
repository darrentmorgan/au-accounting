# Calculation detail: sole-trader-business

## Simplified depreciation order (ATO pool worksheet)
1. Each asset first used in the year: if cost is below the threshold, deduct the business portion; otherwise add the business portion (cars: cost capped at the car limit first) to the pool.
2. Pool balance before depreciation = opening balance (after any business-use adjustment) + pooled additions + pooled cost additions - business portion of termination values of pooled assets sold or lost.
3. Balance negative: the shortfall is assessable income and the closing balance is nil.
4. Balance below the threshold: the whole balance is deducted; closing balance nil.
5. Otherwise: later-year rate on the opening balance plus first-year rate on the year's additions. Disposals reduce the closing balance, not the deduction. Closing balance carries forward.
6. Sale of an asset previously written off in full: business portion of the termination value is assessable income.
7. First improvement under the threshold to an asset previously written off is deducted immediately; later improvements go to the pool.

## Date rules
- Threshold decided by first-use or installed-ready date. Assets first used from 1 July 2026 use the permanent threshold; pool balance write-off follows the same threshold for income years ending on or after 1 July 2026. The 2025-26 year used the same amount under the earlier temporary extension for assets first used between 1 July 2025 and 30 June 2026.
- The tool refuses (AU-BUS-005) an asset whose date falls outside the run year; rerun for its own year and carry the pool forward.

## Non-commercial loss income requirement
Taxable income as if the activity's loss were not deducted, plus reportable fringe benefits, reportable super contributions and net investment losses; must be under the limit. Any assessable first home super saver released amount is ignored. Then one of four tests. Deferred sole trader losses are added back for the small business income tax offset.

## PSI test logic
- Results test alone can make a personal services business. It needs the result share, own tools and liability for defects.
- Unrelated clients, employment and business premises tests each need the single-client rule to be met (less than the stated share from one client and its associates).
- If the results test fails and the single-client rule fails, the PSI rules apply and only a Commissioner determination can change that.
- Unknown facts that could change the outcome cause an escalation (AU-BUS-001) listing what is missing.

## Small business income tax offset
Rate x basic income tax liability x (net small business income / taxable income, at most 1), capped. Basic income tax liability is tax on taxable income before offsets and excluding Medicare levy. Non-refundable.

## Standard deduction (2026-27)
For assessable labour income only. Not available to a person whose income is only business or investment income. Reduced by work-related expenses claimed. Not additive to business deductions.
