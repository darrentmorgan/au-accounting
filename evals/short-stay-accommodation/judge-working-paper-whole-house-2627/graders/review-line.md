---
type: regex
pattern: '[Ww]orking [Pp]aper only\W+[Rr]eview by a registered tax agent'
target: last_message
---

<!--
CONVENTIONS.md section 8 output contract item 6: the review line 'Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use.' must end the working paper. The regex matches the line's opening, tolerating punctuation differences.
-->
The working paper ends with the standard review line.
