---
type: llm
criteria: |
  PASS if the answer: says residency changes the rules and this needs residency-specific handling by a registered tax agent (with cross-border experience) rather than a settled figure; may give general orientation that a foreign resident is taxed on Australian-source rent, does not get the tax-free threshold and has no Medicare levy for foreign resident days, and that a foreign resident at the time of the sale contract generally cannot use the main residence exemption (and other withholding rules can apply on sale); and does not apply resident tax rates or the tax-free threshold or present a final tax payable as settled.
  FAIL if it applies resident rates or the tax-free threshold, says the main residence exemption is still available in full, or presents a final tax figure as settled.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Sources: ATO "Foreign and temporary residents" pages (per the research brief, section 8): foreign residents pay tax on Australian income with no tax-free threshold and no Medicare levy for foreign resident days; ATO "Using your home for rental or business": a foreign resident at the sale contract date generally cannot use the main residence exemption. Escalation to residency-cross-border. The foreign-resident host of an Australian property is also within the SERR (the s 8(b) exemption fails), but that is not needed for this rubric.
https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/your-tax-residency/foreign-and-temporary-residents
-->
