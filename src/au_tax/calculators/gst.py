"""GST and BAS: BAS GST calculation worksheet (G1-G20, 1A, 1B, simpler BAS, W labels), margin scheme GST,
GST registration test, and BAS lodgment due dates.

Law: A New Tax System (Goods and Services Tax) Act 1999 (GSTA) s9-70 (rate), Div 21 (bad debts), s23-5,
s23-15, s144-5 and Div 188 (registration and GST turnover), Div 29 (attribution, tax invoices), s75-5,
s75-10 (margin scheme), s84-5 (reverse charge); TAA 1953 Sch 1 s14-250 (GST at settlement withholding).
ATO BAS instructions (Steps 1-4) for the label arithmetic. Every rate and threshold comes from
data/rates/<year>.yaml and data/rates/<year>.d/gst.yaml via Figures.
"""

from __future__ import annotations

import math
import datetime as dt
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import Figures
from au_tax.holidays import COMMONWEALTH, roll_due_date
from au_tax.registry import Refusal, calculator


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _whole(x: float) -> int:
    """BAS labels are whole dollars, cents dropped (ATO: round down, don't show cents)."""
    return int(math.floor(x + 1e-9)) if x >= 0 else -int(math.floor(-x + 1e-9))


def _fraction(figures: Figures) -> float:
    """GST fraction of a GST-inclusive taxable amount: rate / (1 + rate), i.e. 1/11."""
    rate = figures.get("gst.rate")
    return rate / (1 + rate)


# ---------------------------------------------------------------- BAS worksheet

SaleClass = Literal["taxable", "export_goods", "gst_free", "input_taxed", "margin_scheme", "out_of_scope"]
PurchaseClass = Literal["taxable", "gst_free", "input_taxed_use", "private", "reverse_charge", "out_of_scope"]
AdjustmentReason = Literal[
    "bad_debt_written_off_by_supplier",  # s21-5 decreasing (supplier)
    "bad_debt_recovered_by_supplier",    # s21-10 increasing (supplier)
    "bad_debt_recipient_unpaid",         # s21-15 increasing (recipient)
    "bad_debt_recipient_later_paid",     # s21-20 decreasing (recipient)
    "other_increasing",
    "other_decreasing",
]
_INCREASING = {"bad_debt_recovered_by_supplier", "bad_debt_recipient_unpaid", "other_increasing"}
_BAD_DEBT = {"bad_debt_written_off_by_supplier", "bad_debt_recovered_by_supplier",
             "bad_debt_recipient_unpaid", "bad_debt_recipient_later_paid"}


class Transaction(BaseModel):
    """One sale or purchase. Amounts in AUD."""

    kind: Literal["sale", "purchase"]
    amount: float = Field(ge=0, description="Price. GST-inclusive if gst_inclusive is true, else GST-exclusive. "
                          "For reverse_charge purchases: the amount paid to the offshore supplier (no GST charged).")
    gst_inclusive: bool = Field(True, description="True if amount includes GST (only matters for taxable items).")
    classification: str = Field(
        description="Sales: taxable | export_goods (GST-free export of goods, G2) | gst_free (other GST-free incl. "
        "GST-free services to non-residents, basic food, health, education, going concern, G3) | input_taxed "
        "(residential rent, sale of existing residential premises, financial supplies, G4) | margin_scheme (sale "
        "of real property under the margin scheme; give margin) | out_of_scope (not reported: wages received, "
        "dividends, loans, private sales). Purchases: taxable (GST in the price) | gst_free (no GST in the price, "
        "G14) | input_taxed_use (for making input taxed sales, G13) | private (private or not income tax "
        "deductible, G15) | reverse_charge (imported service or digital product, s84-5) | out_of_scope (wages, "
        "super, loan repayments, dividends: not reported).")
    capital: bool = Field(False, description="Purchases: capital item (G10) rather than non-capital (G11).")
    creditable_share: float = Field(1.0, ge=0, le=1, description="Taxable or reverse_charge purchases: share used "
                                    "for a creditable (business, non-input-taxed) purpose. The rest goes to G15 or G13.")
    non_creditable_reason: Literal["private", "input_taxed_use"] = Field(
        "private", description="Where creditable_share < 1: whether the rest is private/non-deductible (G15) or for input taxed sales (G13).")
    margin: float | None = Field(None, description="margin_scheme sales: the margin (sale price less acquisition cost or approved valuation).")
    tax_invoice_held: bool | None = Field(None, description="Taxable purchases: whether a valid tax invoice is held. "
                                          "False above the tax invoice threshold defers the credit.")
    date: dt.date | None = Field(None, description="Attribution date: accruals basis = earlier of invoice issue or "
                              "any payment; cash basis = date paid/received. Outside period_start..period_end is excluded.")
    amount_paid: float | None = Field(None, ge=0, description="Cash basis only: amount actually paid or received in "
                                      "the period, in the same GST basis as amount. Defaults to the full amount.")
    description: str = ""

    @model_validator(mode="after")
    def _check(self):
        sale = {"taxable", "export_goods", "gst_free", "input_taxed", "margin_scheme", "out_of_scope"}
        purch = {"taxable", "gst_free", "input_taxed_use", "private", "reverse_charge", "out_of_scope"}
        allowed = sale if self.kind == "sale" else purch
        if self.classification not in allowed:
            raise ValueError(f"classification {self.classification!r} not valid for a {self.kind}; use one of {sorted(allowed)}")
        if self.classification == "margin_scheme" and self.margin is None:
            raise ValueError("margin_scheme sale needs margin (use margin_scheme_gst to work it out)")
        return self


