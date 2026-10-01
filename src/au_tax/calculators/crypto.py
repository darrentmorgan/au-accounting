"""Crypto assets (Australia): transaction classification, income receipts and cost base, parcel identification and
per-disposal CGT, personal use screen and investor-versus-business screen.

The tools do what the `cgt` tools do not: decide the event and the AUD capital proceeds for each transaction, match
disposals to parcels (first-in first-out, or a documented specific selection, never average cost across days), turn
staking, airdrop and services receipts into income and cost base, and screen the personal use asset exemption and the
character question. The CGT arithmetic itself (cost base, 12-month rule, discount, the 1 July 2027 regime, loss
ordering) is NOT re-implemented: the ledger calls `capital_gain` once per matched parcel slice and `net_capital_gain`
once per income year in `au_tax.calculators.cgt`.

Law and ATO views (see skills/crypto/references/sources.md):
- Crypto is a CGT asset (ITAA 1997 s108-5; TD 2014/26). Disposal is CGT event A1 (s104-10), capital proceeds for a
  swap are the market value of what is received (s116-20(1)(b)), with the market value of what is given up as the
  fallback (s116-30(2)(a)); a gift is taken to be for market value (s116-30(1)). Lost or destroyed assets: C1 (s104-20).
- Personal use assets: gain disregarded if the first element of cost base is at or below the threshold in
  `individual.personal_use_asset_cgt_exempt_max_cost` (s118-10(3)); losses always disregarded (s108-20(1)).
- Parcel identification: TD 33 (first-in first-out or the taxpayer's own selection where records show it; average cost
  only for same-day identical units, TD 33A). No crypto-specific ATO position exists (applied by analogy).
- Staking and other consensus rewards are ordinary income at market value when received, and that value is the cost base
  (ITAA 1997 s6-5, ITAA 1936 s21; ATO web guidance). Airdrops and wrapping: DRAFT TR 2026/D1 and DRAFT TD 2026/D2 only.
  Chain splits: ATO web guidance only.
No price is looked up: AUD market values are always supplied by the caller and their source recorded.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.cgt import (
    REFORM_DATE,
    CapitalGainInput,
    GainItem,
    LossItem,
    NetCapitalGainInput,
    capital_gain,
    event_figures,
    figures_for_income_year,
    held_12_months,
    income_year_of,
    net_capital_gain,
)
from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator, refusal_catalogue

PUA_KEY = "individual.personal_use_asset_cgt_exempt_max_cost"
LABEL_D1 = ("Draft TR 2026/D1 (airdrops, issued 19 Aug 2026): the ATO's preliminary view only, not law; the ATO web "
            "page that mirrors it does not make it final.")
LABEL_D2 = ("Draft TD 2026/D2 (wrapping, issued 19 Aug 2026): the ATO's preliminary view only, not law; alternative "
            "views are acknowledged and gas or platform fees are not addressed.")


# ---------------------------------------------------------------- helpers

def _d(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(str(x))


def _m(x: Decimal) -> float:
    """Whole cents, half up."""
    return float(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _cents(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _qty(x: Decimal) -> float:
    return float(x.normalize()) if x != 0 else 0.0


def _esc(code: str, detail: str = "") -> dict:
    entry = refusal_catalogue().get(code, {})
    return {"code": code, "message": entry.get("message"), "route": entry.get("route"), "detail": detail}


def _regime(d: dt.date) -> str:
    return "from_1_july_2027" if d >= REFORM_DATE else "before_1_july_2027"


def _dedupe(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for i in items:
        seen.setdefault(i, None)
    return list(seen)


# ================================================================ crypto_classify_transactions

TxType = Literal[
    "buy_with_aud", "sell_for_aud", "swap", "spend_goods_services", "card_load", "gift_given", "donation",
    "network_fee_in_crypto", "own_wallet_transfer", "exchange_deposit", "lost_or_stolen",
    "staking_reward", "defi_reward", "payment_for_services", "airdrop_holder", "airdrop_for_services",
    "airdrop_in_trading_business", "airdrop_other", "chain_split_new_asset", "prize", "gift_received",
    "wrap", "unwrap", "defi_lending", "liquidity_pool", "bridge", "liquid_staking", "derivatives_or_margin",
    "mining", "nft_transaction", "exchange_in_administration",
]

A1_TYPES = {"sell_for_aud", "swap", "spend_goods_services", "card_load", "gift_given", "donation",
            "network_fee_in_crypto"}
INCOME_TYPES = {"staking_reward", "defi_reward", "payment_for_services", "airdrop_for_services"}
CGT005_TYPES = {"wrap", "unwrap", "defi_lending", "liquidity_pool", "bridge", "liquid_staking",
                "derivatives_or_margin", "airdrop_in_trading_business"}
OTHER_ESC = {"mining": "AU-CRYPTO-002", "nft_transaction": "AU-CRYPTO-006", "airdrop_other": "AU-CRYPTO-003",
             "exchange_in_administration": "AU-CRYPTO-004"}


class Transaction(BaseModel):
    """One crypto transaction. Give the Australian local date, or a UTC timestamp to convert."""

    id: str
    type: TxType = Field(description="What happened. sell_for_aud, swap (crypto for crypto), spend_goods_services, "
                         "card_load, gift_given, donation and network_fee_in_crypto are disposals (CGT event A1). "
                         "own_wallet_transfer is not an event. staking_reward, defi_reward, payment_for_services and "
                         "airdrop_for_services are income. wrap, unwrap, defi_lending, liquidity_pool, bridge, "
                         "liquid_staking, derivatives_or_margin, mining, nft_transaction, airdrop_other and "
                         "exchange_in_administration escalate.")
    date: dt.date | None = Field(None, description="Australian local date of the transaction.")
    utc_timestamp: dt.datetime | None = Field(None, description="UTC time from the exchange export, converted to the "
                                              "Australian local date in local_timezone. Give date OR this.")
    local_timezone: str = Field("Australia/Adelaide", description="IANA zone used to convert utc_timestamp.")
    value_received_aud: float | None = Field(None, ge=0, description="AUD received (sale), AUD market value of the "
                                             "asset or goods or services received (swap, spend), card balance increase "
                                             "(card_load), or compensation (lost_or_stolen).")
    market_value_given_up_aud: float | None = Field(None, ge=0, description="AUD market value of the crypto disposed "
                                                    "of at the time. Needed for gifts, donations and fees paid in "
                                                    "crypto; the fallback for a swap when the asset received cannot be "
                                                    "valued.")

    @model_validator(mode="after")
    def _one_date(self):
        if (self.date is None) == (self.utc_timestamp is None):
            raise ValueError("give exactly one of date or utc_timestamp")
        return self


class ClassifyInput(BaseModel):
    """Transactions to classify for tax. One row per transaction."""

    transactions: list[Transaction] = Field(min_length=1)


def _local_date(t: Transaction) -> dt.date:
    if t.utc_timestamp is None:
        return t.date  # type: ignore[return-value]
    try:
        tz = ZoneInfo(t.local_timezone)
    except (ZoneInfoNotFoundError, ValueError) as e:  # pragma: no cover - environment without tz data
        raise ValueError(f"unknown timezone {t.local_timezone}: {e}") from e
    ts = t.utc_timestamp if t.utc_timestamp.tzinfo else t.utc_timestamp.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(tz).date()


def _row(t: Transaction, local: dt.date) -> dict:
    return {"id": t.id, "type": t.type, "local_date": local.isoformat(), "event_income_year": income_year_of(local),
            "law_regime": _regime(local), "treatment": None, "cgt_event": None, "is_disposal": False,
            "is_income": False, "capital_proceeds_aud": None, "proceeds_basis": None, "draft_label": None,
            "escalation": None, "notes": []}


@calculator("crypto_classify_transactions", ClassifyInput)
def crypto_classify_transactions(figures: Figures, inp: ClassifyInput) -> dict:
    """Classify each crypto transaction for Australian tax: CGT event A1 disposal (sale, swap, spending, gifting, card
    load, network fee paid in crypto), CGT event C1 (lost or stolen), income at receipt (staking and DeFi rewards,
    payment for services, airdrop for services), not an event (own-wallet transfer, airdrop or chain split or prize or
    gift received), or an escalation (wrap and unwrap under DRAFT TD 2026/D2, DeFi lending, liquidity pools, bridging,
    liquid staking, derivatives, mining, NFTs, airdrops outside DRAFT TR 2026/D1, exchange in administration). For
    each disposal returns the AUD capital proceeds and the rule used: a swap uses the AUD market value of what is
    received, falling back to the market value given up. Converts a UTC timestamp to the Australian local date (default
    Adelaide) before fixing the income year and the 1 July 2027 regime. Use first, on any list of exchange rows or
    'do I pay tax on this' for a crypto transaction, before the ledger and income tools. It never looks up prices:
    AUD values are supplied by the caller."""
    rows: list[dict] = []
    assumptions = ["Dates are Australian local dates (ACST or ACDT); a UTC timestamp is converted before the income "
                   "year is fixed. No primary source fixes this convention: confirm it."] \
        if any(t.utc_timestamp for t in inp.transactions) else []
    assumptions.append("AUD values are supplied by the caller (reputable exchange price at the time of the transaction) "
                       "and their source and time must be recorded; no daily-average shortcut is approved.")
    warnings: list[str] = []
    escalations: dict[str, dict] = {}

    for t in inp.transactions:
        local = _local_date(t)
        r = _row(t, local)
        ty = t.type
        if ty in A1_TYPES:
            r.update(treatment="cgt_event_A1", cgt_event="A1", is_disposal=True)
            recv, given = t.value_received_aud, t.market_value_given_up_aud
            if ty == "sell_for_aud":
                p, basis = recv, "AUD received (s116-20(1)(b))"
            elif ty in ("swap", "spend_goods_services", "card_load"):
                if recv is not None:
                    p, basis = recv, ("market value of the asset or goods or services received (s116-20(1)(b))"
                                      if ty != "card_load" else "increase in the card balance (s116-20(1)(b))")
                elif given is not None:
                    p, basis = given, ("market value of the crypto given up, because what was received cannot be "
                                       "valued (s116-30(2)(a))")
                else:
                    p, basis = None, None
            elif ty in ("gift_given", "donation"):
                p, basis = given, "market value of the crypto given away, taken to be received (s116-30(1))"
            else:  # network_fee_in_crypto
                p, basis = (given if given is not None else recv), "market value of the crypto spent on the fee"
            if p is None:
                r["escalation"] = _esc("AU-CRYPTO-010", f"transaction {t.id}: no AUD market value supplied")
            else:
                r.update(capital_proceeds_aud=_m(_d(p)), proceeds_basis=basis)
            notes = r["notes"]
            if ty == "swap":
                notes.append("Swapping one crypto for another is a disposal of the crypto given up and an acquisition "
                             "of the crypto received, on the swap date; the 12-month clock restarts on the asset "
                             "received. No AUD has to be received.")
            if ty == "spend_goods_services":
                notes.append("Gift card bought with crypto: proceeds are the gift card's market value. A card "
                             "denominated in crypto is a separate disposal on each use.")
            if ty == "donation":
                notes.append("Narrow no-CGT cases exist for gifts to deductible gift recipients (gift under a will, "
                             "Cultural Gifts Program, personal use crypto); confirm before relying on them.")
            if ty == "network_fee_in_crypto":
                notes.append("A fee paid in crypto is a disposal of the crypto spent. How the fee counts in the cost "
                             "base of the related asset is not settled (draft TD 2026/D2 reserves gas fees); keep the "
                             "record and flag it.")
        elif ty == "lost_or_stolen":
            r.update(treatment="cgt_event_C1", cgt_event="C1", is_disposal=True,
                     capital_proceeds_aud=_m(_d(t.value_received_aud or 0)),
                     proceeds_basis="compensation received (nil if none); the loss uses the reduced cost base")
            r["notes"].append("Event time is when compensation is first received, or the loss is discovered if none. "
                              "A loss needs evidence of ownership and of loss of access; recoverable crypto is not "
                              "lost. With weak evidence use AU-CRYPTO-004.")
        elif ty == "own_wallet_transfer":
            r.update(treatment="not_a_cgt_event")
            r["notes"].append("Transfers between wallets you own are not disposals while you keep ownership. A network "
                              "fee paid in crypto for the transfer is a separate disposal.")
        elif ty == "exchange_deposit":
            r.update(treatment="unsettled_assumed_no_event")
            r["notes"].append("No ATO page says whether depositing with a centralised exchange is a disposal. Whether "
                              "ownership changes turns on beneficial ownership under the account terms (s104-10(2)); "
                              "this is inferred, not stated by the ATO. Check the terms.")
            warnings.append(f"{t.id}: deposit with an exchange is unsettled (beneficial ownership under the account terms).")
        elif ty == "buy_with_aud":
            r.update(treatment="acquisition")
            r["notes"].append("Acquisition: first element of cost base is the AUD paid; brokerage and fees paid in AUD "
                              "are incidental costs (second element).")
        elif ty in INCOME_TYPES:
            r.update(treatment="income_at_receipt", is_income=True)
            r["notes"].append("Ordinary income at the AUD market value when received (ITAA 1997 s6-5; ITAA 1936 s21); "
                              "that value is the cost base of the tokens. A later disposal is a separate CGT event. "
                              "Use crypto_income_receipts for the figures.")
            if ty == "airdrop_for_services":
                r["draft_label"] = LABEL_D1
        elif ty == "airdrop_holder":
            r.update(treatment="not_income_cost_base_market_value", draft_label=LABEL_D1)
            r["notes"].append("Non-business recipient, no services: not ordinary income; a separate CGT asset with a "
                              "cost base of market value at receipt (nil if nil or negligible). Preliminary view only.")
        elif ty == "chain_split_new_asset":
            r.update(treatment="not_income_nil_cost_base")
            r["notes"].append("ATO web guidance (no ruling): a new asset received on a chain split is neither income "
                              "nor a capital gain when received; cost base nil; acquired on the split date. Confirm "
                              "which side continues the original (crypto_income_receipts).")
        elif ty == "prize":
            r.update(treatment="not_income_cost_base_market_value")
            r["notes"].append("Lottery, raffle and game-show prizes are generally not ordinary income; cost base is "
                              "the market value when won.")
        elif ty == "gift_received":
            r.update(treatment="not_a_cgt_event")
            r["notes"].append("Receiving a gift is not a CGT event; keep the market value at receipt. A payment tied "
                              "to work or services is assessable, not a gift.")
        elif ty in CGT005_TYPES:
            r.update(treatment="escalate", escalation=_esc("AU-CGT-005", f"{ty}"))
            if ty in ("wrap", "unwrap"):
                r.update(cgt_event="C2", draft_label=LABEL_D2)
                r["notes"].append("Draft view: wrapping through a lock-and-mint contract is CGT event C2 on both the "
                                  "wrap and the unwrap, with the wrapped token and the coin as separate assets. Not "
                                  "computed here.")
            if ty == "airdrop_in_trading_business":
                r["draft_label"] = LABEL_D1
        elif ty in OTHER_ESC:
            r.update(treatment="escalate", escalation=_esc(OTHER_ESC[ty], f"{ty}"))
            if ty == "airdrop_other":
                r["draft_label"] = LABEL_D1
        if r["escalation"]:
            escalations.setdefault(r["escalation"]["code"], {**r["escalation"], "rows": []})["rows"].append(t.id)
            r["escalation"]["detail"] = r["escalation"]["detail"] or t.id
        rows.append(r)

    return {"rows": rows, "escalations": list(escalations.values()), "assumptions": assumptions, "warnings": warnings}


# ================================================================ crypto_income_receipts

ReceiptKind = Literal[
    "staking_reward", "defi_reward", "payment_for_services", "airdrop_for_services", "airdrop_holder",
    "airdrop_trading_business", "airdrop_other", "chain_split", "prize", "gift_received", "mining",
]
ORIGIN = {"staking_reward": "staking_reward", "defi_reward": "defi_reward",
          "payment_for_services": "payment_for_services", "airdrop_for_services": "airdrop",
          "airdrop_holder": "airdrop", "chain_split": "chain_split", "prize": "prize", "gift_received": "gift_received"}


class Receipt(BaseModel):
    """One receipt of crypto for no payment of crypto or AUD."""

    id: str
    asset: str = "CRYPTO"
    date: dt.date = Field(description="Australian local date received (when applied or dealt with as you direct).")
    quantity: float = Field(gt=0)
    kind: ReceiptKind = Field(description="staking_reward and defi_reward: income. payment_for_services and "
                              "airdrop_for_services: income. airdrop_holder: non-business holder, no services (draft "
                              "TR 2026/D1). airdrop_trading_business, airdrop_other and mining escalate. chain_split: "
                              "new asset from a chain split. prize; gift_received.")
    unit_value_aud: float | None = Field(None, ge=0, description="AUD market value per unit at receipt.")
    total_value_aud: float | None = Field(None, ge=0, description="AUD market value of the whole receipt, instead of "
                                          "unit_value_aud.")
    original_continues: bool | None = Field(None, description="chain_split only: True if the original asset carries "
                                            "on with the same rights (so this is the new asset); False if neither "
                                            "side does; None if unknown.")
    original_cost_base_aud: float | None = Field(None, ge=0, description="chain_split with original_continues False: "
                                                 "cost base of the original, for the ATO's example view only.")
    accessible_on_receipt: bool = Field(True, description="False if the reward is locked or cannot be withdrawn yet.")
    related_to_work: bool = Field(False, description="gift_received: the payment relates to work or services, so it is "
                                  "assessable, not a gift.")


class IncomeReceiptsInput(BaseModel):
    receipts: list[Receipt] = Field(min_length=1)


@calculator("crypto_income_receipts", IncomeReceiptsInput)
def crypto_income_receipts(figures: Figures, inp: IncomeReceiptsInput) -> dict:
    """Assessable income and cost base for crypto received without paying for it. Staking and DeFi rewards, payment
    for services (including crypto paid by a client or sponsor) and an airdrop for services are ordinary income at the
    AUD market value when received, and that value is the cost base (first element) of the tokens. A holder airdrop to a
    non-business investor is not income and has a market value cost base (nil if no market value) under DRAFT TR
    2026/D1 (preliminary view). A new asset from a chain split where the original continues is neither income nor a
    gain and has a nil cost base, acquired on the split date (ATO web guidance). Prizes and gifts received are not
    income (a payment for work is). Airdrops to a trading business or outside the draft, mining, and chain splits
    where the continuing side is unclear escalate with a refusal code. Returns income by income year and
    `acquisitions` rows that go straight into crypto_parcel_ledger. Values are supplied by the caller; nothing is
    looked up."""
    rows: list[dict] = []
    acquisitions: list[dict] = []
    by_year: dict[str, Decimal] = {}
    warnings: list[str] = []
    assumptions = ["AUD market values are supplied by the caller from a reputable exchange at the time of receipt; "
                   "record the source and time."]

    for r in inp.receipts:
        year = income_year_of(r.date)
        row: dict = {"id": r.id, "asset": r.asset, "date": r.date.isoformat(), "income_year": year, "kind": r.kind,
                     "treatment": None, "assessable_income_aud": 0.0, "cost_base_first_element_aud": None,
                     "draft_label": None, "escalation": None, "notes": []}
        value: Decimal | None = None
        if r.total_value_aud is not None:
            value = _cents(_d(r.total_value_aud))
        elif r.unit_value_aud is not None:
            value = _cents(_d(r.quantity) * _d(r.unit_value_aud))
        kind = r.kind
        income = Decimal(0)
        cost: Decimal | None = None
        origin: str | None = ORIGIN.get(kind)

        if kind in ("airdrop_trading_business", "airdrop_other", "mining"):
            code = {"airdrop_trading_business": "AU-CGT-005", "airdrop_other": "AU-CRYPTO-003",
                    "mining": "AU-CRYPTO-002"}[kind]
            row.update(treatment="escalate", escalation=_esc(code, r.id))
            if kind != "mining":
                row["draft_label"] = LABEL_D1
            if kind == "airdrop_trading_business":
                row["notes"].append("Draft view: market value is ordinary income for a crypto trading business and the "
                                    "tokens are trading stock. Not computed here.")
            origin = None
        elif kind == "chain_split":
            if r.original_continues is True:
                row.update(treatment="not_income_nil_cost_base")
                cost = Decimal(0)
                row["notes"].append("ATO web guidance: no income and no capital gain when received; cost base nil; "
                                    "acquired on the split date, so the 12-month clock starts then. No ruling exists.")
            else:
                row.update(treatment="escalate", escalation=_esc(
                    "AU-CRYPTO-011", "which side continues the original is unknown" if r.original_continues is None
                    else "neither side continues the original (CGT event C2 on the original)"))
                if r.original_continues is False and r.original_cost_base_aud is not None:
                    row["ato_web_example_view"] = {
                        "capital_loss_on_original_aud": _m(_d(r.original_cost_base_aud)),
                        "new_asset_cost_base_aud": 0.0,
                        "note": "The ATO's web example only (C2 on the original, both new assets nil cost base). The "
                                "statutory market value substitution for C2 is not addressed there; do not rely on "
                                "this figure without a registered tax agent."}
                origin = None
        elif value is None and kind == "airdrop_holder":
            row.update(treatment="not_income_cost_base_market_value", draft_label=LABEL_D1)
            cost = Decimal(0)
            assumptions.append(f"{r.id}: no market value at receipt, so the airdrop's cost base is nil (draft TR "
                               "2026/D1: nil or negligible market value means nil). Whether an initial allocation "
                               "airdrop is covered is unsettled.")
        elif value is None:
            row.update(treatment="escalate", escalation=_esc("AU-CRYPTO-010", f"{r.id}: no AUD market value at receipt"))
            origin = None
        elif kind in ("staking_reward", "defi_reward", "payment_for_services", "airdrop_for_services"):
            row.update(treatment="income_at_receipt")
            income, cost = value, value
            row["notes"].append("Ordinary income at market value when received; that value is the cost base. A later "
                                "disposal is a separate CGT event, discount-eligible only if held 12 months.")
            if kind == "airdrop_for_services":
                row["draft_label"] = LABEL_D1
            if kind in ("staking_reward", "defi_reward") and not r.accessible_on_receipt:
                warnings.append(f"{r.id}: reward locked or not yet accessible. Timing of receipt (s6-5(4)) is unsettled: "
                                "the only support for deferral is an edited private advice that cannot be relied on. "
                                "Income is shown at the date supplied; confirm with a registered tax agent.")
        elif kind == "airdrop_holder":
            row.update(treatment="not_income_cost_base_market_value", draft_label=LABEL_D1)
            cost = value
            row["notes"].append("Non-business holder, no services: not ordinary income; separate CGT asset; cost base "
                                "market value at receipt. Preliminary view only.")
        elif kind == "prize":
            row.update(treatment="not_income_cost_base_market_value")
            cost = value
            row["notes"].append("Prize or gambling win: generally not ordinary income; cost base is market value when won.")
        elif kind == "gift_received":
            if r.related_to_work:
                row.update(treatment="income_at_receipt")
                income, cost, origin = value, value, "payment_for_services"
                row["notes"].append("A payment tied to work or services is assessable at market value when received, "
                                    "not a gift; cost base is that market value.")
            else:
                row.update(treatment="not_income_cost_base_market_value")
                cost = value
                row["notes"].append("A gift is not income and receiving it is not a CGT event; keep the market value at "
                                    "receipt as the first element.")
        if row["escalation"] is None and cost is not None:
            row["assessable_income_aud"] = _m(income)
            row["cost_base_first_element_aud"] = _m(cost)
            by_year[year] = by_year.get(year, Decimal(0)) + income
            if origin:
                acquisitions.append({"id": r.id, "asset": r.asset, "date": r.date.isoformat(),
                                     "quantity": r.quantity, "first_element_aud": _m(cost),
                                     "incidental_costs_aud": 0, "origin": origin})
        rows.append(row)

    total = sum(by_year.values(), Decimal(0))
    return {"rows": rows, "total_assessable_income_aud": _m(total),
            "assessable_income_by_income_year": {y: _m(v) for y, v in sorted(by_year.items())},
            "acquisitions": acquisitions,
            "escalations": [r["escalation"] for r in rows if r["escalation"]],
            "assumptions": assumptions, "warnings": warnings}


# ================================================================ crypto_personal_use_screen

class PersonalUseScreenInput(BaseModel):
    """Facts about one disposal that the taxpayer says was of a personal use asset."""

    acquired_to_buy_personal_items: bool = Field(description="Acquired to buy items for personal use or consumption.")
    held_as_investment: bool = Field(description="At any time kept for profit or investment, or to facilitate business "
                                     "or purchases of income-producing investments.")
    used_within_short_time: bool | None = Field(None, description="Acquired and used to buy personal items within a "
                                                "short time. False or None if held for some time or only part was spent.")
    used_gateway_or_conversion: bool = Field(False, description="Converted to AUD or another crypto to buy personal "
                                             "items, bought a gift card, topped up a card, or paid through a payment "
                                             "gateway or bill payment intermediary.")
    part_of_larger_holding_or_split: bool = Field(False, description="The disposal is part of a larger holding, or "
                                                  "several disposals were made to keep each under the threshold.")
    is_nft_or_collectable: bool = False
    first_element_aud: float = Field(ge=0, description="First element of cost base (AUD paid or market value given) of "
                                     "the whole asset disposed of.")
    capital_proceeds_aud: float | None = Field(None, ge=0, description="Capital proceeds, to state the gain or loss.")


@calculator("crypto_personal_use_screen", PersonalUseScreenInput)
def crypto_personal_use_screen(figures: Figures, inp: PersonalUseScreenInput) -> dict:
    """Screen a claim that a crypto disposal is of a personal use asset (ITAA 1997 s108-20, s118-10(3); TD 2014/26;
    ATO personal use asset page). Crypto qualifies only if kept or used mainly to buy items for personal use or
    consumption, usually acquired and used within a short time; an investment holding later spent does not. Returns
    `personal_use_asset_indicated`, `not_personal_use` or `uncertain` (gateway or conversion, split or partial
    disposals, or held for some time: the ATO pages conflict or the law is unsettled, so nothing is asserted), with
    whether the gain is disregarded (first element at or below individual.personal_use_asset_cgt_exempt_max_cost,
    inclusive) and that losses are always disregarded. NFTs and collectables escalate. Use before setting
    treat_as_personal_use_asset in crypto_parcel_ledger. The facts are the taxpayer's: record them as an assumption."""
    if inp.is_nft_or_collectable:
        raise Refusal("AU-CRYPTO-006", "NFT or collectable: not a personal use asset screen for fungible crypto")
    threshold = figures.get(PUA_KEY)
    at_or_below = inp.first_element_aud <= threshold
    reasons: list[str] = []
    notes = ["Statute (s118-10(3)) says the first element must be 'or less' than the amount, so a first element exactly "
             "at the amount qualifies. Two ATO web pages say 'less than'; the statute governs."]
    if inp.held_as_investment:
        outcome = "not_personal_use"
        reasons.append("Held at some time as an investment or for profit; investment holdings later spent are not "
                       "personal use assets (TD 2014/26; ATO).")
    elif not inp.acquired_to_buy_personal_items:
        outcome = "not_personal_use"
        reasons.append("Not acquired mainly to buy items for personal use or consumption.")
    elif inp.used_gateway_or_conversion:
        outcome = "uncertain"
        reasons.append("Use through a conversion, gift card, card top-up or payment gateway: the ATO's own pages "
                       "conflict on whether the exemption is lost. Not asserted.")
    elif inp.part_of_larger_holding_or_split:
        outcome = "uncertain"
        reasons.append("Part of a larger holding or split disposals: the set rule (s108-25) may treat the disposals as "
                       "one asset, and its application to fungible crypto is unsettled. Not asserted.")
    elif inp.used_within_short_time:
        outcome = "personal_use_asset_indicated"
        reasons.append("Acquired to buy personal items and used within a short time (ATO: more likely a personal use asset).")
    else:
        outcome = "uncertain"
        reasons.append("Held for some time or only part spent: the ATO says a personal use asset is then less likely.")
    indicated = outcome == "personal_use_asset_indicated"
    gl = None
    if inp.capital_proceeds_aud is not None:
        gl = _m(_d(inp.capital_proceeds_aud) - _d(inp.first_element_aud))
    out: dict = {
        "outcome": outcome, "reasons": reasons, "first_element_at_or_below_threshold": at_or_below,
        "threshold_key": PUA_KEY, "threshold_aud": threshold,
        "capital_gain_disregarded": (at_or_below if indicated else None),
        "capital_loss_disregarded": (True if indicated else None),
        "gain_or_loss_aud": gl,
        "treat_as_personal_use_asset_in_ledger": indicated,
        "notes": notes,
        "assumptions": ["The facts (purpose, timing, how the crypto was used) are the taxpayer's statements and are the "
                        "basis of this screen; the test is applied at disposal on how the asset was actually kept and used."],
        "warnings": [],
    }
    if not indicated:
        out["warnings"].append("Treat as an ordinary CGT asset (investment) unless a registered tax agent confirms "
                               "personal use; flag CRYPTO-PUA-NARROW.")
    if indicated and not at_or_below:
        out["notes"].append("Over the threshold: the gain is not disregarded (no discount unless held 12 months), but a "
                            "loss is still disregarded.")
    return out


