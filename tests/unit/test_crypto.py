"""Crypto calculators. Expected values are hand computations shown step by step in each test, from the ATO
worked examples and rules in docs/research/crypto.md (W-01 to W-09, R-* rules). None were produced by running
the calculators. The CGT arithmetic itself (discount, 12-month rule, loss ordering) is owned by tests/unit/test_cgt.py;
here the tests check that the crypto tools hand the right facts to it."""

import pytest

from au_tax.registry import load_all, run

YEAR = "2026-27"


def ok(tool, year=YEAR, **kw):
    code, out = run(tool, year, kw)
    assert code == 0, out
    return out


def refused(tool, code, year=YEAR, **kw):
    rc, out = run(tool, year, kw)
    assert rc == 3, out
    assert out["refusal"]["code"] == code, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def acq(id, date, qty, first, inc=0, asset="X", origin="purchase", **kw):
    return {"id": id, "asset": asset, "date": date, "quantity": qty, "first_element_aud": first,
            "incidental_costs_aud": inc, "origin": origin, **kw}


def disp(id, date, qty, kind="sale_for_aud", asset="X", **kw):
    return {"id": id, "asset": asset, "date": date, "quantity": qty, "kind": kind, **kw}


def test_tools_registered():
    assert {"crypto_classify_transactions", "crypto_income_receipts", "crypto_parcel_ledger",
            "crypto_personal_use_screen", "crypto_character_screen"} <= set(load_all())


# ================================================================ classification

def tx(id, type, date="2026-11-18", **kw):
    return {"id": id, "type": type, "date": date, **kw}


def test_swap_proceeds_are_market_value_received():
    # W-01 step 2: swap 0.5 BTC for 12.0 ETH shown worth 84,000 -> capital proceeds 84,000 (s116-20(1)(b)).
    out = ok("crypto_classify_transactions",
             transactions=[tx("t1", "swap", value_received_aud=84000, market_value_given_up_aud=83500)])
    row = out["rows"][0]
    assert row["cgt_event"] == "A1" and row["is_disposal"] is True
    assert row["capital_proceeds_aud"] == 84000
    assert "received" in row["proceeds_basis"]
    assert row["event_income_year"] == "2026-27"


def test_swap_falls_back_to_value_given_up_when_received_not_valued():
    # R-08: token not yet listed -> market value of what is given up (s116-30(2)(a)).
    out = ok("crypto_classify_transactions",
             transactions=[tx("t1", "swap", market_value_given_up_aud=9000)])
    row = out["rows"][0]
    assert row["capital_proceeds_aud"] == 9000
    assert "given up" in row["proceeds_basis"]


def test_swap_with_no_value_at_all_escalates_row():
    # R-13: an AUD market value is needed for every transaction; none supplied -> AU-CRYPTO-010 on that row only.
    out = ok("crypto_classify_transactions", transactions=[tx("t1", "swap"), tx("t2", "sell_for_aud", value_received_aud=100)])
    assert out["rows"][0]["escalation"]["code"] == "AU-CRYPTO-010"
    assert out["rows"][0]["capital_proceeds_aud"] is None
    assert out["rows"][1]["capital_proceeds_aud"] == 100


def test_own_wallet_transfer_is_not_an_event_but_fee_in_crypto_is():
    # R-11: moving crypto between wallets you own is not a disposal; a network fee paid in crypto is a disposal
    # of the crypto spent, with proceeds the value of the crypto given up (here 12).
    out = ok("crypto_classify_transactions", transactions=[
        tx("t1", "own_wallet_transfer"), tx("t2", "network_fee_in_crypto", market_value_given_up_aud=12)])
    a, b = out["rows"]
    assert a["treatment"] == "not_a_cgt_event" and a["is_disposal"] is False
    assert b["cgt_event"] == "A1" and b["capital_proceeds_aud"] == 12
    assert any("fee" in w.lower() for w in b["notes"])


def test_spend_gift_and_card_load_proceeds():
    # R-09/R-10: spend -> market value of goods received (430); gift -> market value of the crypto (500,
    # s116-30(1)); card load -> increase in card balance (250).
    out = ok("crypto_classify_transactions", transactions=[
        tx("s", "spend_goods_services", value_received_aud=430),
        tx("g", "gift_given", market_value_given_up_aud=500),
        tx("c", "card_load", value_received_aud=250)])
    assert [r["capital_proceeds_aud"] for r in out["rows"]] == [430, 500, 250]
    assert all(r["cgt_event"] == "A1" for r in out["rows"])


def test_wrap_and_unwrap_escalate_and_label_draft_td_2026_d2():
    # R-52/R-53: wrap is CGT event C2 on the draft view (TD 2026/D2); existing code AU-CGT-005 covers it.
    out = ok("crypto_classify_transactions", transactions=[tx("w", "wrap"), tx("u", "unwrap")])
    for r in out["rows"]:
        assert r["escalation"]["code"] == "AU-CGT-005"
        assert r["draft_label"] and "TD 2026/D2" in r["draft_label"]
    assert out["escalations"] and {e["code"] for e in out["escalations"]} == {"AU-CGT-005"}


def test_escalating_types_map_to_codes():
    out = ok("crypto_classify_transactions", transactions=[
        tx("a", "mining"), tx("b", "nft_transaction"), tx("c", "airdrop_other"), tx("d", "defi_lending"),
        tx("e", "liquidity_pool"), tx("f", "bridge"), tx("g", "derivatives_or_margin")])
    assert [r["escalation"]["code"] for r in out["rows"]] == [
        "AU-CRYPTO-002", "AU-CRYPTO-006", "AU-CRYPTO-003", "AU-CGT-005", "AU-CGT-005", "AU-CGT-005", "AU-CGT-005"]


def test_receipts_are_flagged_as_income_or_not_a_cgt_event():
    out = ok("crypto_classify_transactions", transactions=[
        tx("s", "staking_reward"), tx("p", "payment_for_services"), tx("h", "airdrop_holder"),
        tx("x", "chain_split_new_asset"), tx("r", "gift_received")])
    by = {r["id"]: r for r in out["rows"]}
    assert by["s"]["is_income"] is True and by["p"]["is_income"] is True
    assert by["h"]["is_income"] is False and by["x"]["is_income"] is False and by["r"]["is_income"] is False
    assert all(r["is_disposal"] is False for r in out["rows"])
    assert "TR 2026/D1" in by["h"]["draft_label"]
    assert by["x"]["draft_label"] is None  # ATO web guidance, not a draft