class Adjustment(BaseModel):
    gst_amount: float = Field(ge=0, description="GST amount of the adjustment (1/11 of the GST-inclusive amount written off, recovered, etc.).")
    reason: AdjustmentReason
    description: str = ""


class PaygWithholding(BaseModel):
    w1: float = Field(0, ge=0, description="W1 total salary, wages and other payments.")
    w2: float = Field(0, ge=0, description="W2 amounts withheld from payments at W1.")
    w4: float = Field(0, ge=0, description="W4 amounts withheld where no ABN quoted.")
    w3: float = Field(0, ge=0, description="W3 other amounts withheld.")


class BasWorksheetInput(BaseModel):
    """GST for one BAS period from a list of transactions (calculation worksheet method)."""

    transactions: list[Transaction] = Field(default_factory=list)
    adjustments: list[Adjustment] = Field(default_factory=list)
    accounting_basis: Literal["accrual", "cash"] = Field("accrual", description="GST accounting basis (s29-40 cash basis needs eligibility).")
    period_start: dt.date | None = None
    period_end: dt.date | None = None
    reporting_method: Literal["auto", "full", "simpler"] = Field(
        "auto", description="simpler = Simpler BAS (G1, 1A, 1B only). auto uses gst_turnover if given, else full.")
    gst_turnover: float | None = Field(None, ge=0, description="Annual GST turnover, to choose Simpler BAS vs full reporting.")
    payg_withholding: PaygWithholding | None = None
    gst_registered: bool = True
    special_circumstances: list[Literal["gst_group_or_branch", "financial_supply_apportionment",
                                        "property_development", "commercial_residential_premises",
                                        "complex_international", "fuel_tax_credits"]] = Field(
        default_factory=list, description="Anything present here stops the calculation with the matching refusal.")


_SPECIAL_CODES = {
    "property_development": "AU-GST-001",
    "commercial_residential_premises": "AU-GST-002",
    "financial_supply_apportionment": "AU-GST-003",
    "gst_group_or_branch": "AU-GST-004",
    "complex_international": "AU-GST-005",
    "fuel_tax_credits": "AU-GST-007",
}


