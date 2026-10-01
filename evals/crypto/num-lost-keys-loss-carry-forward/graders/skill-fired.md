---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"au-accounting:(?:crypto|cgt)"'
min: 1
---

The crypto skill (or the cgt skill it hands the arithmetic to) must fire.

<!-- Non-trigger case: the crypto skill owns the topic, but the cgt skill may legitimately fire for the arithmetic. Trigger cases keep the strict crypto name. -->