def test_utc_timestamp_converted_to_australian_local_date_for_the_year_boundary():
    # W-10: 14:45 UTC on 30 Jun 2027 is 00:15 ACST (UTC+9:30) on 1 Jul 2027 -> 2027-28 and the new regime.
    out = ok("crypto_classify_transactions", transactions=[
        {"id": "t", "type": "swap", "utc_timestamp": "2027-06-30T14:45:00Z", "value_received_aud": 1000}])
    row = out["rows"][0]
    assert row["local_date"] == "2027-07-01"
    assert row["event_income_year"] == "2027-28"
    assert row["law_regime"] == "from_1_july_2027"
    assert any("local" in a.lower() for a in out["assumptions"])


def test_utc_timestamp_a_day_earlier_stays_in_2026_27():
    # 13:45 UTC 30 Jun 2027 = 23:15 ACST 30 Jun 2027 -> still 2026-27.
    out = ok("crypto_classify_transactions", transactions=[
        {"id": "t", "type": "swap", "utc_timestamp": "2027-06-30T13:45:00Z", "value_received_aud": 1000}])
    assert out["rows"][0]["local_date"] == "2027-06-30"
    assert out["rows"][0]["event_income_year"] == "2026-27"


def test_classification_needs_a_date():
    rc, out = run("crypto_classify_transactions", YEAR, {"transactions": [{"id": "t", "type": "swap"}]})
    assert rc == 2


def test_lost_or_stolen_classified_as_c1_with_nil_default_proceeds():
    out = ok("crypto_classify_transactions", transactions=[tx("l", "lost_or_stolen")])
    row = out["rows"][0]
    assert row["cgt_event"] == "C1" and row["capital_proceeds_aud"] == 0


# ================================================================ income receipts

def rec(id, kind, qty, unit=None, date="2026-09-14", asset="S", **kw):
    return {"id": id, "asset": asset, "date": date, "quantity": qty, "kind": kind, "unit_value_aud": unit, **kw}


def test_staking_rewards_income_and_cost_base_w02():
    # W-02 steps 1-2: reward 1 = 2.0 x 240 = 480; reward 2 = 1.5 x 270 = 405; total other income 885.
    # Each reward's cost base (first element) is its market value at receipt.
    out = ok("crypto_income_receipts", receipts=[
        rec("r1", "staking_reward", 2.0, 240, date="2026-09-14"),
        rec("r2", "staking_reward", 1.5, 270, date="2026-12-09")])
    r1, r2 = out["rows"]
    assert r1["assessable_income_aud"] == 480 and r1["cost_base_first_element_aud"] == 480
    assert r2["assessable_income_aud"] == 405 and r2["cost_base_first_element_aud"] == 405
    assert out["total_assessable_income_aud"] == 885
    assert out["assessable_income_by_income_year"] == {"2026-27": 885}
    assert out["acquisitions"][0]["origin"] == "staking_reward"
    assert out["acquisitions"][0]["first_element_aud"] == 480
    assert out["acquisitions"][0]["date"] == "2026-09-14"


def test_income_split_across_income_years():
    # 30 Jun 2026 falls in 2025-26 (received 100 x 2 = 200); 1 Jul 2026 in 2026-27 (100 x 3 = 300).
    out = ok("crypto_income_receipts", receipts=[
        rec("r1", "staking_reward", 100, 2, date="2026-06-30"),
        rec("r2", "staking_reward", 100, 3, date="2026-07-01")])
    assert out["assessable_income_by_income_year"] == {"2025-26": 200, "2026-27": 300}


def test_airdrop_holder_established_token_not_income_cost_base_market_value_w05a():
    # W-05(a): 5,000 tokens x 0.40 = 2,000 first element; no ordinary income (draft TR 2026/D1 paras 16, 20).
    out = ok("crypto_income_receipts", receipts=[rec("a", "airdrop_holder", 5000, 0.40, date="2026-02-10")])
    row = out["rows"][0]
    assert row["assessable_income_aud"] == 0
    assert row["cost_base_first_element_aud"] == 2000
    assert row["draft_label"] and "TR 2026/D1" in row["draft_label"]
    assert out["acquisitions"][0]["first_element_aud"] == 2000


def test_airdrop_with_no_market_value_has_nil_cost_base_w05b():
    out = ok("crypto_income_receipts", receipts=[rec("a", "airdrop_holder", 1000, None)])
    assert out["rows"][0]["cost_base_first_element_aud"] == 0
    assert out["rows"][0]["assessable_income_aud"] == 0


def test_airdrop_for_services_is_income_w05c():
    # W-05(c): 60,000 tokens x 0.002 = 120.00 ordinary income; cost base 120.
    out = ok("crypto_income_receipts", receipts=[rec("a", "airdrop_for_services", 60000, 0.002)])
    row = out["rows"][0]
    assert row["assessable_income_aud"] == 120 and row["cost_base_first_element_aud"] == 120


def test_airdrop_to_trading_business_escalates_w05d():
    out = ok("crypto_income_receipts", receipts=[rec("a", "airdrop_trading_business", 100, 2)])
    row = out["rows"][0]
    assert row["escalation"]["code"] == "AU-CGT-005"
    assert out["acquisitions"] == [] and out["total_assessable_income_aud"] == 0


def test_airdrop_other_and_mining_escalate():
    out = ok("crypto_income_receipts", receipts=[rec("a", "airdrop_other", 10, 1), rec("m", "mining", 1, 1)])
    assert [r["escalation"]["code"] for r in out["rows"]] == ["AU-CRYPTO-003", "AU-CRYPTO-002"]
    assert out["acquisitions"] == []


def test_payment_for_services_w09():
    # W-09 step 1: 0.05 BTC x 150,000 = 7,500 ordinary income; cost base 7,500.
    out = ok("crypto_income_receipts", receipts=[
        rec("p", "payment_for_services", 0.05, 150000, date="2026-11-04", asset="BTC")])
    row = out["rows"][0]
    assert row["assessable_income_aud"] == 7500 and row["cost_base_first_element_aud"] == 7500


def test_total_value_can_replace_unit_value():
    out = ok("crypto_income_receipts", receipts=[
        {"id": "p", "asset": "BTC", "date": "2026-11-04", "quantity": 0.05, "kind": "payment_for_services",
         "total_value_aud": 7500}])
    assert out["rows"][0]["assessable_income_aud"] == 7500


def test_income_receipt_without_a_value_escalates_row_with_records_code():
    out = ok("crypto_income_receipts", receipts=[rec("r", "staking_reward", 2.0, None)])
    assert out["rows"][0]["escalation"]["code"] == "AU-CRYPTO-010"
    assert out["total_assessable_income_aud"] == 0


