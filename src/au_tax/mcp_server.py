"""Stdio MCP server exposing figure lookup and every registered calculator as typed tools."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from au_tax.cli import list_keys
from au_tax.figures import FigureError, Figures
from au_tax.registry import figure_refusal, load_all, run

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
    try:
        return {"income_year": income_year, "keys": list_keys(Figures(income_year, allow_draft=True).data)}
    except FigureError as e:
        return {"error": str(e)}


def get_figure(income_year: str, key: str, allow_draft: bool = False) -> dict:
    """Get one figure (value, status, primary source) by key, e.g. div7a.benchmark_interest_rate.
    Unverified figures are refused with AU-GEN-001 unless allow_draft is true; a figure with no
    published value is refused with AU-GEN-003 (no draft is possible)."""
    try:
        f = Figures(income_year, allow_draft=allow_draft)
        value = f.get(key)
        return {"income_year": income_year, "key": key, "value": value,
                "figures_used": f.report(), "draft": f.draft}
    except FigureError as e:
        return {"exit_code": e.exit_code, "error": str(e), "income_year": income_year,
                "refusal_code": e.code, "refusal": figure_refusal(e)}


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
