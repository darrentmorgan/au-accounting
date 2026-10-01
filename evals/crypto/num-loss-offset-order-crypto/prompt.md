---
name: num-loss-offset-order-crypto
description: "Crypto losses are applied to the non-discountable gain first, then the discount, via net_capital_gain."
tags: [crypto, cgt, numeric]
runs: 2
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Resident individual, 2026-27, investor. This income year I sold ETH held 20 months for a gain of $24,000, and SOL held 4 months for a gain of $6,000. I also sold a dead altcoin for a capital loss of $9,500, and I carry forward a net capital loss of $2,500 from 2024-25. Apply the losses in whatever order gives me the lowest net capital gain and tell me the net capital gain for 2026-27.