def test_chain_split_original_continues_nil_cost_base_split_date_w04():
    # W-04 step 1: no income, no capital gain at receipt; first element nil; acquired on the split date.
    out = ok("crypto_income_receipts", receipts=[
        {"id": "q", "asset": "Q", "date": "2025-08-12", "quantity": 4, "kind": "chain_split",
         "original_continues": True}])
    row = out["rows"][0]
    assert row["assessable_income_aud"] == 0 and row["cost_base_first_element_aud"] == 0
    a = out["acquisitions"][0]
    assert a["date"] == "2025-08-12" and a["origin"] == "chain_split" and a["first_element_aud"] == 0


def test_chain_split_unclear_or_no_continuation_escalates():
    out = ok("crypto_income_receipts", receipts=[
        {"id": "q1", "asset": "Q", "date": "2025-08-12", "quantity": 4, "kind": "chain_split"},
        {"id": "q2", "asset": "Q", "date": "2025-08-12", "quantity": 4, "kind": "chain_split",
         "original_continues": False, "original_cost_base_aud": 8300}])
    assert [r["escalation"]["code"] for r in out["rows"]] == ["AU-CRYPTO-011", "AU-CRYPTO-011"]
    # ATO web example, informational only: original cost base 8,300 -> capital loss 8,300, new assets nil.
    view = out["rows"][1]["ato_web_example_view"]
    assert view["capital_loss_on_original_aud"] == 8300 and view["new_asset_cost_base_aud"] == 0
    assert out["acquisitions"] == []


def test_prize_and_gift_received():
    # R-40: prize not ordinary income, cost base market value (300). R-10/T-25: a gift with no link to work is not
    # income (cost base 200); a payment tied to work is assessable at market value (200).
    out = ok("crypto_income_receipts", receipts=[
        rec("p", "prize", 3, 100), rec("g", "gift_received", 2, 100),
        rec("w", "gift_received", 2, 100, related_to_work=True)])
    p, g, w = out["rows"]
    assert (p["assessable_income_aud"], p["cost_base_first_element_aud"]) == (0, 300)
    assert (g["assessable_income_aud"], g["cost_base_first_element_aud"]) == (0, 200)
    assert (w["assessable_income_aud"], w["cost_base_first_element_aud"]) == (200, 200)


def test_locked_staking_reward_carries_a_timing_warning():
    out = ok("crypto_income_receipts", receipts=[rec("r", "staking_reward", 2.0, 240, accessible_on_receipt=False)])
    assert any("locked" in w.lower() or "accessible" in w.lower() for w in out["warnings"])


# ================================================================ personal use screen

def pua(**kw):
    base = {"acquired_to_buy_personal_items": True, "used_within_short_time": True,
            "held_as_investment": False, "used_gateway_or_conversion": False,
            "part_of_larger_holding_or_split": False, "is_nft_or_collectable": False}
    base.update(kw)
    return ok("crypto_personal_use_screen", **base)


def test_pua_case_a_under_threshold():
    # W-03 A: 400 bought 3 Oct 2026, all spent 6 Oct 2026 -> personal use; first element 400 is <= threshold, so the
    # 30 gain (430 - 400) is disregarded.
    out = pua(first_element_aud=400, capital_proceeds_aud=430)
    assert out["outcome"] == "personal_use_asset_indicated"
    assert out["first_element_at_or_below_threshold"] is True
    assert out["capital_gain_disregarded"] is True
    assert out["gain_or_loss_aud"] == 30
    assert out["treat_as_personal_use_asset_in_ledger"] is True
    assert out["figures_used"][0]["key"] == "individual.personal_use_asset_cgt_exempt_max_cost"


def test_pua_case_b_exactly_at_threshold_is_inclusive():
    # W-03 B / T-06: s118-10(3) says "$10,000 or less", so a first element of exactly 10,000 qualifies; gain 600.
    out = pua(first_element_aud=10000, capital_proceeds_aud=10600)
    assert out["first_element_at_or_below_threshold"] is True
    assert out["capital_gain_disregarded"] is True
    assert any("less than" in n for n in out["notes"])


def test_pua_case_c_over_threshold_gain_not_disregarded():
    # W-03 C: 12,000 first element exceeds the threshold, so the 900 gain (12,900 - 12,000) is not disregarded.
    out = pua(first_element_aud=12000, capital_proceeds_aud=12900)
    assert out["outcome"] == "personal_use_asset_indicated"
    assert out["first_element_at_or_below_threshold"] is False
    assert out["capital_gain_disregarded"] is False
    assert out["gain_or_loss_aud"] == 900


def test_pua_case_d_loss_always_disregarded():
    # W-03 D: 9,000 first element, proceeds 8,500 -> loss 500, always disregarded (s108-20(1)).
    out = pua(first_element_aud=9000, capital_proceeds_aud=8500)
    assert out["gain_or_loss_aud"] == -500
    assert out["capital_loss_disregarded"] is True


def test_pua_case_e_investment_holding_is_not_personal_use():
    # W-03 E / T-05: bought as an investment, later spent on a laptop -> not a personal use asset.
    out = pua(held_as_investment=True, acquired_to_buy_personal_items=False, first_element_aud=5000,
              capital_proceeds_aud=8000)
    assert out["outcome"] == "not_personal_use"
    assert out["treat_as_personal_use_asset_in_ledger"] is False
    assert out["gain_or_loss_aud"] == 3000


def test_pua_held_for_some_time_is_uncertain():
    out = pua(used_within_short_time=False, first_element_aud=400)
    assert out["outcome"] == "uncertain"
    assert out["treat_as_personal_use_asset_in_ledger"] is False


def test_pua_gateway_or_split_is_uncertain_not_asserted():
    # R-26/R-27: ATO pages conflict on gateways; s108-25 sets unsettled -> never asserted.
    a = pua(used_gateway_or_conversion=True, first_element_aud=400)
    b = pua(part_of_larger_holding_or_split=True, first_element_aud=400)
    assert a["outcome"] == "uncertain" and b["outcome"] == "uncertain"
    assert a["treat_as_personal_use_asset_in_ledger"] is False


def test_pua_nft_routes_out():
    refused("crypto_personal_use_screen", "AU-CRYPTO-006", acquired_to_buy_personal_items=True,
            used_within_short_time=True, held_as_investment=False, used_gateway_or_conversion=False,
            part_of_larger_holding_or_split=False, is_nft_or_collectable=True, first_element_aud=100)


# ================================================================ character screen

def test_character_screen_passes_for_a_plain_holder():
    out = ok("crypto_character_screen", high_volume_or_large_amounts_only=True)
    assert out["outcome"] == "capital_account_indicated"
    assert any("volume" in w.lower() for w in out["warnings"])


@pytest.mark.parametrize("field", ["runs_crypto_business", "holds_for_sale_or_exchange_in_business",
                                   "acquired_in_commercial_profit_making_scheme",
                                   "regular_repeated_trading_for_profit"])
