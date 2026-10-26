"""Shared CLI/MCP figure lookup validation and envelopes."""

from pydantic import BaseModel, ConfigDict, ValidationError

from au_tax.figures import FigureError, Figures
from au_tax.registry import figure_refusal


class KeysInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FigureInput(KeysInput):
    key: str


def list_keys(node: dict, prefix: str = "") -> list[dict]:
    """Flatten a rates file into [{key, status, unit}] for discovery."""
    out = []
    for name, child in node.items():
        if name == "meta" and not prefix:
            continue
        key = f"{prefix}{name}"
        if isinstance(child, dict) and "status" in child:
            out.append({"key": key, "status": child["status"], "unit": child.get("unit", "")})
        elif isinstance(child, dict):
            out.extend(list_keys(child, key + "."))
    return out


def run_lookup(command: str, income_year: str, payload: dict,
               allow_draft: bool = False) -> tuple[int, dict]:
    """Validate before opening rates, including the empty payload for key discovery."""
    model = {"keys": KeysInput, "figure": FigureInput}[command]
    try:
        inputs = model.model_validate(payload)
    except ValidationError as e:
        return 2, {"error": f"invalid input: {e}", "income_year": income_year}
    try:
        figures = Figures(income_year, allow_draft=allow_draft)
        if isinstance(inputs, FigureInput):
            result = {"key": inputs.key, "value": figures.get(inputs.key)}
        else:
            result = {"keys": list_keys(figures.data)}
    except FigureError as e:
        return e.exit_code, {"error": str(e), "income_year": income_year,
                             "refusal": figure_refusal(e)}
    return 0, {"income_year": income_year, **result,
               "figures_used": figures.report(), "draft": figures.draft}
