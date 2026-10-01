---
type: regex
pattern: '\bAU-(?:IND-001)\b[\s\S]*\bAU-(?:COMP-004|TRUST-011)\b|\bAU-(?:COMP-004|TRUST-011)\b[\s\S]*\bAU-(?:IND-001)\b'
target: last_message
---

<!--
Two limbs, both required. AU-IND-001 trigger: individual scenario outside the calculator scope, including employment termination payments (fires on: $60,000 redundancy lump sum). AU-COMP-004 trigger: trust UPE owed to a private company where Subdiv EA or s 100A is in issue (fires on: $40,000 UPE owed to the family company over three years). AU-TRUST-011 trigger: Division 7A or Subdiv EA consequences of a corporate beneficiary's UPE beyond the post-Bendel position; either is correct for that limb.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IND-001 and AU-COMP-004 or AU-TRUST-011).
