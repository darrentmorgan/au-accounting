"""2027-28 rates file (as at 2026-09-29) and the 2026-27 checked_at rule.

Expected values are read from the primary sources named in each figure's `source` (statute text, ATO pages), not produced by our code.
"""
import datetime as dt

import pytest

from au_tax.figures import FigureError, Figures, load_year


def raw(year: str, key: str) -> dict:
    """The raw figure mapping (value, status, checked_at ...) for domain.key, domain keys may contain dots."""
    data = load_year(year)
    for dom, figs in data.items():
        if dom != "meta" and key.startswith(dom + "."):
            name = key[len(dom) + 1:]
            if name in figs:
                return figs[name]
    raise KeyError(key)


def test_2027_28_meta():
    meta = load_year("2027-28")["meta"]
    assert meta["income_year"] == "2027-28"
    assert meta["start"] == dt.date(2027, 7, 1) and meta["end"] == dt.date(2028, 6, 30)
    assert meta["fbt_year_ending"] == dt.date(2028, 3, 31)


def test_resident_rates_2027_28_from_the_rates_act():
    # ITRA Sch 7 Pt I cl 1, 2027-28 table: 14% to $45,000, 30% to $135,000, 37% to $190,000, 45% above;
    # tax-free threshold $18,200. Bases by hand: 0.14 x 26,800 = 3,752; + 0.30 x 90,000 = 30,752; + 0.37 x 55,000 = 51,102.
    rates = Figures("2027-28").get("individual.resident_rates")
    assert [(b["from"], b["to"], b["rate"], b["base"]) for b in rates] == [
        (0, 18200, 0, 0), (18200, 45000, 0.14, 0), (45000, 135000, 0.30, 3752),
        (135000, 190000, 0.37, 30752), (190000, None, 0.45, 51102)]
    # One fact, one key: the 14% second-bracket rate is the resident_rates table itself; the old separate key
    # (individual.resident_second_bracket_rate_from_2027_28) was removed from both years' files.
    for year in ("2026-27", "2027-28"):
        with pytest.raises(FigureError):
            Figures(year).get("individual.resident_second_bracket_rate_from_2027_28")


@pytest.mark.parametrize("key,expected", [
    ("individual.working_australians_tax_offset_max", 250),       # ITAA 1997 s 61-160 (Tax Reform No. 1 Act 2026 Sch 3)
    ("individual.standard_work_deduction_cap", 1000),             # s 25-130
    ("super.listo_ati_limit", 45000),                             # Co-contribution Act s 12C as amended, 2027-28 onwards
    ("super.listo_max", 810),                                     # 45,000 x 12% x 15%
    ("super.sg_rate", 0.12),                                      # ATO SG table: 12.00 from 1 July 2027
    ("super.div293_threshold", 250000),
    ("cgt.minimum_tax_rate_from_2027_28", 0.3),                   # ITAA 1997 s 119-10(2) step 1
    ("cgt.discount_individual_trust", 0),                         # s 115-100(f) for events on or after 1 Jul 2027
    ("cgt.discount_new_residential_dwelling", 0.5),               # s 115-100(a), s 115-102
    ("cgt.discount_individual_trust_deferred_gain", 0.5),         # s 115-100(aa), (ab) via the 30 Jun 2027 deemed sale
    ("penalties_interest.penalty_unit", 364),                     # next indexation 1 Jul 2029 (Crimes Act s 4AA(3))
    ("company.rate_base_rate_entity", 0.25),
    ("state.sa.payroll_tax_threshold_annual", 1500000),
    ("fbt.return_due_date", 20280521),                            # 21 May 2028 (a Sunday; next business day rule is applied by calculators)
])
def test_legislated_2027_28_figures_are_verified(key, expected):
    assert Figures("2027-28").get(key) == pytest.approx(expected)
    assert raw("2027-28", key)["status"] == "VERIFIED"


@pytest.mark.parametrize("key", [
    "super.concessional_cap", "super.transfer_balance_cap", "super.max_contribution_base_annual", "help.repayment_schedule",
    "medicare.mls_single_tiers", "medicare.low_income_single_lower", "individual.sapto_shade_out_single",
    "individual.etp_cap", "car_home.car_limit", "car_home.home_office_fixed_rate_per_hour", "fbt.benchmark_interest_rate",
    "asic.annual_review_proprietary", "penalties_interest.gic_quarterly", "penalties_interest.sic_quarterly",
    "div7a.benchmark_interest_rate", "payroll.payg_scale1_no_tft", "state.sa.land_tax_general_scale",
    "cgt.indexation_cpi_from_2027", "payg_instalments.gdp_adjustment"])
def test_unpublished_2027_28_figures_refuse_even_in_draft_mode(key):
    with pytest.raises(FigureError) as e:
        Figures("2027-28", allow_draft=True).get(key)
    assert e.value.code == "AU-GEN-003"


def test_every_null_figure_carries_checked_at_and_a_note():
    for year in ("2026-27", "2027-28"):
        nulls = 0
        for dom, figs in load_year(year).items():
            if dom == "meta":
                continue
            for name, fig in figs.items():
                if fig["value"] is None:
                    nulls += 1
                    assert fig["status"] == "SUSPECT", (year, dom, name)
                    assert isinstance(fig.get("checked_at"), dt.date), (year, dom, name)
                    assert fig.get("notes"), (year, dom, name)
        assert nulls > 0


def test_2026_27_unpublished_figures_stay_null_with_url_checked():
    # None published for 2026-27: scoped single lower re-read 2026-10-09; others checked 2026-09-29.
    for key in ("medicare.low_income_single_lower", "medicare.low_income_family_upper", "medicare.low_income_per_child_lower_add",
                "medicare.low_income_sapto_single_upper", "car_home.home_office_fixed_rate_per_hour",
                "penalties_interest.gic_jan_mar_2027", "penalties_interest.sic_apr_jun_2027", "medicare.phi_rebate_from_2027_04_01"):
        fig = raw("2026-27", key)
        assert fig["value"] is None and fig["status"] == "SUSPECT"
        expected_check = dt.date(2026, 10, 9) if key == "medicare.low_income_single_lower" else dt.date(2026, 9, 29)
        assert fig["checked_at"] == expected_check
        assert fig["source"].startswith("https://www.ato.gov.au/")


@pytest.mark.parametrize("key,expected", [
    ("asic.annual_review_proprietary", 342),                 # ASIC INFO 30, from 1 Jul 2026
    ("asic.annual_review_special_purpose_proprietary", 70),
    ("asic.company_registration_fee", 636),
    ("asic.late_fee_lower", 102),
    ("asic.late_fee_higher", 428),
])
def test_2026_27_asic_fees_now_verified_from_info_30(key, expected):
    assert Figures("2026-27").get(key) == expected
    fig = raw("2026-27", key)
    assert fig["status"] == "VERIFIED"
    assert fig["source"].startswith("https://www.asic.gov.au/")