# ================================================================ crypto_character_screen

class CharacterScreenInput(BaseModel):
    """Indicators of business or commercial profit-making (ATO business page; TD 2014/26, TD 2014/27, TR 92/3, TR 97/11)."""

    runs_crypto_business: bool = Field(False, description="Carries on or intends a business of crypto trading, "
                                       "exchange, or NFT selling.")
    mines_crypto: bool = Field(False, description="Mines crypto or receives mining pool payouts.")
    holds_for_sale_or_exchange_in_business: bool = Field(False, description="Holds crypto for sale or exchange in the "
                                                         "ordinary course of any business, including crypto received "
                                                         "as payment and held for sale.")
    acquired_in_commercial_profit_making_scheme: bool = Field(False, description="Acquired in an isolated or repeated "
                                                              "commercial transaction or scheme for profit.")
    regular_repeated_trading_for_profit: bool = Field(False, description="Regular, repeated buying and selling with a "
                                                      "profit-making purpose (not occasional rebalancing).")
    high_volume_or_large_amounts_only: bool = Field(False, description="The only indicator is high volume, large "
                                                    "amounts or sophistication.")


@calculator("crypto_character_screen", CharacterScreenInput)
def crypto_character_screen(figures: Figures, inp: CharacterScreenInput) -> dict:
    """Screen whether crypto is held on capital account (an investor: CGT, discount available) or may be on revenue
    account (a business or commercial profit-making: trading stock and ordinary income, no CGT discount). This is a
    screen, not a determination: any indicator of a crypto business, mining, holding for sale in a business, a
    commercial profit-making scheme, or regular repeated trading for profit is refused with AU-CRYPTO-001 (or
    AU-CRYPTO-002 for mining). High volume, large amounts or sophistication alone are not indicators. Use before the
    ledger for any user who trades often, mines, is paid in crypto, or runs a crypto related business."""
    if inp.mines_crypto:
        raise Refusal("AU-CRYPTO-002", "mining or pool payouts")
    hits = [name for name in ("runs_crypto_business", "holds_for_sale_or_exchange_in_business",
                              "acquired_in_commercial_profit_making_scheme", "regular_repeated_trading_for_profit")
            if getattr(inp, name)]
    if hits:
        raise Refusal("AU-CRYPTO-001", "indicators: " + ", ".join(hits))
    warnings = []
    if inp.high_volume_or_large_amounts_only:
        warnings.append("High volume, large amounts or sophistication alone do not make a business; purpose, "
                        "commerciality, regularity and organisation decide.")
    return {"outcome": "capital_account_indicated",
            "assumptions": ["No business or commercial profit-making indicator was given, so the holder is treated as an "
                            "investor holding crypto on capital account. This is a screen from the facts supplied, not a "
                            "determination."],
            "warnings": warnings}


