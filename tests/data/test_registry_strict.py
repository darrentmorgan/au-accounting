"""Every calculator input model (and every model nested in one) rejects unknown keys, so a
misspelt field is an input error (exit 2), never a silently ignored one (judge MAJOR 1)."""

import json

import pytest

from au_tax.cli import main
from au_tax.registry import _nested_models, load_all, run

CALCS = sorted(load_all().items())


def _all_models(model, seen=None):
    seen = set() if seen is None else seen
    if model in seen:
        return seen
    seen.add(model)
    for f in model.model_fields.values():
        for sub in _nested_models(f.annotation):
            _all_models(sub, seen)
    return seen


@pytest.mark.parametrize("name,calc", CALCS, ids=[n for n, _ in CALCS])
def test_every_calculator_rejects_unknown_top_level_key(name, calc):
    code, out = run(name, "2026-27", {"zz_misspelt_field": True})
    assert code == 2
    assert "zz_misspelt_field" in out["error"]
    assert "Extra inputs are not permitted" in out["error"]


@pytest.mark.parametrize("name,calc", CALCS, ids=[n for n, _ in CALCS])
def test_every_nested_model_forbids_extra(name, calc):
    for model in _all_models(calc.input_model):
        assert model.model_config.get("extra") == "forbid", f"{name}: {model.__name__}"
        schema = model.model_json_schema()
        assert schema.get("additionalProperties") is False, f"{name}: {model.__name__}"


def test_nested_unknown_key_rejected_through_parent():
    payload = {"transactions": [{"kind": "sale", "amount": 110, "classification": "taxable",
                                 "gst_incl": True}]}
    code, out = run("bas_gst_worksheet", "2026-27", payload)
    assert code == 2 and "gst_incl" in out["error"]
    payload["transactions"][0].pop("gst_incl")
    code, _ = run("bas_gst_worksheet", "2026-27", payload)
    assert code == 0


def test_cli_misspelt_help_flag_exit_2(capsys):
    code = main(["individual_income_tax", "--year", "2026-27", "--json",
                 json.dumps({"taxable_income": 100000, "help_debt": True})])
    out = json.loads(capsys.readouterr().out)
    assert code == 2 and out["exit_code"] == 2 and "help_debt" in out["error"]
