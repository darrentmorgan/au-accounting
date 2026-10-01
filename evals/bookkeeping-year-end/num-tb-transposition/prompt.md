---
name: num-tb-transposition
description: "Trial balance out of balance by a transposition error."
tags: [bookkeeping-year-end, numeric]
runs: 2
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

My trial balance at 30 June 2026 does not balance. Total debits are $186,940.00 and total credits are $186,400.00. I compared a handful of postings with the source documents:
- Electricity: invoice $1,287.00, ledger $1,827.00
- Stationery: invoice $342.00, ledger $342.00
- Software subscription: invoice $199.00, ledger $199.00
- Freight: invoice $2,450.00, ledger $2,450.00
What is the difference, what error type is it, which posting is wrong, and what should total debits be once fixed?
