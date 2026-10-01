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
