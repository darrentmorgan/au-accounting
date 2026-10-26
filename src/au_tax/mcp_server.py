"""Stdio MCP server exposing figure lookup and every registered calculator as typed tools."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from au_tax.lookups import run_lookup
from au_tax.registry import load_all, run

server = MCPServer(
    name="au-tax",
    instructions=(
        "Deterministic Australian tax calculators and verified rates. Always use these tools for "
        "figures and arithmetic instead of computing tax yourself. Income years look like 2026-27. "
        "Before answering any Australian tax question, load the matching au-accounting skill: it "
        "defines scope, refusal codes and when to escalate to a registered tax agent."
    ),
)


def list_figures(income_year: str) -> dict:
    """List every figure key in the rates file for an income year (e.g. 2026-27), with status and unit."""
    code, out = run_lookup("keys", income_year, {})
    return {"exit_code": code, **out}


def get_figure(income_year: str, key: str, allow_draft: bool = False) -> dict:
    """Get one figure (value, status, primary source) by key, e.g. div7a.benchmark_interest_rate.
    Unverified figures are refused with AU-GEN-001 unless allow_draft is true; a figure with no
    published value is refused with AU-GEN-003 (no draft is possible)."""
    code, out = run_lookup("figure", income_year, {"key": key}, allow_draft)
    if "refusal" in out:
        out["refusal_code"] = out["refusal"]["code"]  # legacy MCP alias
    return {"exit_code": code, **out}


def _make_tool(name: str, model):
    def tool(income_year: str, inputs: model, allow_draft: bool = False) -> dict:  # type: ignore[valid-type]
        code, out = run(name, income_year, inputs.model_dump(), allow_draft)
        return {"exit_code": code, **out}

    tool.__name__ = name
    # Real objects, not strings, so the SDK can build the input schema from the pydantic model.
    tool.__annotations__ = {"income_year": str, "inputs": model, "allow_draft": bool, "return": dict}
    return tool


def build() -> MCPServer:
    server.add_tool(list_figures)
    server.add_tool(get_figure)
    for name, calc in sorted(load_all().items()):
        server.add_tool(_make_tool(name, calc.input_model), name=name,
                        description=calc.description)
    return server


def main() -> None:
    build().run("stdio")


if __name__ == "__main__":
    main()
