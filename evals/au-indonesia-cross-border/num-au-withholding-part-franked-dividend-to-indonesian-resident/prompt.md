---
name: num-au-withholding-part-franked-dividend-to-indonesian-resident
description: "Australian company pays a 60% franked dividend to an Indonesian resident: withhold 15% on the unfranked part only."
tags: [au-indonesia-cross-border, numeric]
runs: 2
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

We're an Adelaide company (Australian resident for tax). We're paying a A$10,000 dividend, 60% franked, to a shareholder who is an individual tax resident of Indonesia, beneficially entitled to the dividend, and who has given us her Jakarta address. How much dividend withholding tax do we withhold, and how much do we pay her?