def test_character_screen_escalates_on_business_indicators(field):
    refused("crypto_character_screen", "AU-CRYPTO-001", **{field: True})


def test_character_screen_mining_routes_to_mining_code():
    refused("crypto_character_screen", "AU-CRYPTO-002", mines_crypto=True)


# ================================================================ parcel ledger

def ledger(acquisitions, disposals, **kw):
    return ok("crypto_parcel_ledger", acquisitions=acquisitions, disposals=disposals, **kw)


def test_w01_swap_btc_for_eth_discount_and_new_parcel():
    # W-01: cost base = 60,000 + 150 (acquisition fee) + 120 (swap fee) = 60,270. Proceeds 84,000.
    # Gain 84,000 - 60,270 = 23,730. Held 3 Mar 2025 to 18 Nov 2026 (> 12 months) -> 50% = 11,865 net.
    out = ledger([acq("btc1", "2025-03-03", 0.5, 60000, 150, asset="BTC")],
                 [disp("sw1", "2026-11-18", 0.5, "swap", asset="BTC", value_received_aud=84000,
                       incidental_costs_disposal_aud=120, received_asset="ETH", received_quantity=12.0)])
    d = out["disposals"][0]
    assert d["capital_proceeds_aud"] == 84000
    s = d["slices"][0]
    assert s["cost_base_aud"] == approx(60270)
    assert s["held_over_12_months"] is True
    assert s["cgt"]["gross_capital_gain"] == approx(23730)
    assert s["cgt"]["net_capital_gain"] == approx(11865)
    yr = out["net_capital_gain_by_income_year"]["2026-27"]
    assert yr["net_capital_gain"] == approx(11865)
    # ETH parcel: first element 84,000 (market value of BTC given up), acquired on the swap date; the 120 swap fee
    # is not added again (Q-03), and the BTC parcel is used up.
    remaining = {p["id"]: p for p in out["parcels_remaining"]}
    assert set(remaining) == {"sw1-received"}
    eth = remaining["sw1-received"]
    assert eth["asset"] == "ETH" and eth["quantity"] == 12.0
    assert eth["first_element_aud"] == 84000 and eth["date"] == "2026-11-18"
    assert out["figures_used"] and any(f["key"] == "cgt.discount_individual_trust" for f in out["figures_used"])


def test_w02_staking_rewards_sold_net_capital_gain_55():
    # W-02: reward 1 (2.0 units, cost base 480) sold 3 Feb 2027 at 310/unit = 620 with a 10 fee:
    #   cost base 480 + 10 = 490; gain 130; held < 12 months so no discount.
    # reward 2 (1.5 units, cost base 405) sold 5 Mar 2027 at 220/unit = 330: capital loss 75.
    # Net: 130 - 75 = 55.
    out = ledger(
        [acq("r1", "2026-09-14", 2.0, 480, asset="S", origin="staking_reward"),
         acq("r2", "2026-12-09", 1.5, 405, asset="S", origin="staking_reward")],
        [disp("d1", "2027-02-03", 2.0, asset="S", value_received_aud=620, incidental_costs_disposal_aud=10),
         disp("d2", "2027-03-05", 1.5, asset="S", value_received_aud=330)])
    d1, d2 = out["disposals"]
    assert d1["slices"][0]["parcel_id"] == "r1" and d2["slices"][0]["parcel_id"] == "r2"
    assert d1["gross_capital_gain"] == approx(130)
    assert d2["capital_loss"] == approx(75)
    yr = out["net_capital_gain_by_income_year"]["2026-27"]
    assert yr["net_capital_gain"] == approx(55)
    assert yr["discount_amount"] == 0


def test_w04_chain_split_asset_sale_discount_900():
    # W-04: Q received 12 Aug 2025 with nil cost base; sell 2 of 4 units 20 Oct 2026 at 900 each = 1,800.
    # Gain 1,800 - 0 = 1,800; held > 12 months -> discount 900; net 900.
    out = ledger([acq("q", "2025-08-12", 4, 0, asset="Q", origin="chain_split")],
                 [disp("d", "2026-10-20", 2, asset="Q", value_received_aud=1800)])
    assert out["disposals"][0]["gross_capital_gain"] == approx(1800)
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(900)
    assert out["parcels_remaining"][0]["quantity"] == 2


def test_chain_split_with_a_cost_base_is_rejected():
    rc, out = run("crypto_parcel_ledger", YEAR, {"acquisitions": [
        acq("q", "2025-08-12", 4, 100, asset="Q", origin="chain_split")], "disposals": []})
    assert rc == 2


def test_w05a_airdrop_sale_net_750():
    # W-05(a): cost base 5,000 x 0.40 = 2,000; sold 20 Feb 2027 for 3,500; gain 1,500; held from 10 Feb 2026 (> 12
    # months); discount 750; net 750.
    out = ledger([acq("a", "2026-02-10", 5000, 2000, asset="T", origin="airdrop")],
                 [disp("d", "2027-02-20", 5000, asset="T", value_received_aud=3500)])
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(750)


def test_w09_services_payment_then_swap_gain_400():
    # W-09: cost base 7,500 (income already taxed); swap proceeds 7,900; gain 400; under 12 months, no discount.
    out = ledger([acq("p", "2026-11-04", 0.05, 7500, asset="BTC", origin="payment_for_services")],
                 [disp("d", "2026-12-20", 0.05, "swap", asset="BTC", value_received_aud=7900)])
    assert out["disposals"][0]["gross_capital_gain"] == approx(400)
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(400)


def test_fifo_takes_the_oldest_parcel_across_two_parcels():
    # Parcel A: 3 units, first element 300, acquired 1 Jan 2025. Parcel B: 5 units, first element 1,000,
    # acquired 1 Dec 2025. Sell 6 units on 1 Oct 2026 for 1,800 with a 30 selling cost. FIFO: 3 from A, 3 from B.
    # Proceeds by quantity: 900 each. Selling cost 15 each.
    # A: cost base 300 + 15 = 315; gain 585; held > 12 months -> 50% -> 292.50.
    # B: first element 1,000 x 3/5 = 600; + 15 = 615; gain 285; acquired 1 Dec 2025, < 12 months -> no discount.
    # Net = 292.50 + 285 = 577.50. Remaining: 2 units of B with first element 400.
    out = ledger([acq("A", "2025-01-01", 3, 300), acq("B", "2025-12-01", 5, 1000)],
                 [disp("d", "2026-10-01", 6, value_received_aud=1800, incidental_costs_disposal_aud=30)])
    a, b = out["disposals"][0]["slices"]
    assert (a["parcel_id"], a["quantity"], b["parcel_id"], b["quantity"]) == ("A", 3, "B", 3)
    assert a["proceeds_aud"] == approx(900) and b["proceeds_aud"] == approx(900)
    assert a["cost_base_aud"] == approx(315) and b["cost_base_aud"] == approx(615)
    assert a["held_over_12_months"] is True and b["held_over_12_months"] is False
    assert a["cgt"]["net_capital_gain"] == approx(292.5)
    assert b["cgt"]["net_capital_gain"] == approx(285)
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(577.5)
    rem = out["parcels_remaining"]
    assert len(rem) == 1 and rem[0]["id"] == "B" and rem[0]["quantity"] == 2
    assert rem[0]["first_element_aud"] == approx(400)
    assert out["method"] == "fifo"


