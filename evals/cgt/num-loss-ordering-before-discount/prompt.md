---
name: num-loss-ordering-before-discount
description: "Capital losses applied to non-discountable gain first, then discount."
tags: [cgt, numeric]
runs: 2
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Resident individual, 2026-27. Capital gains this year: shares A held 3 years, gain $40,000; crypto B held 5 months, gain $10,000. I also have a current-year capital loss of $12,000 and a carried-forward net capital loss of $6,000 from 2023-24. Apply the losses in whichever way gives me the lowest net capital gain and tell me the net capital gain for 2026-27.