# ================================================================ crypto_parcel_ledger

Origin = Literal["purchase", "swap_received", "staking_reward", "defi_reward", "airdrop", "chain_split",
                 "payment_for_services", "gift_received", "prize", "other"]
DisposalKind = Literal["sale_for_aud", "swap", "spend_goods_services", "gift_given", "card_load",
                       "network_fee_in_crypto", "lost_or_stolen"]


class Acquisition(BaseModel):
    """One parcel of one crypto asset with its own acquisition date and cost base."""

    id: str
    asset: str = "CRYPTO"
    date: dt.date = Field(description="Australian local date acquired (contract date). For a swap, the swap date.")
    quantity: float = Field(gt=0)
    first_element_aud: float = Field(ge=0, description="AUD paid, or AUD market value given up (swap) or received "
                                     "(staking, airdrop, services). Nil only for a chain split or a nil-value airdrop.")
    incidental_costs_aud: float = Field(0, ge=0, description="AUD brokerage, exchange fees and other incidental "
                                        "acquisition costs (second element).")
    origin: Origin = "purchase"
    cost_base_evidenced: bool = Field(True, description="False if the cost base has no supporting record: refused, "
                                      "because records must be reconstructed and nil is not the default.")
    market_value_30_june_2027_per_unit: float | None = Field(None, ge=0, description="AUD market value per unit just "
                                                              "before 1 July 2027 (needed for later disposals of parcels held then).")

    @model_validator(mode="after")
    def _chain_split_nil(self):
        if self.origin == "chain_split" and self.first_element_aud != 0:
            raise ValueError("a chain split asset has a nil cost base (ATO chain splits page)")
        return self


