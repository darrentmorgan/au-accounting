"""Lookup input boundaries and envelopes stay consistent through CLI and the MCP SDK."""

import json

import anyio
import pytest

from au_tax import lookups, mcp_server
from au_tax.cli import main


@pytest.mark.parametrize("command,payload", [
    ("keys", {"allow_darft": True}),
    ("keys", {"key": "gst.rate"}),
    ("keys", []),
    ("keys", None),
    ("keys", "gst.rate"),
    ("figure", {}),
    ("figure", {"key": "gst.rate", "allow_darft": True}),
    ("figure", {"key": None}),
    ("figure", {"key": True}),
    ("figure", []),
])
@pytest.mark.parametrize("year", ["2026-27", "../2026-27"])
def test_lookup_validates_payload_before_rate_access(monkeypatch, capsys, command, payload, year):
    def unexpected_read(*args, **kwargs):
        pytest.fail("invalid input reached rate loading")

    monkeypatch.setattr(lookups, "Figures", unexpected_read)
    code = main([command, "--year", year, "--json", json.dumps(payload)])
    out = json.loads(capsys.readouterr().out)
    assert code == out["exit_code"] == 2
    assert "invalid input" in out["error"]
    assert "value" not in out and "keys" not in out


@pytest.mark.parametrize("command,year,payload,draft,code,refusal", [
    ("keys", "2026-27", {}, False, 0, None),
    ("keys", "../2026-27", {}, False, 4, "AU-GEN-003"),
    ("keys", "2031-32", {}, False, 4, "AU-GEN-003"),
    ("figure", "2026-27", {"key": "gst.rate"}, False, 0, None),
    ("figure", "2026-27", {"key": "gst"}, False, 4, "AU-GEN-003"),
    ("figure", "2026-27", {"key": "no.such.key"}, False, 4, "AU-GEN-003"),
    ("figure", "2026-27", {"key": "medicare.low_income_single_lower"}, True, 4, "AU-GEN-003"),
    ("figure", "2026-27", {"key": "state.nsw.foreign_purchaser_duty_surcharge"}, False, 4, "AU-GEN-001"),
    ("figure", "2026-27", {"key": "state.nsw.foreign_purchaser_duty_surcharge"}, True, 0, None),
])
def test_cli_and_sdk_lookup_envelopes_match(capsys, command, year, payload, draft, code, refusal):
    args = [command, "--year", year, "--json", json.dumps(payload)]
    if draft:
        args.append("--allow-draft")
    assert main(args) == code
    cli = json.loads(capsys.readouterr().out)
    server = mcp_server.build()
    tool = "list_figures" if command == "keys" else "get_figure"
    arguments = {"income_year": year, **payload}
    if command == "figure":
        arguments["allow_draft"] = draft

    async def call():
        return await server.call_tool(tool, arguments)

    mcp = json.loads(anyio.run(call).content[0].text)
    if command == "figure" and refusal:
        assert mcp.pop("refusal_code") == refusal  # existing MCP compatibility alias
    assert cli == mcp
    assert cli["exit_code"] == code
    assert cli["income_year"] == year
    if refusal:
        assert cli["refusal"]["code"] == refusal
        assert cli["refusal"]["message"]
    else:
        assert isinstance(cli["figures_used"], list)
        assert cli["draft"] is draft