@calculator("bas_gst_worksheet", BasWorksheetInput)
def bas_gst_worksheet(figures: Figures, inp: BasWorksheetInput) -> dict:
    """Australian BAS GST calculation worksheet for one tax period. Give a list of sales and purchases, each with
    amount, gst_inclusive flag, classification (sales: taxable, export_goods, gst_free, input_taxed,
    margin_scheme, out_of_scope; purchases: taxable, gst_free, input_taxed_use, private, reverse_charge,
    out_of_scope), capital flag, creditable_share for mixed use, optional date and tax_invoice_held, plus
    Division 19/21 adjustments as GST amounts. Returns every worksheet label G1-G20 (GST-inclusive, cents),
    the whole-dollar BAS labels to report (full: G1, G2, G3, G10, G11, 1A, 1B; Simpler BAS: G1, 1A, 1B),
    net GST payable or refundable, optional PAYG withholding labels W1, W2, W4, W3, W5, and warnings. Use for
    "do my BAS", "what goes at G1/1A/1B", "how much GST do I owe this quarter", "GST on sales and purchases".
    Cash vs accrual attribution by date and amount_paid. Refuses AU-GST-001..007 for special cases."""
    for sc in inp.special_circumstances:
        raise Refusal(_SPECIAL_CODES[sc], sc)
    frac = _fraction(figures)
    rate = figures.get("gst.rate")
    inv_threshold = figures.get("gst.tax_invoice_threshold_incl_gst")
    assumptions: list[str] = ["Calculation worksheet method: all G amounts include GST; 1A = G8/11 and 1B = G20/11 (ATO BAS instructions, Steps 2 and 4)."]
    warnings: list[str] = []
    risk_flags: list[str] = []
    if not inp.gst_registered:
        warnings.append("Not registered for GST: no GST on sales and no credits. Check the registration test (gst_registration_check); if registration was required, GST is payable from that date.")

    g = {k: 0.0 for k in ("G1", "G2", "G3", "G4", "G7", "G10", "G11", "G13", "G14", "G15", "G18")}
    excluded: list[dict] = []
    deferred_credits = 0.0

    def in_period(t: Transaction) -> bool:
        if t.date is None or (inp.period_start is None and inp.period_end is None):
            return True
        if inp.period_start and t.date < inp.period_start:
            return False
        if inp.period_end and t.date > inp.period_end:
            return False
        return True

    for i, t in enumerate(inp.transactions):
        label = t.description or f"transaction {i + 1}"
        if not in_period(t):
            excluded.append({"item": label, "reason": "attribution date outside the period"})
            continue
        amt = t.amount
        if inp.accounting_basis == "cash" and t.amount_paid is not None:
            amt = min(t.amount_paid, t.amount)
            if t.amount_paid < t.amount:
                assumptions.append(f"{label}: cash basis, only the part paid in the period is attributed (s29-5(2), s29-10(2)).")
        elif inp.accounting_basis == "accrual" and t.amount_paid is not None and t.amount_paid < t.amount:
            assumptions.append(f"{label}: accruals basis attributes the whole amount once invoiced or any payment is made (s29-5(1)); amount_paid ignored.")
        # GST-inclusive value for taxable items
        taxable_like = (t.kind == "sale" and t.classification == "taxable") or (
            t.kind == "purchase" and t.classification == "taxable")
        incl = amt * (1 + rate) if (taxable_like and not t.gst_inclusive) else amt

        if t.kind == "sale":
            c = t.classification
            if c == "out_of_scope":
                excluded.append({"item": label, "reason": "not a sale for GST (not reported at G1)"})
                continue
            if c == "margin_scheme":
                m = t.margin or 0.0
                if m > 0:
                    g["G1"] += m
                else:
                    warnings.append(f"{label}: margin is nil or negative, so nothing is reported at G1 and no GST is payable (ATO margin scheme BAS instructions).")
                continue
            g["G1"] += incl
            if c == "export_goods":
                g["G2"] += incl
            elif c == "gst_free":
                g["G3"] += incl
            elif c == "input_taxed":
                g["G4"] += incl
            continue

        # purchases
        c = t.classification
        if c == "out_of_scope":
            excluded.append({"item": label, "reason": "not a purchase for GST (wages, super, loans, dividends etc. are not reported at G10/G11)"})
            continue
        box = "G10" if t.capital else "G11"
        if c == "taxable" and t.tax_invoice_held is False and (
                t.amount if t.gst_inclusive else t.amount * (1 + rate)) > inv_threshold:
            deferred_credits += incl * t.creditable_share
            excluded.append({"item": label, "reason": "no tax invoice held: report it (and claim the credit) in the period you hold one (s29-10(3))"})
            warnings.append(f"{label}: no tax invoice held for a purchase above the tax invoice threshold; the credit cannot be claimed until you hold one (s29-10(3)). Left out of this period.")
            risk_flags.append("GST-RF-008")
            continue
        if c == "reverse_charge":
            if t.creditable_share >= 1:
                g[box] += amt
                g["G14"] += amt
                assumptions.append(f"{label}: imported service used wholly for a creditable purpose, so the reverse charge does not apply (s84-5(1)(b)); reported at {box} and G14 with no GST.")
                continue
            val = amt * (1 + rate)
            g["G1"] += val  # ATO: report price x 1.1 at G1 and at G10/G11
            g[box] += val
            g["G13" if t.non_creditable_reason == "input_taxed_use" else "G15"] += val * (1 - t.creditable_share)
            assumptions.append(f"{label}: reverse charge (s84-5): price x 1.1 reported at G1 and {box}; GST of {_r(amt * rate)} payable, credit for the creditable share only.")
            risk_flags.append("GST-RF-011")
            continue
        g[box] += incl
        if c == "gst_free":
            g["G14"] += incl
        elif c == "input_taxed_use":
            g["G13"] += incl
            risk_flags.append("GST-RF-002")
        elif c == "private":
            g["G15"] += incl
        else:  # taxable
            if t.creditable_share < 1:
                g["G13" if t.non_creditable_reason == "input_taxed_use" else "G15"] += incl * (1 - t.creditable_share)
                if t.non_creditable_reason == "private":
                    risk_flags.append("GST-RF-004")

    for a in inp.adjustments:
        if a.reason in _BAD_DEBT and inp.accounting_basis == "cash":
            warnings.append(f"Adjustment '{a.description or a.reason}' ignored: Division 21 bad debt adjustments are not available on a cash basis (s21-5(2), s21-15(2)).")
            risk_flags.append("GST-RF-009")
            continue
        if a.reason in _INCREASING:
            g["G7"] += a.gst_amount / frac
        else:
            g["G18"] += a.gst_amount / frac
        if a.reason in _BAD_DEBT:
            assumptions.append("Bad debt adjustments: written off or overdue 12 months or more, accruals basis (Div 21; GSTR 2000/2). Increasing adjustments at G7, decreasing at G18.")

    g["G5"] = g["G2"] + g["G3"] + g["G4"]
    g["G6"] = g["G1"] - g["G5"]
    g["G8"] = g["G6"] + g["G7"]
    g["G9"] = g["G8"] * frac
    g["G12"] = g["G10"] + g["G11"]
    g["G16"] = g["G13"] + g["G14"] + g["G15"]
    g["G17"] = g["G12"] - g["G16"]
    g["G19"] = g["G17"] + g["G18"]
    g["G20"] = g["G19"] * frac
    if g["G8"] < 0 or g["G19"] < 0:
        warnings.append("A subtotal is negative; the BAS cannot show negative figures. Check adjustments (decreasing sales adjustments belong at G18).")

    method = inp.reporting_method
    if method == "auto":
        if inp.gst_turnover is not None:
            method = "simpler" if inp.gst_turnover < figures.get("gst.simpler_bas_turnover_max") else "full"
        else:
            method = "full"
            assumptions.append("GST turnover not given: full reporting labels shown; Simpler BAS (G1, 1A, 1B) applies below the Simpler BAS turnover limit.")
    one_a, one_b = g["G9"], g["G20"]
    report_labels = ["G1", "1A", "1B"] if method == "simpler" else ["G1", "G2", "G3", "G10", "G11", "1A", "1B"]
    values = {**g, "1A": one_a, "1B": one_b}
    bas = {k: _whole(max(0.0, values[k])) for k in report_labels}
    net = one_a - one_b
    net_whole = bas["1A"] - bas["1B"]

    out = {
        "accounting_basis": inp.accounting_basis,
        "reporting_method": method,
        "worksheet": {k: _r(v) for k, v in sorted(g.items(), key=lambda kv: int(kv[0][1:]))},
        "gst_on_sales_1A": _r(one_a),
        "gst_on_purchases_1B": _r(one_b),
        "net_gst": _r(net),
        "net_gst_position": "payable" if net > 0 else ("refundable" if net < 0 else "nil"),
        "bas_labels_whole_dollars": bas,
        "net_gst_whole_dollars": net_whole,
        "deferred_credits_no_tax_invoice_gst": _r(deferred_credits * frac),
        "excluded": excluded,
        "assumptions": assumptions,
        "warnings": warnings,
        "risk_flags": sorted(set(risk_flags)),
    }
    if inp.payg_withholding:
        w = inp.payg_withholding
        w5 = w.w2 + w.w4 + w.w3
        out["payg_withholding_labels"] = {"W1": _whole(w.w1), "W2": _whole(w.w2), "W4": _whole(w.w4),
                                          "W3": _whole(w.w3), "W5": _whole(w5), "4": _whole(w5)}
        total = net_whole + _whole(w5)
        out["summary"] = {"1A": bas["1A"], "4 (W5)": _whole(w5), "1B": bas["1B"],
                          "amount_payable" if total >= 0 else "amount_refundable": abs(total)}
        assumptions.append("W5 = W2 + W4 + W3 and is copied to label 4; W1 is not part of W5. PAYG instalments (T labels) are not included; use the payg-instalments skill.")
    return out


