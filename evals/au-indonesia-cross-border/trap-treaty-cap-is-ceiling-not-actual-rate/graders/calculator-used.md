---
type: regex
pattern: 'mcp__plugin_au-accounting_au-tax__\w+'
target: trace
arm: with-only
---

<!--
Skills must not do tax arithmetic in prose (CONVENTIONS section 5: always use the deterministic calculators). Any au-tax MCP call satisfies this grader because the tool name for this domain is chosen by the skill builder, not by the eval author. Tighten to the specific tool name once the builder's tool list is fixed.
-->
At least one au-tax calculator must be called for the figure (arm: with-only).