class ParcelPick(BaseModel):
    parcel_id: str
    quantity: float = Field(gt=0)


class Disposal(BaseModel):
    """One disposal of one crypto asset."""

    id: str
    asset: str = "CRYPTO"
    date: dt.date = Field(description="Australian local date of the disposal (contract date). For lost_or_stolen, the "
                          "date compensation was first received, or the loss was discovered if none.")
    quantity: float = Field(gt=0)
    kind: DisposalKind = "sale_for_aud"
    value_received_aud: float | None = Field(None, ge=0, description="AUD received (sale); AUD market value of what was "
                                             "received (swap, spend); card balance increase (card_load); compensation "
                                             "(lost_or_stolen).")
    market_value_given_up_aud: float | None = Field(None, ge=0, description="AUD market value of the crypto disposed "
                                                    "of. Required for a gift or a fee paid in crypto; the fallback for a "
                                                    "swap or spend that cannot be valued.")
    incidental_costs_disposal_aud: float = Field(0, ge=0, description="AUD brokerage or fees to dispose of it; added to "
                                                 "the cost base, not netted off proceeds.")
    parcel_selection: list[ParcelPick] | None = Field(None, description="Named parcels and quantities, for "
                                                      "method=specific with records.")
    treat_as_personal_use_asset: bool = Field(False, description="Set only after crypto_personal_use_screen returned "
                                              "personal_use_asset_indicated.")
    evidence_adequate: bool | None = Field(None, description="lost_or_stolen only: evidence of ownership and of loss of "
                                           "access is adequate.")
    received_asset: str | None = Field(None, description="Swap only: the asset received, so the ledger adds it as a new "
                                       "parcel with a first element equal to the capital proceeds.")
    received_quantity: float | None = Field(None, gt=0)
    received_market_value_30_june_2027_per_unit: float | None = Field(
        None, ge=0, description="Swap only: AUD market value per unit of the asset received, just before 1 July 2027, if "
        "it will still be held then.")

    @model_validator(mode="after")
    def _swap_receipt(self):
        if (self.received_asset is None) != (self.received_quantity is None):
            raise ValueError("received_asset and received_quantity go together")
        if self.received_asset is None and self.received_market_value_30_june_2027_per_unit is not None:
            raise ValueError("received_market_value_30_june_2027_per_unit needs received_asset")
        if self.received_asset and self.kind != "swap":
            raise ValueError("received_asset only applies to a swap")
        return self