# ---------------------------------------------------------------- margin scheme

class MarginSchemeInput(BaseModel):
    """Sale of real property under the margin scheme (GSTA Div 75)."""

    sale_price: float = Field(gt=0, description="Consideration for the sale (contract price).")
    margin_basis: Literal["consideration", "valuation"] = Field(
        "consideration", description="consideration = sale price less what the seller paid (s75-10(2)); valuation = "
        "sale price less an approved valuation (s75-10(3)).")
    acquisition_price: float | None = Field(None, ge=0, description="What the seller paid for the interest (consideration method).")
    approved_valuation: float | None = Field(None, ge=0, description="Approved valuation at the s75-10(3) valuation date (valuation method).")
    valuation_item_applies: bool = Field(True, description="Valuation method: an item in the s75-10(3) table applies (e.g. held since before 1 Jul 2000).")
    written_agreement: bool = Field(True, description="Seller and buyer agreed in writing, on or before the supply, that the margin scheme applies (s75-5(1), (1A)).")
    acquired_via_fully_taxable_supply: bool = Field(
        False, description="Seller bought the property through a taxable supply on which GST was worked out without the margin scheme (s75-5(3)): scheme not available.")
    special_acquisition: list[Literal["from_associate", "gst_free_going_concern", "gst_free_farmland",
                                      "gst_group_or_joint_venture", "subdivided_land", "inherited"]] = Field(
        default_factory=list, description="s75-11 special rules; any present escalates (AU-GST-001).")
    residential_withholding: bool = Field(
        False, description="Sale of new residential premises or potential residential land: purchaser must withhold at settlement (TAA Sch 1 s14-250).")

    @model_validator(mode="after")
    def _basis(self):
        if self.margin_basis == "consideration" and self.acquisition_price is None:
            raise ValueError("acquisition_price is required for the consideration method")
        if self.margin_basis == "valuation" and self.approved_valuation is None and self.valuation_item_applies:
            raise ValueError("approved_valuation is required for the valuation method")
        return self