def test_partial_parcel_prorates_costs_including_incidentals():
    # 10 units, first element 1,000 + incidental 50, acquired 1 Jan 2025. Sell 4 units 1 Aug 2026 for 800, cost 20.
    # First element 1,000 x 4/10 = 400; incidental 50 x 4/10 = 20; + selling cost 20 -> cost base 440.
    # Gain 800 - 440 = 360; > 12 months -> discount 180 -> net 180. Remaining 6 units: 600 + 30.
    out = ledger([acq("A", "2025-01-01", 10, 1000, 50)],
                 [disp("d", "2026-08-01", 4, value_received_aud=800, incidental_costs_disposal_aud=20)])
    s = out["disposals"][0]["slices"][0]
    assert s["cost_base_aud"] == approx(440)
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(180)
    rem = out["parcels_remaining"][0]
    assert rem["quantity"] == 6 and rem["first_element_aud"] == approx(600) and rem["incidental_costs_aud"] == approx(30)


def test_specific_identification_with_records_uses_named_parcels():
    # Parcel A: 1 unit, 100, acquired 10 Jan 2025. Parcel B: 1 unit, 300, acquired 10 Jun 2025. Sell 1 unit on
    # 1 Mar 2026 for 600.
    # FIFO -> A: gain 500, > 12 months (10 Jan 2025 + 12 months = 10 Jan 2026) -> discount 250 -> net 250.
    # Specific -> B: gain 300, only 8 months -> no discount -> net 300.
    acqs = [acq("A", "2025-01-10", 1, 100), acq("B", "2025-06-10", 1, 300)]
    fifo = ledger(acqs, [disp("d", "2026-03-01", 1, value_received_aud=600)])
    assert fifo["net_capital_gain_by_income_year"]["2025-26"]["net_capital_gain"] == approx(250)
    spec = ledger(acqs, [disp("d", "2026-03-01", 1, value_received_aud=600,
                              parcel_selection=[{"parcel_id": "B", "quantity": 1}])],
                  method="specific", records_identify_parcels=True)
    assert spec["disposals"][0]["slices"][0]["parcel_id"] == "B"
    assert spec["net_capital_gain_by_income_year"]["2025-26"]["net_capital_gain"] == approx(300)
    assert spec["method"] == "specific"


def test_specific_identification_without_records_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-009",
            acquisitions=[acq("A", "2025-01-10", 1, 100), acq("B", "2025-06-10", 1, 300)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=600,
                            parcel_selection=[{"parcel_id": "B", "quantity": 1}])],
            method="specific", records_identify_parcels=False)


def test_specific_selection_must_match_quantity():
    rc, out = run("crypto_parcel_ledger", YEAR, {
        "acquisitions": [acq("A", "2025-01-10", 2, 100)],
        "disposals": [disp("d", "2026-03-01", 2, value_received_aud=600,
                           parcel_selection=[{"parcel_id": "A", "quantity": 1}])],
        "method": "specific", "records_identify_parcels": True})
    assert rc == 3 and out["refusal"]["code"] == "AU-CRYPTO-010"


def test_average_cost_across_different_days_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-009",
            acquisitions=[acq("A", "2025-01-10", 1, 100), acq("B", "2025-06-10", 1, 300)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=600)], method="average")


def test_average_cost_allowed_for_same_day_identical_units():
    # TD 33A: same asset, same day. Parcels: 2 units for 200 and 2 units for 600, both 5 Jan 2026 (average 200/unit).
    # Sell 2 units 1 Mar 2026 for 500: cost base 2 x 200 = 400; gain 100; < 12 months, no discount.
    out = ledger([acq("A", "2026-01-05", 2, 200), acq("B", "2026-01-05", 2, 600)],
                 [disp("d", "2026-03-01", 2, value_received_aud=500)], method="average")
    # Slices: 1 unit from each parcel, proceeds 250 each: A gain 250 - 100 = 150; B loss 250 - 300 = 50; net 100.
    assert out["disposals"][0]["gain_less_loss_aud"] == approx(100)
    assert out["net_capital_gain_by_income_year"]["2025-26"]["net_capital_gain"] == approx(100)
    assert sum(s["cost_base_aud"] for s in out["disposals"][0]["slices"]) == approx(400)


def test_disposal_larger_than_holdings_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-010",
            acquisitions=[acq("A", "2025-01-10", 1, 100)],
            disposals=[disp("d", "2026-03-01", 2, value_received_aud=600)])


def test_a_parcel_acquired_after_the_disposal_cannot_be_matched():
    refused("crypto_parcel_ledger", "AU-CRYPTO-010",
            acquisitions=[acq("A", "2026-04-01", 1, 100)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=600)])


def test_cost_base_without_evidence_is_refused_not_nil():
    refused("crypto_parcel_ledger", "AU-CRYPTO-010",
            acquisitions=[acq("A", "2025-01-10", 1, 0, cost_base_evidenced=False)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=600)])


def test_swap_without_any_aud_value_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-010",
            acquisitions=[acq("A", "2025-01-10", 1, 100)], disposals=[disp("d", "2026-03-01", 1, "swap")])


def test_swap_falls_back_to_value_given_up():
    # No AUD value for the token received -> use the market value given up (1,000): gain 1,000 - 400 = 600.
    out = ledger([acq("A", "2026-01-10", 1, 400)],
                 [disp("d", "2026-03-01", 1, "swap", market_value_given_up_aud=1000)])
    assert out["disposals"][0]["capital_proceeds_aud"] == 1000
    assert "given up" in out["disposals"][0]["proceeds_basis"]
    assert out["disposals"][0]["gross_capital_gain"] == approx(600)