class LedgerInput(BaseModel):
    """Parcels and disposals for one holder. All amounts in AUD."""

    entity_type: Literal["individual", "trust", "company", "complying_super_fund", "smsf"] = "individual"
    residency: Literal["resident", "foreign", "temporary_resident"] = "resident"
    holder_character: Literal["investor", "business_or_trader", "unknown"] = Field(
        "unknown", description="From crypto_character_screen. business_or_trader is refused.")
    method: Literal["fifo", "specific", "average"] = Field(
        "fifo", description="Parcel identification. fifo (TD 33 first-in first-out); specific (named parcels, needs "
        "records_identify_parcels); average is accepted only when every parcel available was acquired on the same day.")
    records_identify_parcels: bool = Field(False, description="Contemporaneous records show which units were disposed of.")
    acquisitions: list[Acquisition] = Field(default_factory=list)
    disposals: list[Disposal] = Field(default_factory=list)
    prior_year_net_capital_losses: float = Field(0, ge=0, description="Unapplied net capital losses brought in to the "
                                                 "first income year with a disposal.")
    repurchased_after_loss_sale: bool = Field(False, description="A loss sale was followed by repurchase of the same or "
                                              "an equivalent asset: refused (Part IVA, TR 2008/1).")
    funded_by_borrowing: bool = Field(False, description="Crypto bought with borrowed money: refused.")
    compute_cgt: bool = Field(True, description="Call capital_gain per slice and net_capital_gain per income year. "
                              "False returns the matching and capital_gain_inputs only.")

    @model_validator(mode="after")
    def _checks(self):
        ids = [a.id for a in self.acquisitions]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate acquisition id")
        dids = [d.id for d in self.disposals]
        if len(dids) != len(set(dids)):
            raise ValueError("duplicate disposal id")
        if self.method != "specific" and any(d.parcel_selection for d in self.disposals):
            raise ValueError("parcel_selection needs method=specific")
        return self


