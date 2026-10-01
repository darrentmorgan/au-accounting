import json

import pytest

from au_tax.cli import main
from au_tax.figures import FigureError, Figures


def test_verified_figure_lookup_records_usage():
    f = Figures("2026-27")
    assert f.get("div7a.benchmark_interest_rate") == pytest.approx(0.0877)
    assert not f.draft
    assert f.report()[0]["status"] == "VERIFIED"


def test_unverified_figure_refused_without_draft():
    # SOURCE-CITED with a value (NSW is outside v0.3 scope and stays unverified): refused unless allow_draft.
    with pytest.raises(FigureError, match="SOURCE-CITED"):
        Figures("2026-27").get("state.nsw.foreign_purchaser_duty_surcharge")


def test_missing_year_and_bad_year():
    with pytest.raises(FigureError):
        Figures("2031-32")
    with pytest.raises(FigureError):
        Figures("2026")


def test_cli_exit_codes(capsys):
    assert main(["figure", "--year", "2026-27", "--json", '{"key": "div7a.benchmark_interest_rate"}']) == 0
    assert json.loads(capsys.readouterr().out)["value"] == pytest.approx(0.0877)
    assert main(["figure", "--year", "2026-27", "--json", "{bad"]) == 2
    assert main(["figure", "--year", "2026-27", "--json", '{"key": "nope.nope"}']) == 4


def test_refusal_code_distinguishes_unverified_from_unpublished():
    # not VERIFIED but with a value (SOURCE-CITED here): AU-GEN-001, a draft is possible
    with pytest.raises(FigureError) as e:
        Figures("2026-27").get("state.nsw.foreign_purchaser_duty_surcharge")
    assert e.value.code == "AU-GEN-001"
    assert Figures("2026-27", allow_draft=True).get("state.nsw.foreign_purchaser_duty_surcharge") is not None
    # null value: AU-GEN-003 even in draft mode
    with pytest.raises(FigureError) as e:
        Figures("2026-27", allow_draft=True).get("medicare.low_income_single_lower")
    assert e.value.code == "AU-GEN-003"
    # absent key and absent year: AU-GEN-003
    with pytest.raises(FigureError) as e:
        Figures("2026-27").get("nope.nope")
    assert e.value.code == "AU-GEN-003"
    with pytest.raises(FigureError) as e:
        Figures("2031-32")
    assert e.value.code == "AU-GEN-003"


def test_cli_envelope_always_has_exit_code(capsys):
    cases = [
        (["figure", "--year", "2026-27", "--json", '{"key": "div7a.benchmark_interest_rate"}'], 0, None),
        (["figure", "--year", "2026-27", "--json", "{bad"], 2, None),
        (["figure", "--year", "2026-27", "--json", "{}"], 2, None),
        (["figure", "--year", "2026-27", "--json", '{"key": "state.nsw.foreign_purchaser_duty_surcharge"}'], 4, "AU-GEN-001"),
        (["figure", "--year", "2026-27", "--json", '{"key": "medicare.low_income_single_lower"}'], 4, "AU-GEN-003"),
        (["keys", "--year", "2026-27"], 0, None),
        (["no_such_calculator", "--year", "2026-27"], 2, None),
        (["individual_income_tax", "--year", "2026-27", "--json", '{"taxable_income": 30000}'], 4, "AU-GEN-003"),
        (["individual_income_tax", "--year", "2026-27", "--json", '{"taxable_income": 100000}'], 0, None),
    ]
    for argv, code, refusal in cases:
        assert main(argv) == code, argv
        out = json.loads(capsys.readouterr().out)
        assert out["exit_code"] == code, argv
        if refusal:
            assert out["refusal"]["code"] == refusal, argv


def test_mcp_get_figure_refusal_codes():
    from au_tax.mcp_server import get_figure

    assert get_figure("2026-27", "state.nsw.foreign_purchaser_duty_surcharge")["refusal_code"] == "AU-GEN-001"
    assert get_figure("2026-27", "state.nsw.foreign_purchaser_duty_surcharge", allow_draft=True)["draft"] is True
    out = get_figure("2026-27", "medicare.low_income_single_lower", allow_draft=True)
    assert out["refusal_code"] == "AU-GEN-003" and out["exit_code"] == 4