def test_swapped_asset_clock_restarts_and_chain_of_swaps():
    # BTC bought 1 Jan 2024 for 10,000, swapped 1 Jun 2026 for ETH worth 30,000 (gain 20,000, discount -> 10,000).
    # ETH acquired 1 Jun 2026 at 30,000; sold 1 Dec 2026 for 33,000: gain 3,000 with NO discount (6 months).
    # Each year is netted on its own: 2025-26 net 10,000; 2026-27 net 3,000.
    out = ledger([acq("b", "2024-01-01", 1, 10000, asset="BTC")],
                 [disp("s1", "2026-06-01", 1, "swap", asset="BTC", value_received_aud=30000,
                       received_asset="ETH", received_quantity=10),
                  disp("s2", "2026-12-01", 10, asset="ETH", value_received_aud=33000)])
    assert out["disposals"][0]["event_income_year"] == "2025-26"
    assert out["disposals"][1]["event_income_year"] == "2026-27"
    assert out["disposals"][1]["slices"][0]["held_over_12_months"] is False
    y = out["net_capital_gain_by_income_year"]
    assert y["2025-26"]["net_capital_gain"] == approx(10000)
    assert y["2026-27"]["net_capital_gain"] == approx(3000)


def test_prior_year_loss_carries_into_the_next_income_year():
    # 2025-26: bought 1 Jan 2025 for 1,000, sold 1 Aug 2025 for 600 -> capital loss 400 (no other gains).
    # 2026-27: bought 1 Jan 2024 for 1,000, sold 1 Sep 2026 for 2,000 -> gain 1,000 (discount eligible).
    # Loss applied before the discount: (1,000 - 400) x 50% = 300.
    out = ledger([acq("a", "2025-01-01", 1, 1000, asset="P"), acq("b", "2024-01-01", 1, 1000, asset="Q")],
                 [disp("d1", "2025-08-01", 1, asset="P", value_received_aud=600),
                  disp("d2", "2026-09-01", 1, asset="Q", value_received_aud=2000)])
    y = out["net_capital_gain_by_income_year"]
    assert y["2025-26"]["net_capital_gain"] == 0
    assert y["2025-26"]["net_capital_loss_carried_forward"] == approx(400)
    assert y["2026-27"]["net_capital_gain"] == approx(300)


def test_prior_year_net_capital_loss_input_is_applied_to_the_first_year():
    out = ledger([acq("b", "2024-01-01", 1, 1000)], [disp("d2", "2026-09-01", 1, value_received_aud=2000)],
                 prior_year_net_capital_losses=400)
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(300)


# ---- personal use assets through the ledger (W-03)

def test_ledger_pua_case_a_gain_disregarded():
    out = ledger([acq("a", "2026-10-03", 1, 400)],
                 [disp("d", "2026-10-06", 1, "spend_goods_services", value_received_aud=430,
                       treat_as_personal_use_asset=True)])
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == 0
    assert out["disposals"][0]["slices"][0]["cgt"]["method"] == "disregarded"


def test_ledger_pua_case_b_at_threshold_disregarded():
    out = ledger([acq("a", "2027-02-01", 1, 10000)],
                 [disp("d", "2027-02-05", 1, "spend_goods_services", value_received_aud=10600,
                       treat_as_personal_use_asset=True)])
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == 0


def test_ledger_pua_case_c_over_threshold_taxable_900():
    # First element 12,000 > threshold -> gain 900 not disregarded; < 12 months, no discount -> net 900.
    out = ledger([acq("a", "2027-03-01", 1, 12000)],
                 [disp("d", "2027-03-10", 1, "spend_goods_services", value_received_aud=12900,
                       treat_as_personal_use_asset=True)])
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(900)