@dataclass
class _Parcel:
    id: str
    asset: str
    date: dt.date
    qty_orig: Decimal
    qty_left: Decimal
    first: Decimal
    inc: Decimal
    origin: str
    mv_2027_unit: float | None
    order: int
    alloc_first: Decimal = field(default_factory=lambda: Decimal(0))
    alloc_inc: Decimal = field(default_factory=lambda: Decimal(0))


def _proceeds(d: Disposal) -> tuple[Decimal, str]:
    recv, given = d.value_received_aud, d.market_value_given_up_aud
    if d.kind == "sale_for_aud":
        if recv is None:
            raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: AUD received not supplied")
        return _cents(_d(recv)), "AUD received (s116-20(1)(b))"
    if d.kind in ("swap", "spend_goods_services", "card_load"):
        if recv is not None:
            return _cents(_d(recv)), ("market value of the asset or goods or services received (s116-20(1)(b))"
                                      if d.kind != "card_load" else "increase in the card balance (s116-20(1)(b))")
        if given is not None:
            return _cents(_d(given)), ("market value of the crypto given up, because what was received cannot be "
                                       "valued (s116-30(2)(a))")
        raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: no AUD market value supplied for a {d.kind}")
    if d.kind == "gift_given":
        if given is None:
            raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: market value of the gift not supplied (s116-30(1))")
        return _cents(_d(given)), "market value of the crypto given away, taken to be received (s116-30(1))"
    if d.kind == "network_fee_in_crypto":
        v = given if given is not None else recv
        if v is None:
            raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: market value of the crypto spent on the fee not supplied")
        return _cents(_d(v)), "market value of the crypto spent on the fee"
    # lost_or_stolen: compensation, nil if none
    return _cents(_d(recv or 0)), "compensation received (nil if none)"


def _select(d: Disposal, candidates: list[_Parcel], parcels: dict[str, _Parcel], inp: LedgerInput,
            qty: Decimal) -> list[tuple[_Parcel, Decimal]]:
    total_left = sum((p.qty_left for p in candidates), Decimal(0))
    if total_left < qty:
        raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: {_qty(qty)} {d.asset} disposed of but only {_qty(total_left)} "
                      f"held on record at {d.date.isoformat()}. Reconstruct the missing acquisitions.")
    if inp.method == "specific":
        if not d.parcel_selection:
            raise Refusal("AU-CRYPTO-009", f"disposal {d.id}: specific identification needs named parcels")
        picks: list[tuple[_Parcel, Decimal]] = []
        for pick in d.parcel_selection:
            p = parcels.get(pick.parcel_id)
            if p is None or p not in candidates:
                raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: parcel {pick.parcel_id} not held on {d.date.isoformat()}")
            q = _d(pick.quantity)
            if q > p.qty_left:
                raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: parcel {p.id} has {_qty(p.qty_left)} left, "
                              f"{_qty(q)} selected")
            picks.append((p, q))
        if sum((q for _, q in picks), Decimal(0)) != qty:
            raise Refusal("AU-CRYPTO-010", f"disposal {d.id}: selected quantities do not equal the disposal quantity")
        return picks
    if inp.method == "average":
        if len({p.date for p in candidates}) > 1:
            raise Refusal("AU-CRYPTO-009", f"disposal {d.id}: parcels held were acquired on different days")
        picks = []
        left = qty
        for i, p in enumerate(candidates):
            q = left if i == len(candidates) - 1 else (qty * p.qty_left / total_left).quantize(Decimal("1e-18"))
            q = min(q, p.qty_left)
            if q > 0:
                picks.append((p, q))
            left -= q
        return picks
    picks = []  # fifo
    left = qty
    for p in candidates:
        if left <= 0:
            break
        q = min(left, p.qty_left)
        picks.append((p, q))
        left -= q
    return picks


def _take(p: _Parcel, q: Decimal) -> tuple[Decimal, Decimal]:
    """First element and incidental costs attributable to q units of parcel p; the last units carry the remainder."""
    if q == p.qty_left:
        first, inc = p.first - p.alloc_first, p.inc - p.alloc_inc
    else:
        first, inc = _cents(p.first * q / p.qty_orig), _cents(p.inc * q / p.qty_orig)
    p.alloc_first += first
    p.alloc_inc += inc
    p.qty_left -= q
    return first, inc


