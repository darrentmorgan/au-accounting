import anyio
from pydantic import BaseModel

from au_tax.mcp_server import build
from au_tax.registry import Refusal, calculator, load_all, run


class _In(BaseModel):
    amount: float


@calculator("zz_test_double_benchmark", _In)
def _double(figures, inputs):
    """Test-only calculator."""
    if inputs.amount < 0:
        raise Refusal("AU-GEN-002", "negative")
    return {"result": inputs.amount * 2 * figures.get("div7a.benchmark_interest_rate")}


def test_registry_envelope_and_refusal():
    load_all()
    code, out = run("zz_test_double_benchmark", "2026-27", {"amount": 100})
    assert code == 0 and round(out["result"], 2) == 17.54 and out["draft"] is False
    code, out = run("zz_test_double_benchmark", "2026-27", {"amount": -1})
    assert code == 3 and out["refusal"]["code"] == "AU-GEN-002"
    code, out = run("zz_test_double_benchmark", "2026-27", {"amount": "x"})
    assert code == 2


def test_mcp_tools_listed_and_callable():
    server = build()

    async def go():
        names = {t.name for t in await server.list_tools()}
        assert {"list_figures", "get_figure", "zz_test_double_benchmark"} <= names
        return await server.call_tool("get_figure", {"income_year": "2026-27", "key": "div7a.benchmark_interest_rate"})

    res = anyio.run(go)
    assert "0.0877" in str(res)


def test_total_limitations_survive_cli_and_mcp(capsys):
    import json
    from au_tax.cli import main

    cases = [
        ('individual_income_tax', {'taxable_income': 120000}, 'hospital_cover_not_stated'),
        ('assemble_taxable_income', {
            'components': [{'kind': 'salary_wages', 'amount': 45000, 'source_skill': 'user'}],
            'prior_year_tax_losses': 1000,
        }, 'net_exempt_income_assumed_nil'),
    ]
    server = build()
    for name, payload, identifier in cases:
        assert main([name, '--year', '2025-26', '--json', json.dumps(payload)]) == 0
        cli = json.loads(capsys.readouterr().out)

        async def go():
            return await server.call_tool(name, {'income_year': '2025-26', 'inputs': payload})

        result = anyio.run(go)
        # MCP exposes the same JSON dictionary in its text content.
        mcp = json.loads(result.content[0].text)
        assert cli == mcp
        assert cli['total_complete'] is False
        assert cli['total_status'] == 'conditional'
        assert cli['limitations'][0]['id'] == identifier
