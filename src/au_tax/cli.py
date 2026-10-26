"""`au-tax` command line entry point. JSON in, JSON out."""

from __future__ import annotations

import argparse
import json
import sys

from au_tax.lookups import run_lookup
from au_tax.registry import run


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
    return emit(*run_lookup(args.command, args.year, payload, args.allow_draft))


if __name__ == "__main__":
    sys.exit(main())