@calculator("margin_scheme_gst", MarginSchemeInput)
def margin_scheme_gst(figures: Figures, inp: MarginSchemeInput) -> dict:
    """GST on a sale of real property under the margin scheme (GSTA Div 75): margin = sale price less the
    seller's acquisition price (consideration method) or an approved valuation (valuation method); GST = 1/11
    of the margin; BAS reporting per ATO instructions (G1 = the margin, nothing at G1 if the margin is nil or
    negative; 1A = GST on the margin), comparison with GST on the full price, and GST at settlement withholding
    by the purchaser for new residential premises (7% of the contract price under the margin scheme) with the
    resulting credit or balance for the seller. Use for "margin scheme GST", "GST on selling a new house",
    "what goes at G1 for a margin scheme sale". Refuses AU-GST-006 when the scheme is not available (no written
    agreement, acquired through a fully taxable supply) and AU-GST-001 for s75-11 special cases."""
    if inp.special_acquisition:
        raise Refusal("AU-GST-001", "margin scheme special rules (s75-11): " + ", ".join(inp.special_acquisition))
    if not inp.written_agreement:
        raise Refusal("AU-GST-006", "no written agreement to apply the margin scheme (s75-5(1), (1A))")
    if inp.acquired_via_fully_taxable_supply:
        raise Refusal("AU-GST-006", "acquired through a taxable supply worked out without the margin scheme (s75-5(3))")
    if inp.margin_basis == "consideration":
        base = inp.acquisition_price
    else:
        if not inp.valuation_item_applies:
            raise Refusal("AU-GST-006", "no item in the s75-10(3) table allows a valuation")
        base = inp.approved_valuation
    frac = figures.get("gst.margin_scheme_gst_fraction")
    std = _fraction(figures)
    margin = inp.sale_price - base
    gst = max(0.0, margin) * frac
    out = {
        "sale_price": _r(inp.sale_price),
        "margin_basis": inp.margin_basis,
        "cost_or_valuation": _r(base),
        "margin": _r(margin),
        "gst_on_margin": _r(gst),
        "gst_if_full_price": _r(inp.sale_price * std),
        "gst_saved_by_margin_scheme": _r(inp.sale_price * std - gst),
        "bas_labels_whole_dollars": {"G1": _whole(max(0.0, margin)), "1A": _whole(gst)},
        "assumptions": [
            "Sale price is the whole consideration; stamp duty and other acquisition costs are not part of the margin (the margin uses the purchase price only, s75-10(2)).",
            "The buyer cannot claim a GST credit on a margin scheme purchase (s75-20) and the seller cannot issue a tax invoice showing the GST.",
        ],
        "warnings": [],
    }
    if margin <= 0:
        out["warnings"].append("Margin is nil or negative: no GST and nothing reported at G1 for this sale.")
    if inp.residential_withholding:
        rate = figures.get("gst.settlement_withholding_margin_scheme_rate")
        wh = rate * inp.sale_price
        out["settlement_withholding"] = {
            "amount_withheld_by_purchaser": _r(wh),
            "basis": "margin scheme: percentage of the contract price (TAA Sch 1 s14-250(6)(a))",
            "seller_credit_less_gst": _r(wh - gst),
            "seller_credit_less_gst_bas_whole_dollars": _whole(wh) - _whole(gst),
            "seller_position": "refund" if wh > gst else ("balance payable" if wh < gst else "nil"),
        }
        out["assumptions"].append("GST at settlement: the purchaser pays the withheld amount to the ATO on settlement; the seller still reports the sale in the BAS for the settlement period and gets a credit for the amount withheld.")
    return out


