"""Trusts and partnerships: beneficiaries' shares of trust net income (proportionate approach with
streaming of capital gains and franked distributions), trustee s99A tax on unallocated net income,
Division 6AA tax on a resident minor's unearned income, and partners' shares of partnership net income
or loss (partnership salaries and interest on capital as profit appropriations).

Law: ITAA 1936 Div 5 (ss90, 92), Div 6 (ss95, 97, 98, 99A), Div 6E, Div 6AA (ss102AC-102AG);
ITAA 1997 Subdiv 115-C, Subdiv 207-B, Subdiv 61-D (s61-115); Income Tax Rates Act 1986 ss12(9), 13,
Sch 7, Sch 11; FCT v Bamford [2010] HCA 10; TR 2005/7. Every rate and threshold comes from
data/rates/<year>.yaml and its overlays via Figures.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.individual import IndividualTaxInput, _apply, _days_in_year, _medicare_levy
from au_tax.figures import FigureError, Figures
from au_tax.registry import Refusal, calculator

EPS = 0.005


def _r(x: float) -> float:
    return round(x + 0.0, 2)


# ================================================================ trust distribution shares

BeneficiaryKind = Literal[
    "resident_individual",
    "resident_minor",
    "resident_individual_legal_disability",
    "non_resident_individual",
    "resident_company",
    "non_resident_company",
    "trust",
    "exempt_entity",
]


class Beneficiary(BaseModel):
    name: str
    kind: BeneficiaryKind = Field(
        "resident_individual",
        description="resident_minor = under 18 on 30 June (a legal disability, so s98 applies); "
        "resident_individual_legal_disability = e.g. bankrupt or lacking capacity; trust = a trustee beneficiary.")
    present_entitlement: float = Field(
        0, ge=0,
        description="Dollar amount of trust income (income of the trust estate as the deed defines it) the beneficiary is "
        "presently entitled to at 30 June, INCLUDING any part that is a specific entitlement to a franked "
        "distribution or (if capital gains form part of trust income) a capital gain.")
    specific_capital_gain: float = Field(
        0, ge=0,
        description="Amount of the capital gain (net financial benefit, after capital losses and before the CGT discount) "
        "the beneficiary is specifically entitled to, recorded in that character within 2 months after year end "
        "(ITAA 1997 s115-228).")
    specific_franked_distribution: float = Field(
        0, ge=0,
        description="Amount of the franked distribution (net financial benefit) the beneficiary is specifically "
        "entitled to, recorded in that character by 30 June (ITAA 1997 s207-58).")
    outside_family_group: bool = Field(
        False, description="True if the trust has made a family trust election and this beneficiary is outside the family group.")


class TrustDistributionInput(BaseModel):
    """One resident trust for one income year. Amounts in AUD."""

    net_income: float = Field(
        description="Net income of the trust estate (ITAA 1936 s95(1)): assessable income calculated as if the trustee were "
        "a resident taxpayer, less allowable deductions. Includes the net capital gain and franked distributions "
        "grossed up by franking credits.")
    trust_income: float = Field(
        description="Income of the trust estate for the year as defined by the trust deed (distributable income).")
    net_capital_gain: float = Field(0, ge=0, description="Net capital gain included in net_income (after losses and any CGT discount).")
    capital_gain: float | None = Field(
        None, ge=0,
        description="The trust's capital gain after capital losses and before the CGT discount (denominator for specific "
        "entitlements). Defaults to net_capital_gain, or twice it when cgt_discount_applied.")
    cgt_discount_applied: bool = Field(
        False, description="True if the trust applied the CGT discount to the gain; beneficiaries then gross up their share (s115-215).")
    capital_gains_in_trust_income: bool = Field(
        True, description="True if the deed makes capital gains part of trust income (so specific entitlements to them come out of trust income).")
    franked_distributions: float = Field(0, ge=0, description="Franked distributions received by the trust (cash amount).")
    franking_credits: float = Field(0, ge=0, description="Franking credits attached to those distributions (included in net_income).")
    franked_distribution_expenses: float = Field(
        0, ge=0, description="Deductions directly relevant to the franked distributions (reduce the attributable amount).")
    beneficiaries: list[Beneficiary] = Field(default_factory=list)
    trust_kind: Literal["discretionary", "fixed", "unit", "hybrid", "deceased_estate", "bankrupt_estate",
                        "foreign", "mit_or_amit", "public_trading_trust"] = "discretionary"
    resolution_by_30_june: bool | None = Field(
        None, description="Whether present entitlements were created by 30 June (or earlier date the deed requires). "
        "False means nobody is presently entitled and the trustee is assessed under s99A unless a default "
        "beneficiary clause applies (deed question).")

    @model_validator(mode="after")
    def _check(self):
        names = [b.name for b in self.beneficiaries]
        if len(set(names)) != len(names):
            raise ValueError("beneficiary names must be unique")
        cg = self.gross_capital_gain()
        if sum(b.specific_capital_gain for b in self.beneficiaries) > cg + EPS:
            raise ValueError("specific capital gain entitlements exceed the capital gain")
        if sum(b.specific_franked_distribution for b in self.beneficiaries) > self.franked_distributions + EPS:
            raise ValueError("specific franked distribution entitlements exceed the franked distributions")
        if self.resolution_by_30_june is not False:
            removed = 0.0
            for b in self.beneficiaries:
                own = self.removed_from_income(b)
                if own > b.present_entitlement + EPS:
                    raise ValueError(f"{b.name}: present_entitlement must include the specific entitlements that form part "
                                     "of trust income")
                removed += own
            adj_ti = self.trust_income - removed
            total_pe = sum(b.present_entitlement - self.removed_from_income(b) for b in self.beneficiaries)
            if total_pe > max(adj_ti, 0.0) + EPS:
                raise ValueError(f"present entitlements ({total_pe:.2f}, excluding streamed amounts) exceed the trust income "
                                 f"available ({adj_ti:.2f})")
        return self

    def gross_capital_gain(self) -> float:
        if self.capital_gain is not None:
            return self.capital_gain
        return self.net_capital_gain * 2 if self.cgt_discount_applied else self.net_capital_gain

    def removed_from_income(self, b: "Beneficiary") -> float:
        return b.specific_franked_distribution + (b.specific_capital_gain if self.capital_gains_in_trust_income else 0.0)


@calculator("trust_distribution_shares", TrustDistributionInput)
def trust_distribution_shares(figures: Figures, inp: TrustDistributionInput) -> dict:
    """Shares of a resident trust's net income for one income year (2025-26 or 2026-27) under ITAA 1936
    Div 6 using the proportionate approach (FCT v Bamford [2010] HCA 10), with streaming of capital gains
    (ITAA 1997 Subdiv 115-C) and franked distributions (Subdiv 207-B) through specific entitlements, and
    Div 6E adjusted net income. Inputs: s95 net income, trust (deed) income, net capital gain, franked
    distributions and franking credits, and each beneficiary's present entitlement and specific
    entitlements. Returns each beneficiary's adjusted Division 6 percentage, share of ordinary net income,
    attributable capital gain (and grossed-up gain), attributable franked distribution and franking credit,
    total amount assessed, the assessing section (s97, or s98 for minors, other legal disabilities and
    non-residents), and the trustee's s99A amount on income nobody is entitled to with s99A tax plus
    Medicare levy. Use for "how is the trust's net income split", "Bamford proportionate approach",
    "streaming a capital gain or franked dividend", "what if the trustee doesn't resolve by 30 June",
    "s99A tax on undistributed income". Flags minors (Div 6AA), corporate beneficiaries (Bendel, s100A),
    family trust distribution tax exposure and PCG 2022/2 red-zone scenario 4 mismatches. Refuses
    AU-TRUST-005/006/007 for foreign, unit/MIT/public trading and deceased or bankrupt estates, and
    AU-TRUST-008 when net income is below the streamed character amounts, and AU-TRUST-004 when net income is a loss."""
    kind = inp.trust_kind
    if kind in ("deceased_estate", "bankrupt_estate"):
        raise Refusal("AU-TRUST-007", f"{kind}: s99/s99A discretion")
    if kind == "foreign":
        raise Refusal("AU-TRUST-005", "foreign or non-resident trust estate")
    if kind in ("mit_or_amit", "public_trading_trust"):
        raise Refusal("AU-TRUST-006", kind)

    assumptions: list[str] = []
    warnings: list[str] = []
    risk_flags: list[str] = []
    s99a_rate = figures.get("trusts.s99a_rate")
    levy_rate = figures.get("medicare.levy_rate")

    ni = inp.net_income
    if ni < 0:
        raise Refusal("AU-TRUST-004", "trust net loss: it stays in the trust and later use depends on the Sch 2F loss tests")
    if ni == 0:
        warnings.append("Net income is nil: no beneficiary or trustee is assessed under Div 6.")
        return {"net_income": _r(ni), "beneficiaries": [], "trustee": {"s99a_amount": 0.0, "s99a_tax": 0.0},
                "assumptions": assumptions, "warnings": warnings, "risk_flags": []}

    cg_net = inp.net_capital_gain
    cg = inp.gross_capital_gain()
    fd = inp.franked_distributions
    fc = inp.franking_credits
    net_fd = max(0.0, fd - inp.franked_distribution_expenses)
    adj_ni = ni - cg_net - net_fd - fc  # Div 6E: net income without the streamed-character amounts
    if adj_ni < -EPS:
        raise Refusal("AU-TRUST-008", f"net income {ni} below net capital gain + net franked distributions + franking credits")
    adj_ni = max(0.0, adj_ni)

    bens = inp.beneficiaries
    no_resolution = inp.resolution_by_30_june is False
    if no_resolution:
        warnings.append("No present entitlement was created by 30 June: unless a default beneficiary clause in the deed "
                        "applies, nobody is presently entitled and the trustee is assessed under s99A on all net income "
                        "(deed question, AU-TRUST-002). Specific entitlements also fail.")
        spec = {b.name: (0.0, 0.0) for b in bens}
        pcts = {b.name: 0.0 for b in bens}
        adj_ti = inp.trust_income
    else:
        spec = {b.name: (b.specific_capital_gain, b.specific_franked_distribution) for b in bens}
        # adjusted trust income: trust income less capital gains / franked distributions any entity is specifically
        # entitled to (ATO "Calculating shares of the franked distribution", step 1)
        adj_ti = inp.trust_income - sum(inp.removed_from_income(b) for b in bens)
        pe_adj = {b.name: b.present_entitlement - inp.removed_from_income(b) for b in bens}
        if adj_ti <= EPS:
            pcts = {b.name: 0.0 for b in bens}
            if adj_ni > EPS:
                warnings.append("Trust income (after streamed amounts) is nil but net income is positive: nobody has a "
                                "Division 6 percentage, so the trustee is assessed under s99A on the ordinary net income "
                                "(Bamford proportionate approach).")
        else:
            pcts = {n: max(0.0, v) / adj_ti for n, v in pe_adj.items()}
    spec_cg = sum(v[0] for v in spec.values())
    spec_fd = sum(v[1] for v in spec.values())
    trustee_pct = max(0.0, 1.0 - sum(pcts.values()))

    unstreamed_cg = max(0.0, cg - spec_cg)
    unstreamed_fd = max(0.0, fd - spec_fd)

    def attrib(name: str | None, pct: float) -> dict:
        s_cg, s_fd = spec.get(name, (0.0, 0.0)) if name else (0.0, 0.0)
        cg_share = s_cg + pct * unstreamed_cg
        fd_share = s_fd + pct * unstreamed_fd
        cg_frac = cg_share / cg if cg else 0.0
        fd_frac = fd_share / fd if fd else 0.0
        att_cg = cg_frac * cg_net
        att_fd = fd_frac * net_fd
        fc_share = fd_frac * fc
        div6 = pct * adj_ni
        return {
            "adjusted_division_6_percentage": round(pct * 100, 4),
            "share_of_ordinary_net_income": _r(div6),
            "attributable_capital_gain": _r(att_cg),
            "capital_gain_grossed_up": _r(att_cg * 2 if inp.cgt_discount_applied else att_cg),
            "attributable_franked_distribution": _r(att_fd),
            "franking_credit": _r(fc_share),
            "total_assessed": _r(div6 + att_cg + att_fd + fc_share),
        }

    out_bens = []
    for b in bens:
        row = {"name": b.name, "kind": b.kind, **attrib(b.name, pcts[b.name])}
        flags: list[str] = []
        if b.kind in ("resident_individual", "resident_company", "trust", "exempt_entity"):
            row["assessed_under"] = "s97 (beneficiary includes the share in own return)"
        elif b.kind == "resident_minor":
            row["assessed_under"] = "s98(1) trustee assessed (legal disability); minor also returns the share with a credit (s100)"
            if row["total_assessed"] > figures.get("trusts.minor_eti_threshold"):
                flags.append("div6aa-minor")
                warnings.append(f"{b.name} is a minor: the share is likely eligible (unearned) income under Div 6AA unless "
                                "excepted (s102AG). Use div6aa_minor_tax.")
        elif b.kind == "resident_individual_legal_disability":
            row["assessed_under"] = "s98(1) trustee assessed (legal disability); beneficiary also returns it with a credit (s100)"
        elif b.kind in ("non_resident_individual", "non_resident_company"):
            row["assessed_under"] = "s98(3) trustee assessed (non-resident beneficiary); beneficiary assessed s98A with a credit"
            flags.append("non-resident-beneficiary")
        if b.kind == "resident_company":
            flags.append("corporate-beneficiary-upe")
        if b.kind == "trust":
            flags.append("trustee-beneficiary-reporting")
        if b.outside_family_group:
            flags.append("ftdt-outside-family-group")
            warnings.append(f"{b.name} is outside the family group of a family trust election: family trust distribution "
                            "tax may apply to the distribution (AU-TRUST-004).")
        cash = b.present_entitlement + (0.0 if inp.capital_gains_in_trust_income else b.specific_capital_gain)
        taxed = row["share_of_ordinary_net_income"] + row["attributable_franked_distribution"] + row["attributable_capital_gain"]
        if taxed - cash > max(1.0, 0.1 * cash) and not no_resolution:  # screen only; franking credits excluded
            flags.append("s100a-red-zone-4-screen")
            warnings.append(f"{b.name} is assessed on more than their entitlement (Bamford mismatch). Where this is "
                            "significant PCG 2022/2 red-zone scenario 4 may be in point (AU-TRUST-001).")
        row["risk_flags"] = flags
        risk_flags.extend(flags)
        out_bens.append(row)

    t = attrib(None, trustee_pct)
    s99a_amount = t["total_assessed"]
    trustee = {
        "adjusted_division_6_percentage": t["adjusted_division_6_percentage"],
        "s99a_amount": s99a_amount,
        "components": {k: t[k] for k in ("share_of_ordinary_net_income", "attributable_capital_gain",
                                         "attributable_franked_distribution", "franking_credit")},
        "s99a_rate": s99a_rate,
        "s99a_tax": _r(s99a_amount * s99a_rate),
        "medicare_levy": _r(s99a_amount * levy_rate),
        "s99a_tax_and_medicare": _r(s99a_amount * (s99a_rate + levy_rate)),
    }
    if s99a_amount > 0:
        risk_flags.append("s99a-unallocated-income")
        assumptions.append("Trustee assessed under s99A (not s99): no Commissioner's discretion assumed. Medicare levy "
                           "added because the trustee pays the top rate on all of it.")
        if t["franking_credit"]:
            assumptions.append("The trustee's share of franking credits is shown in the s99A amount; the trustee may be "
                               "entitled to a matching tax offset (s207-45), not deducted here.")
    if cg_net:
        assumptions.append("Capital gains treated as one pool with the same CGT character; beneficiaries gross up their "
                           "attributable gain" + (" (discount applied by the trust)" if inp.cgt_discount_applied else "")
                           + " and apply their own discount and losses (s115-215).")
    assumptions.append("Present entitlements, specific entitlements and the deed's income definition are as stated; the deed "
                       "was not read (AU-TRUST-002).")
    if inp.resolution_by_30_june is None:
        warnings.append("Resolution timing not stated: present entitlement must exist by 30 June (or earlier if the deed "
                        "says so); franked distribution streaming must be recorded by 30 June and capital gain streaming "
                        "within 2 months after year end.")
    if any(b.kind == "resident_company" for b in bens):
        warnings.append("Corporate beneficiary: after Commissioner of Taxation v Bendel [2026] HCA 18 an unpaid present "
                        "entitlement left untouched is not a Div 7A loan, but Subdiv EA, s100A and steps that turn the "
                        "UPE into a loan still apply (AU-TRUST-011).")
    total_assessed = sum(r["total_assessed"] for r in out_bens) + s99a_amount
    return {
        "net_income": _r(ni),
        "trust_income": _r(inp.trust_income),
        "adjusted_net_income": _r(adj_ni),
        "adjusted_trust_income": _r(adj_ti),
        "beneficiaries": out_bens,
        "trustee": trustee,
        "total_assessed_check": _r(total_assessed),
        "risk_flags": sorted(set(risk_flags)),
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ================================================================ Div 6AA

class Div6AAInput(BaseModel):
    """One minor for one income year. Amounts in AUD, net of the deductions that relate to them."""

    under_18_on_30_june: bool = Field(True, description="Under 18 on the last day of the income year (s102AC(1)(a)).")
    residency: Literal["resident", "non_resident"] = "resident"
    excepted_person: bool = Field(
        False, description="Excepted person under s102AC(2): full-time occupation on 30 June (or 3+ months in the year and "
        "intending to continue), carer allowance or disability support pension, certified disability, double orphan, "
        "principal beneficiary of a special disability trust.")
    unearned_income: float = Field(
        0, ge=0, description="Eligible (non-excepted) assessable income less its deductions: e.g. discretionary trust "
        "distributions, dividends, interest, rent from gifted property. This is the eligible taxable income.")
    excepted_income: float = Field(
        0, ge=0, description="Excepted income less its deductions: employment or own-business income, income from property "
        "inherited or received as compensation, distributions from a deceased estate (s102AE, s102AG).")
    trustee_assessed: bool = Field(False, description="The unearned income is a trust share taxed to the trustee under s98 (same rates, Sch 12).")
    shares_from_multiple_trusts: bool = Field(False, description="Div 6AA trust shares from more than one trust assessed to trustees.")
    special_income_component: bool = Field(False, description="Primary production averaging or abnormal income present.")
    include_medicare_levy: bool = True


@calculator("div6aa_minor_tax", Div6AAInput)
def div6aa_minor_tax(figures: Figures, inp: Div6AAInput) -> dict:
    """Tax on a resident minor's income under ITAA 1936 Div 6AA and Income Tax Rates Act 1986 s13 and
    Sch 11, for 2025-26 or 2026-27. Inputs: unearned (eligible, non-excepted) income net of its deductions,
    excepted income (work, own business, inheritance, compensation, deceased estate) and whether the minor
    is an excepted person. Returns the Div 6AA tax on the eligible taxable income (nil up to the threshold,
    the phase-in cap between the threshold and the phase-out limit, then the flat rate on the whole
    amount), ordinary tax on excepted income, low income tax offset (which cannot reduce tax on unearned
    income), Medicare levy where computable, and the total. Use for "tax on a trust distribution to my
    child", "minor's unearned income", "kids' dividend or interest income", "how much can I distribute
    to a child tax free". Refuses AU-TRUST-009 for non-resident minors, shares from several trusts,
    averaging or special income, since those depend on the Commissioner's discretion."""
    if inp.residency != "resident":
        raise Refusal("AU-TRUST-009", "non-resident minor")
    if inp.shares_from_multiple_trusts:
        raise Refusal("AU-TRUST-009", "shares from several trusts (ITRA s13(4)-(7))")
    if inp.special_income_component:
        raise Refusal("AU-TRUST-009", "special income component")

    assumptions: list[str] = []
    warnings: list[str] = []
    rates = figures.get("individual.resident_rates")
    threshold = figures.get("trusts.minor_eti_threshold")
    phase_rate = figures.get("trusts.minor_phase_in_rate")
    eti_rate = figures.get("trusts.minor_eti_rate")
    top = rates[-1]["rate"]
    phase_out = math.floor(threshold * phase_rate / (phase_rate - top))  # ITRA s13(10)

    def ordinary(x: float) -> float:
        return _apply(rates, max(0.0, x)) if x > 0 else 0.0

    prescribed = inp.under_18_on_30_june and not inp.excepted_person
    ti = inp.unearned_income + inp.excepted_income
    eti = inp.unearned_income if prescribed else 0.0
    applies = prescribed and eti > threshold

    if applies:
        tax_other = ordinary(ti - eti)  # Sch 11 cl 1: other income as if it were the whole taxable income
        full = eti_rate * eti  # Sch 11 cl 2
        tax_eti = full
        basis = "flat rate on the whole eligible taxable income (ITRA Sch 11 Pt I cl 2)"
        if eti <= phase_out:
            cap_a = phase_rate * (eti - threshold)
            cap_b = ordinary(ti) - ordinary(ti - eti)
            cap = max(cap_a, cap_b)
            if cap < full:
                tax_eti = cap
                basis = ("phase-in cap: " + ("phase-in rate on the excess over the threshold" if cap_a >= cap_b
                         else "tax on the eligible income as the top slice at ordinary rates") + " (ITRA s13(2))")
    else:
        tax_other = ordinary(ti)
        tax_eti = 0.0
        if not prescribed:
            basis = ("not a prescribed person: " + ("excepted person (s102AC(2))" if inp.excepted_person else "18 or over on 30 June")
                     + "; ordinary rates on all income")
        else:
            basis = "Div 6AA does not apply: eligible taxable income at or below the threshold (ITRA s13(1)(b)); ordinary rates"

    lito_full = max(0.0, _apply(figures.get("individual.lito"), ti))
    # s61-115: LITO cannot reduce tax on a minor's eligible (Div 6AA) income
    lito = min(lito_full, tax_other)  # s61-115: never against tax on eligible (Div 6AA) income
    income_tax = tax_other - lito + tax_eti

    levy = None
    levy_detail: dict = {}
    if inp.include_medicare_levy:
        try:
            ind = IndividualTaxInput(taxable_income=ti)
            levy, levy_detail = _medicare_levy(figures, ind, ti, _days_in_year(figures), assumptions, warnings)
        except FigureError as e:
            warnings.append(f"Medicare levy not computed: {e}. Income tax figures above are unaffected.")
    total = income_tax + (levy or 0.0)

    if applies:
        assumptions.append("Unearned income treated as eligible taxable income; excepted income taxed at ordinary rates "
                           "with the full tax-free threshold. LITO applied only against tax on excepted income (ITAA 1997 s61-115).")
    if inp.trustee_assessed:
        assumptions.append("Trustee assessed under s98 on the minor's share: same rates (ITRA s13(3), s13(6), Sch 12 Pt I). "
                           "The minor also includes the share and gets a credit for the trustee's tax (s100).")
    return {
        "prescribed_person": prescribed,
        "div6aa_applies": applies,
        "taxable_income": _r(ti),
        "eligible_taxable_income": _r(eti),
        "excepted_income": _r(inp.excepted_income),
        "threshold": threshold,
        "phase_out_limit": phase_out,
        "div6aa_tax": _r(tax_eti),
        "div6aa_basis": basis,
        "tax_on_other_income": _r(tax_other),
        "lito_applied": _r(lito),
        "income_tax": _r(income_tax),
        "medicare_levy": _r(levy) if levy is not None else None,
        "medicare_levy_detail": levy_detail,
        "total_tax": _r(total),
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ================================================================ partnerships

class Partner(BaseModel):
    name: str
    profit_share: float = Field(ge=0, description="Share of residual profit (fraction or percentage; normalised).")
    loss_share: float | None = Field(None, ge=0, description="Share of a partnership loss; defaults to profit_share.")
    salary: float = Field(0, ge=0, description="Partnership salary agreed before year end (a profit appropriation, TR 2005/7).")
    interest_on_capital: float = Field(0, ge=0, description="Interest on capital contributed, if the agreement allocates it (a profit appropriation).")


class PartnershipInput(BaseModel):
    """One partnership for one income year. Amounts in AUD."""

    assessable_income: float | None = Field(None, ge=0, description="Partnership assessable income (s90).")
    deductions: float | None = Field(None, ge=0, description="Allowable deductions, EXCLUDING partner salaries and interest on partners' capital.")
    net_income: float | None = Field(None, description="Net income or (negative) loss if already worked out; overrides the two above.")
    partner_appropriations_deducted: float = Field(
        0, ge=0, description="Partner salaries or interest on capital that were expensed in the accounts and included in "
        "deductions or net_income above; added back (not deductible, TR 2005/7 para 7).")
    partners: list[Partner]
    agreement_before_year_end: bool = Field(True, description="Salary and profit-share agreement made before 30 June (Galland).")
    tax_law_partnership_only: bool = Field(False, description="Co-owners receiving income jointly (e.g. a rental property), not carrying on a business.")
    corporate_limited_partnership: bool = False
    partner_changes_during_year: bool = False

    @model_validator(mode="after")
    def _check(self):
        if self.net_income is None and (self.assessable_income is None or self.deductions is None):
            raise ValueError("give net_income, or both assessable_income and deductions")
        if not self.partners:
            raise ValueError("at least one partner required")
        if sum(p.profit_share for p in self.partners) <= 0:
            raise ValueError("profit shares must sum to more than nil")
        names = [p.name for p in self.partners]
        if len(set(names)) != len(names):
            raise ValueError("partner names must be unique")
        return self


@calculator("partnership_shares", PartnershipInput)
def partnership_shares(figures: Figures, inp: PartnershipInput) -> dict:
    """Net income or partnership loss (ITAA 1936 s90) and each partner's individual interest (s92) for one
    income year. Partnership salaries and interest on partners' capital are profit appropriations, not
    deductions (TR 2005/7): they are added back, allocated first to the extent of available net income,
    and the balance is shared in the profit-sharing ratio. Salary drawn beyond available net income is
    an advance of future profits, not assessable now; salaries cannot create or increase a loss, and a
    loss is shared in the loss ratio. Use for "how do we split partnership profit", "partner salary",
    "is a partner's wage deductible", "partnership loss shares", "statement of distribution on the
    partnership return". Refuses AU-TRUST-010 for corporate limited partnerships, partner changes during
    the year and agreements made after year end."""
    if inp.corporate_limited_partnership:
        raise Refusal("AU-TRUST-010", "corporate limited partnership (Div 5A)")
    if inp.partner_changes_during_year:
        raise Refusal("AU-TRUST-010", "partner joined or left during the year")
    if not inp.agreement_before_year_end:
        raise Refusal("AU-TRUST-010", "agreement made after year end is not effective for that year (Galland)")

    assumptions: list[str] = []
    warnings: list[str] = []
    base = inp.net_income if inp.net_income is not None else (inp.assessable_income - inp.deductions)
    ni = base + inp.partner_appropriations_deducted
    if inp.partner_appropriations_deducted:
        assumptions.append("Partner salaries or interest on capital expensed in the accounts were added back: they are "
                           "distributions of profit, not deductions (TR 2005/7).")
    if inp.tax_law_partnership_only:
        if any(p.salary or p.interest_on_capital for p in inp.partners):
            warnings.append("A partnership in receipt of income jointly (not carrying on business) cannot pay partner "
                            "salaries; income and losses follow the legal interests (TR 93/32 for rental co-owners).")
        assumptions.append("Tax-law partnership (co-owners): shares should match legal ownership interests.")

    tot_p = sum(p.profit_share for p in inp.partners)
    rows = []
    approps = {p.name: p.salary + p.interest_on_capital for p in inp.partners}
    total_approps = sum(approps.values())
    if ni > 0:
        available = min(ni, total_approps)
        scale = available / total_approps if total_approps else 0.0
        residual = ni - available
        if total_approps > ni:
            assumptions.append("Net income is below total salaries and interest on capital; available net income applied to "
                               "them pro rata to the agreed amounts (TR 2005/7 Example 2 has one salaried partner).")
        for p in inp.partners:
            appr = approps[p.name] * scale
            res = residual * p.profit_share / tot_p
            rows.append({"name": p.name, "salary_and_interest_allocated": _r(appr), "residual_share": _r(res),
                         "share_of_net_income": _r(appr + res),
                         "drawings_in_advance_of_profits": _r(approps[p.name] - appr)})
        kind = "net income"
    else:
        losses = [p.loss_share if p.loss_share is not None else p.profit_share for p in inp.partners]
        tot_l = sum(losses)
        if tot_l <= 0:
            raise Refusal("AU-TRUST-002", "loss-sharing ratio not given; the partnership agreement must say how losses are shared")
        for p, ls in zip(inp.partners, losses):
            rows.append({"name": p.name, "salary_and_interest_allocated": 0.0, "residual_share": _r(ni * ls / tot_l),
                         "share_of_net_income": _r(ni * ls / tot_l),
                         "drawings_in_advance_of_profits": _r(approps[p.name])})
        kind = "partnership loss" if ni < 0 else "nil"
        if total_approps:
            assumptions.append("Salaries and interest on capital cannot create or increase a partnership loss; the amounts "
                               "drawn are advances of future profits (TR 2005/7 Example 3).")
    if any(r["drawings_in_advance_of_profits"] > 0 for r in rows):
        warnings.append("Drawings in advance of profits are not assessable now; they are assessable in a later year when "
                        "profits cover them, or repayable if the partnership ends first (TR 2005/7 paras 9, 22-23).")
    return {
        "result": kind,
        "net_income_or_loss": _r(ni),
        "partners": rows,
        "total_allocated": _r(sum(r["share_of_net_income"] for r in rows)),
        "assumptions": assumptions + ["The partnership lodges a return but pays no income tax; each partner includes the "
                                      "share (s92(1)) or deducts the loss share (s92(2))."],
        "warnings": warnings,
    }
