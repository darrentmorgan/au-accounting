---
name: trap-2627-medicare-lowincome-unpublished
description: "Trap: 2026-27 Medicare low-income thresholds are not published."
tags: [individual-tax, trap]
runs: 2
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, mcp__plugin_au-accounting_au-tax__individual_income_tax, mcp__plugin_au-accounting_au-tax__get_figure]
---

What's my Medicare levy on $30,000 taxable income in 2026-27? Single, no dependants, resident.