# ---------------------------------------------------------------- registration

class RegistrationInput(BaseModel):
    """GST registration test for an enterprise (GSTA s23-5, s23-15, s144-5, Div 188)."""

    entity_type: Literal["business", "non_profit"] = "business"
    current_gst_turnover: float = Field(0, ge=0, description="GST-exclusive value of supplies for this month and the previous 11 months.")
    projected_gst_turnover: float | None = Field(None, ge=0, description="GST-exclusive value of supplies for this month and the next 11 months.")
    input_taxed_sales_included: float = Field(0, ge=0, description="Input taxed sales (residential rent, financial supplies) included in current_gst_turnover; excluded from GST turnover.")
    projected_input_taxed_sales_included: float | None = Field(None, ge=0, description="Input taxed sales included in projected_gst_turnover; defaults to input_taxed_sales_included.")
    projected_capital_asset_sales_included: float = Field(0, ge=0, description="Sales of capital assets included in projected turnover; excluded (s188-25).")
    projected_ceasing_business_sales_included: float = Field(0, ge=0, description="Sales made because the enterprise is ending or permanently shrinking, in projected turnover; excluded (s188-25).")
    supplies_taxi_or_ride_sourcing: bool = Field(False, description="Supplies taxi, limousine or ride-sourcing travel (s144-5): must register regardless of turnover.")
    wants_fuel_tax_credits: bool = Field(False, description="Wants to claim fuel tax credits (needs GST registration).")
    in_gst_group: bool = False
    amounts_include_gst: bool = Field(False, description="True if the turnover figures include GST charged; they are then reduced by the GST fraction (assumes all taxable).")
    currently_registered: bool = False


