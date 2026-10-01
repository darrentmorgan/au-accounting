"""`au-tax` command line entry point. JSON in, JSON out."""

from __future__ import annotations

import argparse
import json
import sys

from au_tax.figures import FigureError, Figures
from au_tax.registry import figure_refusal, run


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


def emit(code: int, out: dict) -> int:
    """Print the JSON envelope with exit_code first and return the code (CONVENTIONS s5)."""
    print(json.dumps({"exit_code": code, **out}, indent=2, default=str))
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="au-tax")
    parser.add_argument("command", help="keys | figure | <calculator name>")
    parser.add_argument("--year", required=True, help="income year, e.g. 2026-27")
    parser.add_argument("--json", default="{}", help="input payload as JSON")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.json)
    except json.JSONDecodeError as e:
        return emit(2, {"error": f"invalid JSON input: {e}"})

    if args.command not in ("keys", "figure"):
        return emit(*run(args.command, args.year, payload, args.allow_draft))
    try:
        figures = Figures(args.year, allow_draft=args.allow_draft)
        if args.command == "keys":
            result = {"keys": list_keys(figures.data)}
        else:
            result = {"key": payload["key"], "value": figures.get(payload["key"])}
    except FigureError as e:
        return emit(e.exit_code, {"error": str(e), "income_year": args.year,
                                  "refusal": figure_refusal(e)})
    except (KeyError, ValueError, TypeError) as e:
        return emit(2, {"error": f"invalid input: {e}"})

    return emit(0, {"income_year": args.year, **result,
                    "figures_used": figures.report(), "draft": figures.draft})


if __name__ == "__main__":
    sys.exit(main())
