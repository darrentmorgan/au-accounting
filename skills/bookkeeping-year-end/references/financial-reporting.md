# Financial reporting (companies)

## Who must prepare a financial report (Corporations Act 2001 Ch 2M)
- Large proprietary companies, public companies (except small companies limited by guarantee), disclosing entities, registered schemes and similar entities must prepare an annual financial report and directors' report (s 292). The tool `large_proprietary_test` covers only the proprietary company split.
- Small proprietary companies are exempt unless: foreign-controlled, having crowd-sourced funding shareholders, directed by ASIC (s 294), or directed by qualifying shareholders (s 293). Foreign-controlled companies may have relief in ASIC instruments; that is an ASIC relief question (AU-BKP-001 if the company wants to rely on it and the position is unclear).
- All proprietary companies must keep financial records that would allow true and fair statements to be prepared and audited (s 286), whether or not they must prepare a report.

## Size test (s 45A and Corporations Regulations reg 1.0.02B)
- Tested for the company and the entities it controls, on consolidated revenue for the year, consolidated gross assets at year end, and employees at year end (part-timers as a fraction of full-time equivalent). Two of the three thresholds must be met or exceeded for "large"; otherwise "small". Thresholds are figures under `asic.large_proprietary_*`.
- Whether the company controls another entity follows AASB 10; if unclear, the tool refuses (AU-BKP-001).
- Consequences for a large company: financial report audited, sent to members and lodged with ASIC due `bookkeeping.financial_report_lodgement_months` months after year end (s 319). Some large companies may have audit relief under ASIC instruments (wholly-owned company or grandfathered company relief); that needs confirmation from a registered company auditor or the ASIC instrument itself.

## Types of financial statements
- **General purpose (GPFS)**: Tier 1 (full recognition, measurement and disclosure) or Tier 2 (same recognition and measurement, reduced disclosure under AASB 1060).
- **Special purpose (SPFS)**: available only to entities that are not reporting entities. Whether an entity is a reporting entity turns on whether users depend on general purpose statements (SAC 1 factors). This is a judgement for the accountant. The AASB has consulted on removing SPFS for certain for-profit private sector entities; check the AASB site before advising a large proprietary company that has been using SPFS.
- **AASB 18** replaces AASB 101 for for-profit entities for periods beginning on or after 1 Jan 2027, changing the profit or loss structure and adding management-defined performance measures disclosure. AASB 1060 alignment is being progressed separately. Flag this to a large company with a 30 June 2028 year end onward, and for early adopters.

## Small companies: what to do anyway
- Keep the ledger to a standard that would support a compilation if a lender, shareholder or ASIC asks.
- Prepare accounting profit to tax reconciliation and the balance sheet loan accounts for the tax return regardless.
- Lodge the ASIC annual review and keep company records (registers, minutes, resolutions).

## Escalate
Audits, consolidated groups, disputed reporting entity status, revenue for multiple-element or long-term contracts, lease accounting (AASB 16), impairment, business combinations, financial instruments, and any ASIC relief application: AU-BKP-001.