@calculator("gst_registration_check", RegistrationInput)
def gst_registration_check(figures: Figures, inp: RegistrationInput) -> dict:
    """Whether an enterprise must register for GST: GST turnover (current = this month plus previous 11;
    projected = this month plus next 11) against the registration threshold (non-profit threshold for NFPs),
    at or above the threshold meets it (s188-10); input taxed sales, capital asset sales and wind-down sales
    are excluded as the law requires; taxi and ride-sourcing drivers must register at any turnover (s144-5);
    registration deadline; and the reporting consequences (Simpler BAS below its turnover limit, monthly BAS
    at or above the monthly threshold, cash accounting limit). Use for "do I need to register for GST", "GST
    threshold", "I earn $X from Uber / Airbnb / consulting, do I charge GST". Refuses AU-GST-004 for GST groups."""
    if inp.in_gst_group:
        raise Refusal("AU-GST-004", "GST group turnover")
    key = "gst.registration_threshold_nfp" if inp.entity_type == "non_profit" else "gst.registration_threshold"
    threshold = figures.get(key)
    deadline = figures.get("gst.registration_deadline_days")
    assumptions: list[str] = []
    warnings: list[str] = []

    def clean(x: float) -> float:
        return x * (1 - _fraction(figures)) if inp.amounts_include_gst else x

    cur = max(0.0, clean(inp.current_gst_turnover) - inp.input_taxed_sales_included)
    proj = None
    if inp.projected_gst_turnover is not None:
        pit = inp.projected_input_taxed_sales_included
        pit = inp.input_taxed_sales_included if pit is None else pit
        proj = max(0.0, clean(inp.projected_gst_turnover) - pit
                   - inp.projected_capital_asset_sales_included - inp.projected_ceasing_business_sales_included)
    if inp.input_taxed_sales_included or inp.projected_input_taxed_sales_included:
        assumptions.append("Input taxed sales (for example residential rent, including short-stay letting of residential premises) are excluded from GST turnover (s188-15, s188-20).")
    if inp.amounts_include_gst:
        assumptions.append("Turnover figures included GST; reduced by 1/11 on the assumption that all of it was taxable.")

    reasons: list[str] = []
    status: str
    if inp.supplies_taxi_or_ride_sourcing:
        status = "must_register"
        reasons.append("Supplies taxi or ride-sourcing travel: registration required regardless of GST turnover (s144-5).")
    else:
        meets_current = cur >= threshold
        meets_projected = proj is not None and proj >= threshold
        if meets_projected:
            status = "must_register"
            reasons.append("Projected GST turnover is at or above the registration threshold (s188-10(1)(b)).")
        elif meets_current and proj is None:
            status = "must_register"
            reasons.append("Current GST turnover is at or above the registration threshold (s188-10(1)(a)); projected turnover not given.")
        elif meets_current:
            status = "must_register_unless_ato_satisfied_projected_below"
            reasons.append("Current GST turnover is at or above the threshold but projected turnover is below it: registration is required unless the Commissioner is satisfied projected turnover will be below the threshold (s188-10(1)(a)).")
        else:
            status = "not_required"
            reasons.append("Neither current nor projected GST turnover reaches the registration threshold; registration is optional (usually for at least 12 months once registered).")
        if inp.wants_fuel_tax_credits:
            reasons.append("Fuel tax credits need GST registration, so register if you want to claim them.")
        if proj is None:
            warnings.append("Projected GST turnover not given: test it too, since projected turnover alone can trigger registration (for example a new business).")
    out = {
        "entity_type": inp.entity_type,
        "registration_threshold": threshold,
        "current_gst_turnover": _r(cur),
        "projected_gst_turnover": _r(proj) if proj is not None else None,
        "status": status,
        "must_register": status.startswith("must_register"),
        "reasons": reasons,
        "registration_deadline_days": deadline,
        "assumptions": assumptions,
        "warnings": warnings,
    }
    if status.startswith("must_register") and not inp.currently_registered:
        out["next_steps"] = (f"Register within {deadline} days of reaching the threshold (after obtaining an ABN). "
                             "If registration was required earlier, GST is payable on sales from the date you were required to be registered, even if you did not charge it.")
    basis = max(cur, proj or 0.0)
    out["reporting"] = {
        "bas_frequency": "monthly (required)" if basis >= figures.get("gst.monthly_reporting_turnover_min") else "quarterly (or monthly by choice)",
        "simpler_bas_available": basis < figures.get("gst.simpler_bas_turnover_max"),
        "cash_accounting_available_if_aggregated_turnover_similar": basis < figures.get("gst.cash_accounting_turnover_max"),
    }
    return out


# ---------------------------------------------------------------- due dates

