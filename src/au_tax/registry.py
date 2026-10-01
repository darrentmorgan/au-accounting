"""Calculator registry. Each module in au_tax.calculators registers itself with @calculator;
no shared file needs editing when a domain adds a calculator."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Callable, get_args

import yaml
from pydantic import BaseModel

from au_tax.figures import FigureError, Figures

REFUSALS_DIR = Path(__file__).resolve().parents[2] / "data" / "refusals"


class Refusal(Exception):
    """Raise with a code from data/refusals/*.yaml to stop a calculation."""

    exit_code = 3

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


class InputError(ValueError):
    """Raise when inputs contradict each other in a way only the calculator can see (for example nights that
    do not add up to the days in the income year). Exit code 2, like a validation error."""


@cache
def refusal_catalogue() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(REFUSALS_DIR.glob("*.yaml")):  # au.yaml = general; <domain>.yaml per domain
        for r in (yaml.safe_load(path.read_text()) or {}).get("refusals", []):
            out[r["code"]] = r
    return out


def figure_refusal(e: FigureError) -> dict:
    """Refusal block for a FigureError: AU-GEN-001 (unverified, draft available) or AU-GEN-003
    (no published value, no draft possible), with the figure detail passed through."""
    entry = refusal_catalogue().get(e.code, {})
    return {"code": e.code, "message": entry.get("message"), "route": entry.get("route"),
            "detail": str(e)}


@dataclass(frozen=True)
class Calculator:
    name: str
    description: str
    input_model: type[BaseModel]
    fn: Callable[[Figures, Any], dict]


REGISTRY: dict[str, Calculator] = {}


def _nested_models(annotation: Any) -> list[type[BaseModel]]:
    """Every BaseModel subclass reachable through an annotation (list[X], X | None, dict[str, X]...)."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    out: list[type[BaseModel]] = []
    for arg in get_args(annotation):
        out += _nested_models(arg)
    return out


def forbid_extra(model: type[BaseModel], _seen: set | None = None) -> None:
    """Make a model and every nested model reject unknown keys, so a misspelt field is an input
    error (exit 2) rather than a silently ignored one. Nested models are rebuilt first so the
    parent's schema picks up their strict config."""
    seen = set() if _seen is None else _seen
    if model in seen:
        return
    seen.add(model)
    for field in model.model_fields.values():
        for sub in _nested_models(field.annotation):
            forbid_extra(sub, seen)
    if model.model_config.get("extra") != "forbid":
        model.model_config["extra"] = "forbid"
    model.model_rebuild(force=True)


def calculator(name: str, input_model: type[BaseModel]):
    """Register fn(figures, inputs) -> dict. The docstring becomes the tool description."""

    def wrap(fn):
        if name in REGISTRY:
            raise ValueError(f"duplicate calculator {name}")
        forbid_extra(input_model)
        REGISTRY[name] = Calculator(name, (fn.__doc__ or "").strip(), input_model, fn)
        return fn

    return wrap


@cache
def load_all() -> dict[str, Calculator]:
    import au_tax.calculators as pkg

    for mod in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"{pkg.__name__}.{mod.name}")
    return REGISTRY


def run(name: str, income_year: str, payload: dict, allow_draft: bool = False) -> tuple[int, dict]:
    """Run a calculator and return (exit_code, envelope). Never raises for expected failures."""
    calcs = load_all()
    if name not in calcs:
        return 2, {"error": f"unknown calculator {name}", "available": sorted(calcs)}
    calc = calcs[name]
    try:
        inputs = calc.input_model.model_validate(payload)
    except Exception as e:  # pydantic ValidationError
        return 2, {"error": f"invalid input: {e}"}
    try:
        figures = Figures(income_year, allow_draft=allow_draft)
        result = calc.fn(figures, inputs)
    except FigureError as e:
        return e.exit_code, {"error": str(e), "income_year": income_year, "refusal": figure_refusal(e)}
    except InputError as e:  # facts that contradict each other (for example day counts), found once figures are known
        return 2, {"error": f"invalid input: {e}", "income_year": income_year}
    except Refusal as r:
        entry = refusal_catalogue().get(r.code)
        if entry is None:
            return 2, {"error": f"calculator raised unknown refusal code {r.code}"}
        return r.exit_code, {"income_year": income_year,
                             "refusal": {"code": r.code, "message": entry["message"],
                                         "route": entry.get("route"), "detail": r.detail}}
    return 0, {"income_year": income_year, **result,
               "figures_used": figures.report(), "draft": figures.draft}