def _split(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    """Split an amount by weights to whole cents; the last part takes the remainder."""
    whole = sum(weights, Decimal(0))
    parts: list[Decimal] = []
    used = Decimal(0)
    for i, w in enumerate(weights):
        v = (total - used) if i == len(weights) - 1 else _cents(total * w / whole)
        parts.append(v)
        used += v
    return parts


def _trim(res: dict) -> dict:
    keys = ("method", "reason", "cost_base", "reduced_cost_base", "gross_capital_gain", "capital_loss",
            "discount_percentage", "discount_amount", "net_capital_gain", "components", "market_value_30_june_2027",
            "minimum_tax_capital_gain", "partial", "deferred_component", "post_1_july_2027_part", "field_refusals")
    return {k: res[k] for k in keys if k in res}


@calculator("crypto_parcel_ledger", LedgerInput)
def crypto_parcel_ledger(figures: Figures, inp: LedgerInput) -> dict:
    """Match crypto disposals to acquisition parcels and work out the capital gain or loss and the net capital gain
    for each income year (resident individual, capital account). Each disposal gets its AUD capital proceeds (a swap
    uses the AUD market value received, falling back to the market value given up; a gift uses market value; a
    lost_or_stolen event uses compensation) and is matched to parcels by first-in first-out, a documented specific
    selection (method specific with records_identify_parcels), or average cost only where every parcel was acquired the
    same day. Average cost across different days and a specific selection with no records are refused (AU-CRYPTO-009);
    a disposal larger than the holdings, a cost base with no evidence or a missing AUD value is refused (AU-CRYPTO-010).
    A swap with received_asset adds the asset received as a new parcel acquired on the swap date with a first element
    equal to the capital proceeds. Each matched slice goes through the `capital_gain` tool (cost base, 12-month rule,
    discount, the 1 July 2027 regime and its market value input) and each income year through `net_capital_gain` (loss
    ordering, carried-forward losses); nothing is re-implemented. Personal use asset treatment applies only when
    treat_as_personal_use_asset is set, after crypto_personal_use_screen. Business or trader, foreign or temporary
    resident, non-individual holders, borrowing and wash-sale flags are refused. Use for any list of crypto disposals
    or 'how much CGT on my crypto'; feed it the acquisitions rows from crypto_income_receipts for rewards and airdrops.
    Held across 1 July 2027: when the index numbers for the post-1 July 2027 part are unpublished, the disposal still
    returns its deferred component (deemed sale notional gain, discount, discounted amount: `deferred_gain_aud`,
    `deferred_gain_discount_aud`, `deferred_gain_after_discount_aud`, and `deferred_components`) and a field-level
    refusal (`field_refusals`, AU-GEN-003) for the post-July part; that disposal's gross gain and the year's
    `net_capital_gain` are withheld (`incomplete`), with the known-components figure labelled as such."""
    if inp.entity_type != "individual":
        raise Refusal("AU-CGT-003", f"holder is a {inp.entity_type}: different discount, streaming and 1 July 2027 rules")
    if inp.residency != "resident":
        raise Refusal("AU-CRYPTO-005", f"residency: {inp.residency}")
    if inp.holder_character == "business_or_trader":
        raise Refusal("AU-CRYPTO-001", "holder_character business_or_trader")
    if inp.repurchased_after_loss_sale:
        raise Refusal("AU-CRYPTO-008", "loss sale followed by repurchase")
    if inp.funded_by_borrowing:
        raise Refusal("AU-CRYPTO-007", "crypto bought with borrowed money")
    if inp.method == "specific" and not inp.records_identify_parcels:
        raise Refusal("AU-CRYPTO-009", "specific identification without records that show which units were disposed of")
    for a in inp.acquisitions:
        if not a.cost_base_evidenced:
            raise Refusal("AU-CRYPTO-010", f"parcel {a.id}: cost base has no supporting record; reconstruct it "
                          "from exchange and blockchain data (nil is not the default)")

    assumptions: list[str] = []
    warnings: list[str] = []
    if inp.holder_character == "unknown":
        assumptions.append("Holder treated as an investor holding crypto on capital account (resident individual). Run "
                           "crypto_character_screen: a business, or a commercial profit-making transaction, would put "
                           "the crypto on revenue account.")
    assumptions.append("Dates are Australian local dates. AUD values were supplied by the caller from a reputable "
                       "exchange at the time of each transaction; the source and time must be on file.")
    method_text = {"fifo": "Parcels identified first-in first-out (TD 33; no crypto-specific ATO position exists).",
                   "specific": "Parcels identified from the named selections; contemporaneous records show which units "
                               "were disposed of (TD 33, by analogy).",
                   "average": "Average cost applied only because every parcel available was acquired on the same day "
                              "(TD 33A)."}[inp.method]
    assumptions.append(method_text)

    parcels: dict[str, _Parcel] = {}
    order = 0
    for a in inp.acquisitions:
        parcels[a.id] = _Parcel(a.id, a.asset, a.date, _d(a.quantity), _d(a.quantity), _cents(_d(a.first_element_aud)),
                                _cents(_d(a.incidental_costs_aud)), a.origin, a.market_value_30_june_2027_per_unit,
                                order)
        order += 1

    sequence = sorted(enumerate(inp.disposals), key=lambda t: (t[1].date, t[0]))
    disposals_out: list[dict] = []
    cgt_rows: list[dict] = []
    gains_by_year: dict[str, list[GainItem]] = {}
    losses_by_year: dict[str, list[LossItem]] = {}
    years_seen: list[str] = []
    partial_years: dict[str, list[dict]] = {}   # income year -> field refusals of disposals whose post-July part is refused
    deferred_components: list[dict] = []
    field_refusals: list[dict] = []
    swap_fee_seen = False
    threshold: float | None = None

    for _, d in sequence:
        qty = _d(d.quantity)
        year = income_year_of(d.date)
        if year not in years_seen:
            years_seen.append(year)
        if d.kind == "lost_or_stolen" and d.evidence_adequate is not True:
            raise Refusal("AU-CRYPTO-004", f"disposal {d.id}: evidence of ownership and loss of access not adequate")
        proceeds, basis = _proceeds(d)
        candidates = sorted((p for p in parcels.values() if p.asset == d.asset and p.date <= d.date and p.qty_left > 0),
                            key=lambda p: (p.date, p.order))
        picks = _select(d, candidates, parcels, inp, qty)
        qs = [q for _, q in picks]
        proceeds_parts = _split(proceeds, qs)
        cost_parts = _split(_cents(_d(d.incidental_costs_disposal_aud)), qs)
        takes = []
        for (p, q) in picks:
            partial_parcel = q < p.qty_orig
            first, inc = _take(p, q)
            takes.append((p, q, first, inc, partial_parcel))

        pua = d.treat_as_personal_use_asset and d.kind != "lost_or_stolen"
        pua_within = False
        if pua:
            threshold = event_figures(figures, d.date, warnings).get(PUA_KEY)  # the disposal's own income year
            total_first = sum((t[2] for t in takes), Decimal(0))
            pua_within = float(total_first) <= threshold
            assumptions.append(f"Disposal {d.id} treated as a personal use asset on the taxpayer's assertion (from "
                               "crypto_personal_use_screen): the first element of the whole disposal is tested against "
                               "the threshold, not each slice.")
            if any(t[4] for t in takes):
                warnings.append(f"Disposal {d.id}: part of a larger holding; the set rule (s108-25) may treat split "
                                "disposals of a personal use asset as one asset. Unsettled for fungible crypto.")
        if d.kind == "swap" and d.incidental_costs_disposal_aud:
            swap_fee_seen = True
        if d.kind == "network_fee_in_crypto":
            warnings.append(f"Disposal {d.id}: a fee paid in crypto is a disposal; how it counts in the cost base of "
                            "the related asset is unsettled (flag CRYPTO-FEES-IN-CRYPTO).")

        slices: list[dict] = []
        d_gain = d_loss = Decimal(0)
        d_deferred = d_deferred_discount = d_deferred_net = Decimal(0)
        d_field_refusals: list[dict] = []
        for (p, q, first, inc, _partial), pr, dc in zip(takes, proceeds_parts, cost_parts):
            row = {"acquisition_date": p.date.isoformat(), "event_date": d.date.isoformat(),
                   "capital_proceeds": _m(pr), "first_element": _m(first), "incidental_costs_acquisition": _m(inc),
                   "incidental_costs_disposal": _m(dc), "asset_type": "crypto",
                   "cgt_event": "C1" if d.kind == "lost_or_stolen" else "A1"}
            if pua and pua_within:
                row["asset_type"] = "personal_use_asset"
            mv = p.mv_2027_unit
            sl = {"parcel_id": p.id, "quantity": _qty(q), "acquisition_date": p.date.isoformat(),
                  "acquisition_origin": p.origin, "first_element_aud": _m(first), "incidental_costs_aud": _m(inc),
                  "proceeds_aud": _m(pr), "disposal_costs_aud": _m(dc), "cost_base_aud": _m(first + inc + dc),
                  "held_over_12_months": held_12_months(p.date, d.date)}
            cgt_rows.append({"disposal": d.id, "parcel": p.id, **row})
            if inp.compute_cgt:
                kw: dict[str, Any] = dict(
                    entity_type="individual", cgt_event=row["cgt_event"], asset_type=row["asset_type"],
                    acquisition_date=p.date, event_date=d.date, capital_proceeds=row["capital_proceeds"],
                    first_element=row["first_element"], incidental_costs_acquisition=row["incidental_costs_acquisition"],
                    incidental_costs_disposal=row["incidental_costs_disposal"],
                    market_value_30_june_2027=(float(_cents(_d(mv) * q)) if mv is not None else None),
                    personal_use_crypto_claim=bool(pua))
                res = capital_gain(figures, CapitalGainInput(**kw))
                warnings.extend(res.get("warnings", []))
                assumptions.extend(res.get("assumptions", []))
                sl["cgt"] = _trim(res)
                if res.get("partial"):
                    # Only the post-1 July 2027 part is refused (its index numbers are unpublished): keep the deferred
                    # component as a figure and carry the field-level refusal up to the disposal and the ledger.
                    dc = res["deferred_component"]
                    d_deferred += _d(dc["notional_gain"])
                    d_deferred_discount += _d(dc["discount_amount"])
                    d_deferred_net += _d(dc["gain_after_discount"])
                    deferred_components.append({
                        "disposal": d.id, "parcel": p.id, "notional_gain": dc["notional_gain"],
                        "notional_loss": dc["notional_loss"], "discount_percentage": dc["discount_percentage"],
                        "discount_amount": dc["discount_amount"], "gain_after_discount": dc["gain_after_discount"]})
                    for fr in res["field_refusals"]:
                        d_field_refusals.append({**fr, "parcel": p.id})
                    partial_years.setdefault(year, []).extend(d_field_refusals)
                else:
                    d_gain += _d(res.get("gross_capital_gain") or 0)
                    d_loss += _d(res.get("capital_loss") or 0)
                for comp in res.get("components", []):
                    g, loss = comp.get("gain") or 0, comp.get("capital_loss") or 0
                    label = f"{d.id}:{p.id}"
                    if g > 0:
                        elig = bool(comp.get("discount_eligible"))
                        gains_by_year.setdefault(year, []).append(GainItem(
                            amount=g, discount_eligible=elig,
                            discount_percentage=comp.get("discount_percentage") if elig else None,
                            category=comp["category"], collectable=bool(comp.get("collectable")), label=label))
                    if loss > 0:
                        losses_by_year.setdefault(year, []).append(LossItem(
                            amount=loss, personal_use_asset=bool(pua and not pua_within), label=label))
                if pua and not pua_within and (res.get("capital_loss") or 0) > 0:
                    assumptions.append(f"Disposal {d.id}: loss on a personal use asset disregarded (s108-20(1)).")
                losses_by_year.setdefault(year, [])
                gains_by_year.setdefault(year, [])
            slices.append(sl)
        disposals_out.append({
            "id": d.id, "kind": d.kind, "asset": d.asset, "date": d.date.isoformat(), "event_income_year": year,
            "law_regime": _regime(d.date), "cgt_event": "C1" if d.kind == "lost_or_stolen" else "A1",
            "quantity": _qty(qty), "capital_proceeds_aud": _m(proceeds), "proceeds_basis": basis,
            "disposal_costs_aud": _m(_d(d.incidental_costs_disposal_aud)), "slices": slices,
            **(({"gross_capital_gain": None, "capital_loss": None, "gain_less_loss_aud": None,
                 "deferred_gain_aud": _m(d_deferred), "deferred_gain_discount_aud": _m(d_deferred_discount),
                 "deferred_gain_after_discount_aud": _m(d_deferred_net), "field_refusals": d_field_refusals}
                if d_field_refusals else
                {"gross_capital_gain": _m(d_gain), "capital_loss": _m(d_loss), "gain_less_loss_aud": _m(d_gain - d_loss)})
               if inp.compute_cgt else {}),
        })
        field_refusals.extend({"disposal": d.id, **fr} for fr in d_field_refusals)
        if d.received_asset:
            new_id = f"{d.id}-received"
            parcels[new_id] = _Parcel(new_id, d.received_asset, d.date, _d(d.received_quantity), _d(d.received_quantity),
                                      proceeds, Decimal(0), "swap_received",
                                      d.received_market_value_30_june_2027_per_unit, order)
            order += 1

    if swap_fee_seen:
        assumptions.append("A swap fee paid in AUD is kept in the cost base of the crypto disposed of (as in the ATO's "
                           "own example) and is not added again to the asset received; the ATO is silent on adding it to "
                           "both (unsettled).")

    by_year_out: dict[str, dict] = {}
    if inp.compute_cgt:
        prior = inp.prior_year_net_capital_losses
        for y in sorted(years_seen):
            year_figures = figures_for_income_year(figures, y, warnings)  # discount rates are the income year's own
            res = net_capital_gain(year_figures, NetCapitalGainInput(
                entity_type="individual", gains=gains_by_year.get(y, []), losses=losses_by_year.get(y, []),
                prior_year_net_capital_losses=prior))
            assumptions.extend(res.pop("assumptions", []))
            warnings.extend(res.pop("warnings", []))
            prior = res["net_capital_loss_carried_forward"]
            if y in partial_years:
                # A disposal in this year has a refused post-July part, so the year cannot be netted in full: the figure
                # over the components that are known is labelled as such and the net capital gain is withheld.
                res = {**res, "net_capital_gain": None, "net_capital_gain_known_components_only": res["net_capital_gain"],
                       "incomplete": True, "field_refusals": partial_years[y]}
                warnings.append(f"Net capital gain for {y} is incomplete: it excludes the post-1 July 2027 part of the "
                                "disposal(s) with a field refusal, so it is withheld. Any capital loss carried forward "
                                "from this year is provisional for the same reason.")
            by_year_out[y] = res

    remaining = [{"id": p.id, "asset": p.asset, "quantity": _qty(p.qty_left), "date": p.date.isoformat(),
                  "origin": p.origin, "first_element_aud": _m(p.first - p.alloc_first),
                  "incidental_costs_aud": _m(p.inc - p.alloc_inc)}
                 for p in sorted(parcels.values(), key=lambda p: (p.date, p.order)) if p.qty_left > 0]
    if any(y >= "2027-28" for y in years_seen):
        warnings.append("Events from 1 July 2027 use the date-effective rules in the capital_gain tool, with the figures "
                        "of each event's own income year (2027-28 file for 2027-28 events). Indexation from 1 July 2027 "
                        "needs the published CPI index numbers in the rates file; until they are loaded the post-1 July 2027 part of "
                        "a disposal that would be indexed is refused AU-GEN-003 at field level, while the deferred "
                        "component (deemed sale gain and its discount) is still given.")
    return {
        "method": inp.method, "disposals": disposals_out, "parcels_remaining": remaining,
        "capital_gain_inputs": cgt_rows, "net_capital_gain_by_income_year": by_year_out,
        "deferred_components": deferred_components, "field_refusals": field_refusals,
        "assumptions": _dedupe(assumptions), "warnings": _dedupe(warnings),
    }
