"""Income-year individual settlement; credit eligibility is a classified input, never inferred.

ITAA 1997 ss63-10, 67-25, 207-20 and Subdiv 61-G; TAA 1953 Sch1 ss18-15, 45-30.
Uses the individual calculator for all tax components and the selected year's PHI figures.
Does not compute an ATO running account balance or company/trust assessments.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from au_tax.calculators.individual import IndividualTaxInput, individual_income_tax
from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator


class FrankingCreditInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    income_year: str
    credit: float = Field(ge=0)
    gross_up_included: bool = Field(description="Dividend AND this franking gross-up already included once in taxable income.")
    refundable_eligibility_confirmed: bool = Field(
        description="Resident individual's entitlement confirmed, including qualified-person/holding-period, "
        "related-payment and integrity rules; not inferred from a company's maximum credit.")


class PrivateHealthPolicyRow(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    period: Literal["1jul_to_31mar", "1apr_to_30jun"]
    age_band: Literal["under_65", "65_69", "70_plus"] = Field(
        description="Oldest covered person's applicable age band for this premium row; split when it changes.")
    eligible_premium: float = Field(
        ge=0, description="This taxpayer's allocated rebate-eligible premium before premium reductions, "
        "excluding lifetime health cover loading; not the net cash premium.")
    rebate_received: float = Field(ge=0, description="Premium reduction/rebate already received for this allocated row.")


class PrivateHealthRebateInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    income_year: str
    eligibility_and_allocation_confirmed: bool = Field(
        description="PHI eligibility, registered complying insurer/policy, tax claim code and this taxpayer's "
        "allocation confirmed. Unresolved spouse claims, changing family status or eligibility must refuse.")
    income_for_rebate: float = Field(
        ge=0, description="Confirmed income for surcharge purposes for PHI; combined family income if family. "
        "Includes applicable add-backs; never infer from taxable income alone.")
    family: bool = Field(description="Confirmed PHI family status on 30 June; can differ from policy type.")
    dependent_children: int = Field(ge=0, description="Qualifying PHI dependent children for the family threshold increase.")
    rows: list[PrivateHealthPolicyRow] = Field(min_length=1)


class IndividualSettlementInput(IndividualTaxInput):
    model_config = ConfigDict(allow_inf_nan=False)

    tax_withheld: float = Field(ge=0, description="Confirmed PAYG withholding for this income year, zero if none.")
    payg_instalment_credit: float = Field(
        ge=0, description="ATO-reconciled income-year instalment credit under Sch1 s45-30, net of variations/credits. "
        "Not an instalment estimate or arbitrary payment; unpaid instalments remain separate account debts.")
    franking: FrankingCreditInput | None = Field(description="Confirmed credit/gross-up facts; explicit null confirms none.")
    private_health_rebate: PrivateHealthRebateInput | None = Field(
        description="All this taxpayer's allocated PHI statement rows; explicit null confirms no rebate adjustment.")
    unmodelled_inputs: list[str] = Field(
        description="Required reconciliation inventory. Empty only after confirming no other offsets/credits, "
        "unresolved facts or assessment adjustments. Name FITO, SBITO, trust complications etc. if present.")


def _money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _stop(detail: str) -> None:
    raise Refusal("AU-IND-005", detail)


def _phi(figures: Figures, inp: PrivateHealthRebateInput | None) -> dict:
    if inp is None:
        return {"entitlement": 0.0, "rebate_received": 0.0, "refundable_offset": 0.0,
                "excess_rebate_liability": 0.0, "rows": []}
    if inp.income_year != figures.income_year:
        _stop("PHI rows belong to a different income year.")
    if not inp.eligibility_and_allocation_confirmed:
        _stop("PHI eligibility, tax claim code or premium allocation is unresolved.")
    if not inp.family and inp.dependent_children:
        _stop("PHI dependent children supplied with single income thresholds.")
    shift = (figures.get("medicare.mls_family_per_child_after_first") * max(0, inp.dependent_children - 1)
             if inp.family else 0)
    rows = []
    entitlement = received = Decimal("0.00")
    for row in inp.rows:
        key = f"medicare.phi_rebate_{row.period}_{row.age_band}"
        tiers = figures.get(key)
        # PHI uses the family income-for-surcharge threshold increase for children after the first.
        tier = next(t for t in tiers if (
            (t["family_to"] if inp.family else t["to"]) is None
            or inp.income_for_rebate <= (t["family_to"] + shift if inp.family else t["to"])))
        earned = _money(Decimal(str(row.eligible_premium)) * Decimal(str(tier["rate"])))
        paid = _money(row.rebate_received)
        entitlement += earned
        received += paid
        rows.append({"period": row.period, "age_band": row.age_band, "figure_key": key,
                     "rate": tier["rate"], "eligible_premium": float(_money(row.eligible_premium)),
                     "entitlement": float(earned), "rebate_received": float(paid)})
    adjustment = entitlement - received
    return {"entitlement": float(entitlement), "rebate_received": float(received),
            "refundable_offset": float(max(Decimal(0), adjustment)),
            "excess_rebate_liability": float(max(Decimal(0), -adjustment)), "rows": rows}


@calculator("individual_tax_settlement", IndividualSettlementInput)
def individual_tax_settlement(figures: Figures, inp: IndividualSettlementInput) -> dict:
    """Deterministic individual income-year refund/amount owing, after LITO/WATO, Medicare/MLS and HELP.
    Nets confirmed PAYG withholding, reconciled PAYG instalment credits, eligible refundable franking credits
    (dividend and gross-up must already be in taxable income), and PHI rebate entitlement less rebate received.
    Supply every settlement field: explicit null for absent franking/PHI and zero for absent PAYG credits.
    PHI rows split premium payment periods and oldest-person age bands; use the selected year's Figures.
    Refuses AU-IND-005 for ANY unmodelled input, unresolved component limitation, entitlement or draft.
    Other offsets, company/trust assessments and ATO account balances are outside scope. Never pass an
    after-franking or after-PHI tax amount as taxable income. Recomputes tax; does not trust a supplied liability.
    """
    if inp.unmodelled_inputs:
        _stop("Unmodelled inputs: " + ", ".join(inp.unmodelled_inputs))
    if inp.franking is not None:
        if inp.franking.income_year != figures.income_year:
            _stop("Franking credit belongs to a different income year.")
        if inp.residency != "resident" or not inp.franking.refundable_eligibility_confirmed:
            _stop("Refundable franking-credit eligibility is unresolved or outside the resident-individual scope.")
        if not inp.franking.gross_up_included:
            _stop("Dividend and franking gross-up must be included once in taxable income before settlement.")

    # Remove settlement fields before invoking the existing tax model; no supplied total is accepted.
    tax_input = IndividualTaxInput.model_validate({
        name: getattr(inp, name) for name in IndividualTaxInput.model_fields
    })
    tax_input.tax_withheld = None  # do not expose a competing withholding-only estimate in this result
    tax = individual_income_tax(figures, tax_input)
    if tax["limitations"]:
        _stop("Unresolved tax components: " + ", ".join(x["id"] for x in tax["limitations"]))
    phi = _phi(figures, inp.private_health_rebate)
    if figures.draft:
        _stop("A final settlement cannot use draft figures.")

    credit = _money(inp.franking.credit if inp.franking is not None else 0)
    withholding, instalments = _money(inp.tax_withheld), _money(inp.payg_instalment_credit)
    # Non-refundable offsets are already capped against income tax in the component calculator.
    # Refundable offsets are not capped at income tax; they can fund levy/MLS or generate a refund.
    liability = _money(tax["total_liability"]) + _money(phi["excess_rebate_liability"])
    credits = withholding + instalments + credit + _money(phi["refundable_offset"])
    balance = liability - credits
    rate_source = {"resident": "tax-rates-australian-residents", "foreign": "tax-rates-foreign-residents",
                   "whm": "tax-rates-working-holiday-makers"}[inp.residency]
    rules = [
        ("income_tax", "Income Tax Rates Act 1986 Sch7; selected income-year resident/foreign/WHM rates",
         "https://www.ato.gov.au/tax-rates-and-codes/" + rate_source),
        ("non_refundable_offset_order", "ITAA 1997 s63-10; Subdiv 61-D (and Subdiv 61-E from 2027-28)",
         "https://www.ato.gov.au/law/view/document?docid=PAC/19970038/63-10"),
        ("medicare_levy_and_mls", "Medicare Levy Act 1986 ss6-9, 8B-8D; selected income-year figures",
         "https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy"),
        ("study_loan_repayment", "Higher Education Support Act 2003; offsets do not reduce repayment income",
         "https://www.ato.gov.au/tax-rates-and-codes/study-and-training-support-loans-rates-and-repayment-thresholds"),
        ("franking_gross_up_and_credit", "ITAA 1997 s207-20 (entitlement subject to s207-145)",
         "https://www.ato.gov.au/law/view/document?docid=PAC/19970038/207-20"),
        ("franking_refundability", "ITAA 1997 s67-25 and Div67",
         "https://www.ato.gov.au/law/view/document?docid=PAC/19970038/67-25"),
        ("phi_reconciliation", "ITAA 1997 Subdiv61-G; PHI Act 2007 rebate reconciliation",
         "https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/private-health-insurance-rebate/claiming-the-private-health-insurance-rebate"),
        ("payg_withholding_credit", "TAA 1953 Sch1 s18-15",
         "https://www.ato.gov.au/law/view/document?docid=PAC/19530001/Sch1-18-15"),
        ("payg_instalment_credit", "TAA 1953 Sch1 s45-30 (unpaid instalment liability remains)",
         "https://www.ato.gov.au/law/view/document?docid=PAC/19530001/Sch1-45-30"),
        ("account_credit_allocation", "PS LA 2011/21 Attachment A (PAYG credit priority for study loans)",
         "https://www.ato.gov.au/law/view/view.htm?docid=PSR/PS201121/NAT/ATO/00001"),
    ]
    return {
        "settlement_complete": True, "settlement_status": "complete", "limitations": [],
        "completeness_scope": "Income-year individual assessment on confirmed inputs; excludes ATO account debts, "
                              "refund retention, interest and penalties. Not a notice of assessment or cash refund guarantee.",
        "tax_components": tax, "private_health_rebate": phi,
        "liability_including_phi_excess": float(liability),
        "credits": {"payg_withheld": float(withholding), "payg_instalments": float(instalments),
                    "refundable_franking": float(credit), "phi_refundable_offset": phi["refundable_offset"]},
        "total_credits": float(credits), "net_amount_owing": float(balance),
        "refund": float(max(Decimal(0), -balance)), "amount_owing": float(max(Decimal(0), balance)),
        "rule_authorities": [{"rule": rule, "authority": authority, "source": source,
                              "income_year": figures.income_year} for rule, authority, source in rules],
        "assumptions": [a for a in tax["assumptions"] if not a.startswith("Only LITO")] + [
            "Non-refundable LITO/WATO are capped in the tax components; refundable credits are applied in settlement.",
            "Credits and PHI rows are confirmed, allocated income-year inputs. Credit eligibility has not been inferred.",
            "Dividend and franking gross-up are already in taxable income once; settlement does not gross up again.",
            "PHI entitlement is rounded to cents per supplied statement row; aggregate duplicate portions of the same row.",
        ],
        "warnings": ["ATO account debts, including unpaid instalments, may reduce a cash refund or increase the "
                     "account amount owing; reconcile the account separately."],
    }