class DueDateInput(BaseModel):
    cycle: Literal["quarterly", "monthly"] = "quarterly"
    quarter: int | None = Field(None, ge=1, le=4, description="Quarter of the income year: 1 = Jul-Sep, 2 = Oct-Dec, 3 = Jan-Mar, 4 = Apr-Jun.")
    month: int | None = Field(None, ge=1, le=12, description="Calendar month for a monthly BAS (1 = January).")
    lodgment: Literal["paper", "online_self", "registered_agent"] = "online_self"
    gst_turnover: float | None = Field(None, ge=0, description="GST turnover; large business clients (GST turnover at or above the monthly threshold) get no online concession.")

    @model_validator(mode="after")
    def _need(self):
        if self.cycle == "quarterly" and self.quarter is None:
            raise ValueError("quarter is required for a quarterly BAS")
        if self.cycle == "monthly" and self.month is None:
            raise ValueError("month is required for a monthly BAS")
        return self


def _ymd(n: int) -> date:
    return date(n // 10000, (n // 100) % 100, n % 100)


@calculator("bas_due_date", DueDateInput)
def bas_due_date(figures: Figures, inp: DueDateInput) -> dict:
    """Due date to lodge and pay a BAS for a quarter or month of the income year: original due date (quarterly:
    28th of the month after the quarter, quarter 2 due 28 February; monthly: 21st of the next month), the
    two-week online lodge-and-pay concession (quarters 1, 3 and 4 only; not monthly or large business), the
    registered agent lodgment program date, the December monthly concession, and the roll to the first business day
    when the date is a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT (TAA 1953 s 8AAZMB). Use for
    "when is my BAS due", "Q1 BAS due date", "extra time if I lodge online / through an agent"."""
    start = figures.data["meta"]["start"]
    y0, y1 = start.year, start.year + 1
    notes: list[str] = []
    large = inp.gst_turnover is not None and inp.gst_turnover >= figures.get("gst.monthly_reporting_turnover_min")
    if inp.cycle == "quarterly":
        q = inp.quarter
        day = figures.get("gst.bas_quarterly_due_day")
        original = {1: date(y0, 10, day), 2: date(y1, 2, day), 3: date(y1, 4, day), 4: date(y1, 7, day)}[q]
        period = {1: f"Jul-Sep {y0}", 2: f"Oct-Dec {y0}", 3: f"Jan-Mar {y1}", 4: f"Apr-Jun {y1}"}[q]
        applicable = original
        if q == 2:
            notes.append("Quarter 2 is due 28 February and gets no online or agent extension (it already includes extra time).")
        elif inp.lodgment == "online_self":
            if large:
                notes.append("Large business clients (for example GST turnover at or above the monthly reporting threshold) are excluded from the online concession.")
            else:
                applicable = original + timedelta(days=figures.get("gst.bas_online_concession_days"))
                notes.append("Online lodgment: extra 2 weeks to lodge and pay (quarters 1, 3 and 4), applied automatically.")
        elif inp.lodgment == "registered_agent":
            agent = figures.get(f"gst.bas_agent_q{q}_due_yyyymmdd")
            applicable = _ymd(agent)
            notes.append("Registered agent lodgment program date: requires electronic lodgment by the agent and an eligible activity statement.")
        else:
            notes.append("Paper lodgment: no concession.")
    else:
        m = inp.month
        yr = y0 if m >= 7 else y1
        period = date(yr, m, 1).strftime("%B %Y")
        ny, nm = (yr + 1, 1) if m == 12 else (yr, m + 1)
        original = date(ny, nm, figures.get("gst.bas_monthly_due_day"))
        applicable = original
        notes.append("Monthly BAS: due the 21st of the following month; no online two-week concession.")
        if m == 12 and inp.lodgment != "paper" and not (inp.gst_turnover is not None and inp.gst_turnover > figures.get("gst.simpler_bas_turnover_max")):
            applicable = date(ny, 2, figures.get("gst.bas_monthly_december_concession_day_february"))
            notes.append("December monthly BAS: 21 February for businesses with turnover up to the limit that lodge electronically (not deferred GST scheme members).")
    roll = roll_due_date(applicable, COMMONWEALTH, figures)
    rolled = roll.due
    return {
        "cycle": inp.cycle,
        "period": period,
        "lodgment": inp.lodgment,
        "original_due_date": original.isoformat(),
        "due_date": rolled.isoformat(),
        "due_date_weekday": rolled.strftime("%A"),
        "applies_to": "lodge and pay",
        "business_day_roll": roll.as_dict(),
        "notes": notes,
        "assumptions": [],
        "warnings": roll.warnings,
    }