def test_ledger_pua_threshold_tested_on_the_whole_disposal_not_each_slice():
    # Two parcels of first element 6,000 each (12,000 in total). Spend both on a personal item worth 13,000: the
    # whole disposal is over the threshold, even though each slice alone is under it. Gain 1,000 taxable.
    out = ledger([acq("a", "2027-03-01", 1, 6000), acq("b", "2027-03-01", 1, 6000)],
                 [disp("d", "2027-03-10", 2, "spend_goods_services", value_received_aud=13000,
                       treat_as_personal_use_asset=True)])
    assert out["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(1000)


def test_ledger_pua_case_d_loss_disregarded():
    # W-03 D: first element 9,000 (at or below the threshold), proceeds 8,500: loss 500 disregarded (s108-20(1)).
    out = ledger([acq("a", "2027-03-01", 1, 9000)],
                 [disp("d", "2027-03-04", 1, "spend_goods_services", value_received_aud=8500,
                       treat_as_personal_use_asset=True)])
    y = out["net_capital_gain_by_income_year"]["2026-27"]
    assert y["net_capital_gain"] == 0
    assert y["net_capital_loss_carried_forward"] == 0
    assert out["disposals"][0]["slices"][0]["cgt"]["method"] == "disregarded"


def test_ledger_pua_over_threshold_loss_is_still_disregarded():
    # First element 12,000 (over the threshold), proceeds 11,000: loss 1,000 is a personal use asset loss, always
    # disregarded (s108-20(1)): it must not offset gains or carry forward, and the tool reports it as disregarded.
    out = ledger([acq("a", "2027-03-01", 1, 12000)],
                 [disp("d", "2027-03-04", 1, "spend_goods_services", value_received_aud=11000,
                       treat_as_personal_use_asset=True)])
    y = out["net_capital_gain_by_income_year"]["2026-27"]
    assert y["net_capital_gain"] == 0 and y["net_capital_loss_carried_forward"] == 0
    assert y["personal_use_losses_disregarded"] == approx(1000)


def test_ledger_case_e_and_f_investment_spent_on_laptop():
    # W-03 E: 5,000 bought 10 Jan 2026 (not personal use); spent 20 Nov 2026 on a laptop worth 8,000 -> gain 3,000,
    # < 12 months so no discount. F: spent 20 Mar 2027 -> > 12 months -> discount 1,500.
    e = ledger([acq("a", "2026-01-10", 1, 5000)],
               [disp("d", "2026-11-20", 1, "spend_goods_services", value_received_aud=8000)])
    f = ledger([acq("a", "2026-01-10", 1, 5000)],
               [disp("d", "2027-03-20", 1, "spend_goods_services", value_received_aud=8000)])
    assert e["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(3000)
    assert f["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(1500)


# ---- lost or stolen (W-07)

def test_w07_lost_key_c1_capital_loss():
    # W-07: 0.8 BTC cost 48,000, loss discovered 12 Feb 2027, no compensation -> C1, proceeds nil, capital loss
    # 48,000; it cannot reduce other income and is carried forward (no gains).
    out = ledger([acq("b", "2025-05-05", 0.8, 48000, asset="BTC")],
                 [disp("l", "2027-02-12", 0.8, "lost_or_stolen", asset="BTC", evidence_adequate=True)])
    assert out["disposals"][0]["slices"][0]["cgt"]["capital_loss"] == approx(48000)
    y = out["net_capital_gain_by_income_year"]["2026-27"]
    assert y["net_capital_gain"] == 0
    assert y["net_capital_loss_carried_forward"] == approx(48000)


def test_w07_variant_compensation_reduces_the_loss():
    # Compensation of 10,000 first received 1 Apr 2027 -> event date 1 Apr 2027, proceeds 10,000, loss 38,000.
    out = ledger([acq("b", "2025-05-05", 0.8, 48000, asset="BTC")],
                 [disp("l", "2027-04-01", 0.8, "lost_or_stolen", asset="BTC", value_received_aud=10000,
                       evidence_adequate=True)])
    assert out["disposals"][0]["slices"][0]["cgt"]["capital_loss"] == approx(38000)


def test_lost_without_adequate_evidence_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-004",
            acquisitions=[acq("b", "2025-05-05", 0.8, 48000, asset="BTC")],
            disposals=[disp("l", "2027-02-12", 0.8, "lost_or_stolen", asset="BTC", evidence_adequate=False)])


# ---- 1 July 2027 (defers to cgt)

def test_w08_across_1_july_2027_splits_deferred_discounted_gain(synthetic_post_2027_cpi):
    # W-08: cost 100,000 (10 Jan 2026); market value just before 1 Jul 2027 evidenced at 140,000; sold 15 Mar 2028
    # for 155,000. Deferred gain 140,000 - 100,000 = 40,000, held > 12 months -> discount 50% = 20,000.
    # Post-1 July 2027: reacquired 1 Jul 2027 at 140,000, indexed by March 2028 quarter 156.0 / September 2027
    # quarter 150.0 (synthetic test index numbers, tests/conftest.py) = 1.04 -> 145,600; gain 155,000 - 145,600
    # = 9,400, no discount. Net capital gain 2027-28 = 40,000 - 20,000 + 9,400 = 29,400.
    out = ledger([acq("b", "2026-01-10", 1, 100000, asset="BTC", market_value_30_june_2027_per_unit=140000)],
                 [disp("d", "2028-03-15", 1, asset="BTC", value_received_aud=155000)])
    comps = out["disposals"][0]["slices"][0]["cgt"]["components"]
    deferred = [c for c in comps if str(c["category"]).startswith("deferred")][0]
    post = [c for c in comps if not str(c["category"]).startswith("deferred")][0]
    assert deferred["gain"] == approx(40000) and deferred["discount_percentage"] == 0.5
    assert post["gain"] == approx(9400) and post["discount_percentage"] == 0
    assert out["disposals"][0]["law_regime"] == "from_1_july_2027"
    yr = out["net_capital_gain_by_income_year"]["2027-28"]
    assert yr["discount_amount"] == approx(20000)
    assert yr["net_capital_gain"] == approx(29400)


def test_w08_unpublished_index_numbers_give_deferred_component_and_refuse_post_part():
    # The same sale against the real rates file: cgt.indexation_cpi_from_2027 is null, so the indexed post-1 July 2027 part
    # cannot be worked out and is refused AU-GEN-003 at field level (no upper bound shown). The deferred component does
    # not need it: deferred gain 140,000 - 100,000 = 40,000, held over 12 months, 50% = 20,000, after discount 20,000.
    code, out = run("crypto_parcel_ledger", YEAR, dict(
        acquisitions=[acq("b", "2026-01-10", 1, 100000, asset="BTC", market_value_30_june_2027_per_unit=140000)],
        disposals=[disp("d", "2028-03-15", 1, asset="BTC", value_received_aud=155000)]))
    assert code == 0, out
    d = out["disposals"][0]
    assert d["deferred_gain_aud"] == approx(40000) and d["deferred_gain_discount_aud"] == approx(20000)
    assert d["deferred_gain_after_discount_aud"] == approx(20000)
    assert d["gross_capital_gain"] is None and d["gain_less_loss_aud"] is None
    assert d["field_refusals"][0]["code"] == "AU-GEN-003"
    assert "cgt.indexation_cpi_from_2027" in d["field_refusals"][0]["detail"]
    assert out["field_refusals"][0]["code"] == "AU-GEN-003"
    yr = out["net_capital_gain_by_income_year"]["2027-28"]
    assert yr["incomplete"] is True and yr["net_capital_gain"] is None
    assert yr["net_capital_gain_known_components_only"] == approx(20000)


def test_hold_across_1_july_2027_two_eth_deferred_component():
    # 2 ETH bought 5 Mar 2026 for 24,000; market value just before 1 Jul 2027 evidenced at 36,000 (18,000 per ETH);
    # sold 20 Oct 2027 for 39,000. Deferred notional gain 36,000 - 24,000 = 12,000; held 5 Mar 2026 to 20 Oct 2027 (over 12
    # months, the deemed sale ignored) so the 50% discount = 6,000 and the discounted amount is 6,000. The post-1 July 2027
    # part (39,000 less 36,000 indexed) needs the unpublished CPI: refused at field level.
    out = ledger([acq("eth", "2026-03-05", 2, 24000, asset="ETH", market_value_30_june_2027_per_unit=18000)],
                 [disp("s1", "2027-10-20", 2, asset="ETH", value_received_aud=39000)])
    d = out["disposals"][0]
    assert d["deferred_gain_aud"] == approx(12000)
    assert d["deferred_gain_discount_aud"] == approx(6000)
    assert d["deferred_gain_after_discount_aud"] == approx(6000)
    assert d["field_refusals"][0]["field"] == "post_1_july_2027_part" and d["field_refusals"][0]["code"] == "AU-GEN-003"
    assert out["deferred_components"] == [{"disposal": "s1", "parcel": "eth", "notional_gain": approx(12000),
                                           "notional_loss": 0.0, "discount_percentage": 0.5,
                                           "discount_amount": approx(6000), "gain_after_discount": approx(6000)}]
    yr = out["net_capital_gain_by_income_year"]["2027-28"]
    assert yr["net_capital_gain"] is None and yr["net_capital_gain_known_components_only"] == approx(6000)


def test_2027_disposal_without_market_value_propagates_cgt_refusal():
    refused("crypto_parcel_ledger", "AU-CGT-006",
            acquisitions=[acq("b", "2026-01-10", 1, 100000, asset="BTC")],
            disposals=[disp("d", "2028-03-15", 1, asset="BTC", value_received_aud=155000)])


def test_asset_acquired_after_1_july_2027_has_no_discount_and_is_indexed(synthetic_post_2027_cpi):
    # Acquired 1 Sep 2027 for 10,000 (September 2027 quarter, synthetic index 150.0), sold 1 Dec 2028 for 15,000
    # (December 2028 quarter, synthetic 160.5). Factor 160.5 / 150.0 = 1.07 -> cost base 10,700; gain 4,300, no discount.
    out = ledger([acq("b", "2027-09-01", 1, 10000, asset="BTC")],
                 [disp("d", "2028-12-01", 1, asset="BTC", value_received_aud=15000)])
    s = out["disposals"][0]["slices"][0]["cgt"]
    assert s["gross_capital_gain"] == approx(4300) and s["discount_percentage"] == 0
    assert out["net_capital_gain_by_income_year"]["2028-29"]["net_capital_gain"] == approx(4300)


def test_sale_in_a_year_with_no_rates_file_refuses():
    # A disposal on 1 Dec 2028 falls in 2028-29, which has no rates file: nothing is carried forward from 2027-28.
    code, out = run("crypto_parcel_ledger", YEAR, dict(
        acquisitions=[acq("b", "2027-09-01", 1, 10000, asset="BTC")],
        disposals=[disp("d", "2028-12-01", 1, asset="BTC", value_received_aud=15000)]))
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"
    assert "2028-29" in out["refusal"]["detail"]


# ---- holder gates

def test_business_or_trader_is_refused():
    refused("crypto_parcel_ledger", "AU-CRYPTO-001", acquisitions=[acq("a", "2025-01-01", 1, 100)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=200)], holder_character="business_or_trader")


def test_foreign_or_temporary_resident_is_refused():
    for r in ("foreign", "temporary_resident"):
        refused("crypto_parcel_ledger", "AU-CRYPTO-005", acquisitions=[acq("a", "2025-01-01", 1, 100)],
                disposals=[disp("d", "2026-03-01", 1, value_received_aud=200)], residency=r)


def test_non_individual_entity_uses_the_cgt_code():
    refused("crypto_parcel_ledger", "AU-CGT-003", acquisitions=[acq("a", "2025-01-01", 1, 100)],
            disposals=[disp("d", "2026-03-01", 1, value_received_aud=200)], entity_type="trust")


def test_unknown_character_is_an_assumption_not_a_refusal():
    out = ledger([acq("a", "2025-01-01", 1, 100)], [disp("d", "2026-03-01", 1, value_received_aud=200)])
    assert any("capital account" in a.lower() for a in out["assumptions"])


def test_capital_gain_inputs_are_returned_for_reuse():
    out = ledger([acq("A", "2025-01-01", 10, 1000, 50)],
                 [disp("d", "2026-08-01", 4, value_received_aud=800, incidental_costs_disposal_aud=20)])
    row = out["capital_gain_inputs"][0]
    assert row["acquisition_date"] == "2025-01-01" and row["event_date"] == "2026-08-01"
    assert row["capital_proceeds"] == approx(800) and row["first_element"] == approx(400)
    assert row["incidental_costs_acquisition"] == approx(20) and row["incidental_costs_disposal"] == approx(20)
    assert row["asset_type"] == "crypto"


def test_compute_cgt_false_matches_parcels_without_calling_cgt():
    out = ledger([acq("A", "2025-01-01", 10, 1000, 50)],
                 [disp("d", "2026-08-01", 4, value_received_aud=800, incidental_costs_disposal_aud=20)],
                 compute_cgt=False)
    assert "cgt" not in out["disposals"][0]["slices"][0]
    assert out["disposals"][0]["slices"][0]["cost_base_aud"] == approx(440)
    assert out["net_capital_gain_by_income_year"] == {}


def test_quantity_rounding_is_exact_for_fractional_units():
    # 0.1 + 0.2 of a coin must not leave float dust: buy 0.3, sell 0.1 then 0.2 -> nothing remains.
    out = ledger([acq("A", "2025-01-01", 0.3, 300)],
                 [disp("d1", "2026-02-01", 0.1, value_received_aud=100),
                  disp("d2", "2026-03-01", 0.2, value_received_aud=200)])
    assert out["parcels_remaining"] == []


def test_swap_received_parcel_carries_its_30_june_2027_value_into_a_later_sale(synthetic_post_2027_cpi):
    # BTC bought 1 Jan 2025 for 10,000; swapped 1 Sep 2026 for ETH worth 20,000 (gain 10,000 before discount).
    # ETH (acquired 1 Sep 2026, first element 20,000) is worth 26,000 just before 1 Jul 2027 (supplied) and sold
    # 1 Dec 2027 for 30,000. Deferred gain 26,000 - 20,000 = 6,000; held from 1 Sep 2026 to 1 Dec 2027 (past
    # 12 months: 1 Sep 2027 is the anniversary), so the deferred gain is discounted: 6,000 x 50% = 3,000.
    # Post-1 July 2027: reacquired at 26,000, factor December 2027 quarter 153.0 / September 2027 quarter 150.0
    # (synthetic test index numbers) = 1.02 -> 26,520; gain 30,000 - 26,520 = 3,480, no discount.
    out = ledger([acq("b", "2025-01-01", 1, 10000, asset="BTC")],
                 [disp("s", "2026-09-01", 1, "swap", asset="BTC", value_received_aud=20000, received_asset="ETH",
                       received_quantity=5, received_market_value_30_june_2027_per_unit=5200),
                  disp("d", "2027-12-01", 5, asset="ETH", value_received_aud=30000)])
    comps = out["disposals"][1]["slices"][0]["cgt"]["components"]
    deferred = [c for c in comps if str(c["category"]).startswith("deferred")][0]
    assert deferred["gain"] == approx(6000) and deferred["discount_percentage"] == 0.5
    post = [c for c in comps if not str(c["category"]).startswith("deferred")][0]
    assert post["gain"] == approx(3480)


def test_remaining_parcels_can_be_fed_back_in_as_acquisitions():
    out = ledger([acq("A", "2025-01-01", 10, 1000, 50)],
                 [disp("d", "2026-08-01", 4, value_received_aud=800)], compute_cgt=False)
    again = ledger(out["parcels_remaining"], [disp("e", "2026-09-01", 6, value_received_aud=900)])
    # Remaining 6 units carry first element 600 + incidental 30 = 630; proceeds 900; gain 270, > 12 months -> net 135.
    assert again["net_capital_gain_by_income_year"]["2026-27"]["net_capital_gain"] == approx(135)


def test_wash_sale_and_borrowing_flags_are_refused():
    base = dict(acquisitions=[acq("a", "2025-01-01", 1, 100)],
                disposals=[disp("d", "2026-08-01", 1, value_received_aud=50)])
    refused("crypto_parcel_ledger", "AU-CRYPTO-008", repurchased_after_loss_sale=True, **base)
    refused("crypto_parcel_ledger", "AU-CRYPTO-007", funded_by_borrowing=True, **base)


def test_every_crypto_refusal_code_is_in_the_catalogue():
    from au_tax.registry import refusal_catalogue
    assert {f"AU-CRYPTO-{n:03d}" for n in range(1, 12)} <= set(refusal_catalogue())
