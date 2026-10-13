"""Exercise validation and refusal handling through the SDK tool boundary."""

import json

import anyio
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from au_tax import mcp_server


@pytest.mark.parametrize("name,inputs,field", [
    ("individual_income_tax", {"taxable_income": 100000, "help_debt": True}, "help_debt"),
    ("bas_gst_worksheet", {"transactions": [
        {"kind": "sale", "amount": 110, "classification": "taxable", "gst_incl": True},
    ]}, "inputs.transactions.0.gst_incl"),
])
def test_sdk_rejects_unknown_input_before_calculation(monkeypatch, name, inputs, field):
    server = mcp_server.build()

    def unexpected_run(*args, **kwargs):
        pytest.fail("invalid SDK input reached a calculator")

    monkeypatch.setattr(mcp_server, "run", unexpected_run)

    async def call():
        return await server.call_tool(name, {"income_year": "2026-27", "inputs": inputs})

    with pytest.raises(ToolError) as error:
        anyio.run(call)
    assert field in str(error.value)
    assert "Extra inputs are not permitted" in str(error.value)


@pytest.mark.parametrize("year,key,allow_draft,code", [
    ("2026-27", "state.nsw.foreign_purchaser_duty_surcharge", False, "AU-GEN-001"),
    ("2026-27", "medicare.low_income_single_lower", True, "AU-GEN-003"),
    ("../2026-27", "gst.rate", False, "AU-GEN-003"),
])
def test_sdk_figure_refusal_preserves_envelope(year, key, allow_draft, code):
    server = mcp_server.build()

    async def call():
        return await server.call_tool("get_figure", {
            "income_year": year, "key": key, "allow_draft": allow_draft,
        })

    result = anyio.run(call)
    out = json.loads(result.content[0].text)
    assert out["exit_code"] == 4
    assert out["income_year"] == year
    assert out["refusal_code"] == out["refusal"]["code"] == code
    assert out["refusal"]["message"]
    assert "value" not in out


def test_sdk_explicit_draft_keeps_unverified_provenance():
    server = mcp_server.build()
    key = "state.nsw.foreign_purchaser_duty_surcharge"

    async def call():
        return await server.call_tool("get_figure", {
            "income_year": "2026-27", "key": key, "allow_draft": True,
        })

    out = json.loads(anyio.run(call).content[0].text)
    assert out["draft"] is True
    assert out["income_year"] == "2026-27"
    assert out["figures_used"] == [{"key": key, "value": out["value"],
                                    "status": "SOURCE-CITED",
                                    "source": out["figures_used"][0]["source"]}]
    assert out["figures_used"][0]["source"].startswith("https://")
