# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Validate data/rates/*.yaml. Run: uv run scripts/validate_rates.py [files...]

Checks: meta block, figure schema, allowed statuses, source URL presence,
SUSPECT/null pairing, bracket monotonicity and base continuity. A figure may carry an optional
`checked_at` date (when the source URL was last checked); it is required on null-valued figures
in income years from 2026-27 (FIRST_CHECKED_AT_YEAR).
Prints counts by status per file. Exit 1 on any error.
"""
from __future__ import annotations

import datetime as dt
import sys
from collections import Counter
from pathlib import Path

import yaml

STATUSES = {"VERIFIED", "SOURCE-CITED", "SUSPECT"}
REQUIRED = ("value", "unit", "status", "source", "as_at")
META_REQUIRED = ("income_year", "start", "end", "compiled")
TOL = 1.5  # dollars; ATO publishes rounded bases
FIRST_CHECKED_AT_YEAR = "2026-27"  # null-valued figures must carry checked_at from this income year


def is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_list(path: str, items: list, errs: list[str]) -> None:
    if not items:
        errs.append(f"{path}: empty list")
        return
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errs.append(f"{path}[{i}]: list item must be a mapping")
            return
    if all("rate" in it and "base" in it for it in items):
        check_brackets(path, items, errs)
    else:
        # dated series (e.g. GIC by quarter): need from/to dates, chronological, numeric rate
        prev_to = None
        for i, it in enumerate(items):
            for k in ("from", "to", "rate"):
                if k not in it:
                    errs.append(f"{path}[{i}]: missing '{k}'")
            f, t = it.get("from"), it.get("to")
            if isinstance(f, dt.date) and isinstance(t, dt.date):
                if f > t:
                    errs.append(f"{path}[{i}]: from after to")
                if prev_to and f <= prev_to:
                    errs.append(f"{path}[{i}]: overlaps or out of order")
                prev_to = t
            else:
                errs.append(f"{path}[{i}]: from/to must be dates")
            if not is_num(it.get("rate")):
                errs.append(f"{path}[{i}]: rate must be numeric")


def check_brackets(path: str, items: list, errs: list[str]) -> None:
    n = len(items)
    for i, b in enumerate(items):
        for k in ("from", "to", "rate", "base"):
            if k not in b:
                errs.append(f"{path}[{i}]: missing '{k}'")
        if not is_num(b.get("from")):
            errs.append(f"{path}[{i}]: 'from' must be a number")
        if b.get("to") is not None and not is_num(b.get("to")):
            errs.append(f"{path}[{i}]: 'to' must be a number or null")
        if not is_num(b.get("rate")) or not -1 <= b["rate"] <= 1:
            errs.append(f"{path}[{i}]: 'rate' must be a decimal between -1 and 1 (got {b.get('rate')!r})")
        if not is_num(b.get("base")):
            errs.append(f"{path}[{i}]: 'base' must be a number")
        if b.get("to") is None and i != n - 1:
            errs.append(f"{path}[{i}]: open-ended 'to' only allowed on last bracket")
        if is_num(b.get("to")) and is_num(b.get("from")) and b["to"] <= b["from"]:
            errs.append(f"{path}[{i}]: 'to' must exceed 'from'")
    if n and items[-1].get("to") is not None:
        errs.append(f"{path}: last bracket must have to: null")
    if errs and any(e.startswith(path) for e in errs):
        return
    if items[0]["from"] != 0:
        errs.append(f"{path}: first bracket must start at 0")
    for i in range(1, n):
        p, c = items[i - 1], items[i]
        if c["from"] != p["to"]:
            errs.append(f"{path}[{i}]: gap or overlap (prev.to={p['to']}, from={c['from']})")
            continue
        if p.get("whole_income") or c.get("whole_income"):
            continue
        if p["rate"] == 0:
            continue  # threshold steps (e.g. SA trust land tax jumps to $125 at $25,000)
        expect = p["base"] + p["rate"] * (p["to"] - p["from"])
        if abs(expect - c["base"]) > TOL:
            errs.append(f"{path}[{i}]: base {c['base']} != {expect:.2f} implied by previous bracket")


def check_figure(path: str, fig, errs: list[str], status_counter: Counter, need_checked_at: bool = False) -> None:
    if not isinstance(fig, dict):
        errs.append(f"{path}: figure must be a mapping")
        return
    for k in REQUIRED:
        if k not in fig:
            errs.append(f"{path}: missing '{k}'")
    st = fig.get("status")
    if st not in STATUSES:
        errs.append(f"{path}: status {st!r} not in {sorted(STATUSES)}")
    else:
        status_counter[st] += 1
    src = fig.get("source")
    if not isinstance(src, str) or not src.startswith(("http://", "https://")):
        errs.append(f"{path}: source must be an http(s) URL")
    if not isinstance(fig.get("unit"), str) or not fig.get("unit"):
        errs.append(f"{path}: unit must be a non-empty string")
    if not isinstance(fig.get("as_at"), dt.date):
        errs.append(f"{path}: as_at must be a YYYY-MM-DD date")
    if "notes" in fig and not isinstance(fig["notes"], str):
        errs.append(f"{path}: notes must be a string")
    if "checked_at" in fig and not isinstance(fig["checked_at"], dt.date):
        errs.append(f"{path}: checked_at must be a YYYY-MM-DD date")
    extra = set(fig) - set(REQUIRED) - {"notes", "checked_at"}
    if extra:
        errs.append(f"{path}: unexpected keys {sorted(extra)}")
    v = fig.get("value", "<missing>")
    if v is None:
        if st != "SUSPECT":
            errs.append(f"{path}: null value requires status SUSPECT")
        if not fig.get("notes"):
            errs.append(f"{path}: null value requires a note")
        if need_checked_at and "checked_at" not in fig:
            errs.append(f"{path}: null value requires checked_at (income years from {FIRST_CHECKED_AT_YEAR})")
    elif isinstance(v, list):
        check_list(f"{path}.value", v, errs)
    elif not is_num(v) and not isinstance(v, dt.date):
        errs.append(f"{path}: value must be a number, an ISO date, a bracket list or null (got {type(v).__name__})")


REQUIRED_DOMAINS = ["individual", "medicare", "help", "super", "company", "div7a", "cgt", "gst",
                    "payg_instalments", "penalties_interest", "car_home", "fbt", "payroll_wages", "asic", "state.sa", "state.nsw"]
REQUIRED_KEYS = {
    "individual": ["resident_rates", "foreign_resident_rates", "whm_rates", "lito"],
    "medicare": ["levy_rate", "mls_single_tiers", "mls_family_tiers", "low_income_single_lower", "low_income_family_upper"],
    "help": ["repayment_schedule"],
    "super": ["sg_rate", "concessional_cap", "non_concessional_cap", "transfer_balance_cap", "div293_threshold"],
    "company": ["rate_base_rate_entity", "rate_other", "bre_aggregated_turnover_threshold"],
    "div7a": ["benchmark_interest_rate"],
    "cgt": ["discount_individual_trust", "small_business_aggregated_turnover", "small_business_max_net_asset_value"],
    "gst": ["rate", "registration_threshold"],
    "payg_instalments": ["gdp_adjustment"],
    "penalties_interest": ["penalty_unit", "gic_quarterly", "sic_quarterly"],
    "car_home": ["car_cents_per_km", "car_limit", "home_office_fixed_rate_per_hour"],
    "fbt": ["rate", "gross_up_type1", "gross_up_type2", "benchmark_interest_rate"],
    "state.sa": ["payroll_tax_threshold_annual", "land_tax_general_scale", "land_tax_trust_scale", "stamp_duty_conveyance_scale"],
}


def validate(path: Path) -> tuple[list[str], Counter, int]:
    errs: list[str] = []
    counts: Counter = Counter()
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"], counts, 0
    if not isinstance(doc, dict):
        return ["top level must be a mapping"], counts, 0
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        errs.append("meta: missing")
    else:
        for k in META_REQUIRED:
            if k not in meta:
                errs.append(f"meta: missing '{k}'")
        for k in ("start", "end", "compiled"):
            if k in meta and not isinstance(meta[k], dt.date):
                errs.append(f"meta.{k}: must be a date")
        iy = str(meta.get("income_year", ""))
        if iy and path.stem != iy:
            errs.append(f"meta.income_year {iy!r} does not match filename {path.stem!r}")
        if isinstance(meta.get("start"), dt.date) and isinstance(meta.get("end"), dt.date):
            if meta["start"] >= meta["end"]:
                errs.append("meta: start must precede end")
    total = 0
    need = path.stem >= FIRST_CHECKED_AT_YEAR
    for dom, figs in doc.items():
        if dom == "meta":
            continue
        if not isinstance(figs, dict):
            errs.append(f"{dom}: domain must be a mapping of figure keys")
            continue
        for key, fig in figs.items():
            total += 1
            check_figure(f"{dom}.{key}", fig, errs, counts, need)
    for dom in REQUIRED_DOMAINS:
        if dom not in doc:
            errs.append(f"missing domain '{dom}'")
    for dom, keys in REQUIRED_KEYS.items():
        for k in keys:
            if dom in doc and k not in doc[dom]:
                errs.append(f"{dom}: missing required key '{k}'")
    return errs, counts, total


def validate_overlay(path: Path, base: dict) -> tuple[list[str], Counter, int]:
    """Overlay files (<year>.d/<domain>.yaml) hold domains only; keys must not collide with the base file."""
    errs: list[str] = []
    counts: Counter = Counter()
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"], counts, 0
    total = 0
    need = path.parent.name.split(".")[0] >= FIRST_CHECKED_AT_YEAR
    for dom, figs in doc.items():
        if dom == "meta" or not isinstance(figs, dict):
            errs.append(f"{dom}: overlay must contain domain mappings only")
            continue
        for key, fig in figs.items():
            total += 1
            if key in (base.get(dom) or {}):
                errs.append(f"{dom}.{key}: already defined in base file")
            check_figure(f"{dom}.{key}", fig, errs, counts, need)
    return errs, counts, total


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "data" / "rates"
    files = [Path(a) for a in sys.argv[1:]] or sorted(root.glob("*.yaml"))
    if not files:
        print(f"no rate files found in {root}")
        return 1
    bad = 0
    for f in files:
        errs, counts, total = validate(f)
        print(f"{f.name}: {total} figures | " + ", ".join(f"{s}={counts.get(s, 0)}" for s in sorted(STATUSES)))
        for e in errs:
            print(f"  ERROR {e}")
        bad += len(errs)
        base = yaml.safe_load(f.read_text()) or {}
        for ov in sorted((f.parent / f"{f.stem}.d").glob("*.yaml")):
            errs, counts, total = validate_overlay(ov, base)
            print(f"  overlay {ov.name}: {total} figures | " + ", ".join(f"{s}={counts.get(s, 0)}" for s in sorted(STATUSES)))
            for e in errs:
                print(f"    ERROR {e}")
            bad += len(errs)
    print("FAIL" if bad else "OK", f"({bad} errors)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
