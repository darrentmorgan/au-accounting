"""Load figures from data/rates/<income-year>.yaml and enforce verification status."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

RATES_DIR = Path(__file__).resolve().parents[2] / "data" / "rates"
YEAR_RE = re.compile(r"^\d{4}-\d{2}$")


UNVERIFIED = "AU-GEN-001"  # figure has a value but is not VERIFIED: a draft is possible
UNPUBLISHED = "AU-GEN-003"  # no rates file, key absent, or value null: no draft is possible


class FigureError(Exception):
    """Raised when a figure is missing, or unverified without draft mode.

    `code` is the refusal code: AU-GEN-001 when the figure exists but is not VERIFIED (rerun with
    allow_draft), AU-GEN-003 when there is no published value at all (a draft cannot help)."""

    exit_code = 4

    def __init__(self, message: str, code: str = UNPUBLISHED):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Figure:
    key: str
    value: Any
    unit: str
    status: str
    source: str
    as_at: str


@cache
def load_year(income_year: str) -> dict:
    if not YEAR_RE.match(income_year):
        raise FigureError(f"income year must look like 2026-27, got {income_year!r}")
    path = RATES_DIR / f"{income_year}.yaml"
    if not path.exists():
        raise FigureError(f"no rates file for {income_year}")
    data = yaml.safe_load(path.read_text())
    # Overlays: data/rates/<year>.d/<domain>.yaml, added by domain skills. Keys must not collide.
    for overlay in sorted((RATES_DIR / f"{income_year}.d").glob("*.yaml")):
        for domain, figs in (yaml.safe_load(overlay.read_text()) or {}).items():
            target = data.setdefault(domain, {})
            clash = set(target) & set(figs)
            if clash:
                raise FigureError(f"{overlay.name} redefines {domain}.{sorted(clash)[0]}")
            target.update(figs)
    return data


def _resolve(node: Any, parts: list[str]) -> Any:
    """Walk parts through nested mappings. A mapping key may itself contain dots (e.g. the domain
    key "state.sa"), so try every prefix of the remaining parts joined with dots. None if not found."""
    if not parts:
        return node
    if not isinstance(node, dict):
        return None
    for i in range(1, len(parts) + 1):
        k = ".".join(parts[:i])
        if k in node:
            found = _resolve(node[k], parts[i:])
            if found is not None:
                return found
    return None


class Figures:
    """Figure lookup for one income year that records every key it hands out."""

    def __init__(self, income_year: str, allow_draft: bool = False):
        self.income_year = income_year
        self.allow_draft = allow_draft
        self.data = load_year(income_year)
        self.used: dict[str, Figure] = {}
        self._mirror: tuple[Figures, str] | None = None  # (parent, year suffix) for a for_year() view

    def for_year(self, income_year: str) -> "Figures":
        """Figures for another income year, for a rule that is date-effective (a CGT event or an amount dated in a
        different year from the one the tool was called with). Every figure read through the returned object is also
        recorded on this one as `<key>@<year>`, so `figures_used` and `draft` report it. Raises FigureError
        (AU-GEN-003) when there is no rates file for that year."""
        if income_year == self.income_year:
            return self
        if self._mirror is not None:  # views do not nest: report on the root object
            return self._mirror[0].for_year(income_year)
        other = Figures(income_year, self.allow_draft)
        other._mirror = (self, income_year)
        return other

    def get(self, key: str) -> Any:
        node = _resolve(self.data, key.split("."))
        if node is None:
            raise FigureError(f"figure {key} not in {self.income_year} rates file")
        if not isinstance(node, dict) or "status" not in node:
            raise FigureError(f"{key} is a group, not a figure")
        fig = Figure(key, node.get("value"), node.get("unit", ""), node["status"],
                     node.get("source", ""), str(node.get("as_at", "")))
        if fig.value is None:
            raise FigureError(f"figure {key} has no published value for {self.income_year}; no draft is possible")
        if fig.status != "VERIFIED" and not self.allow_draft:
            raise FigureError(f"figure {key} is {fig.status}; rerun with --allow-draft to produce a draft",
                              UNVERIFIED)
        self.used[key] = fig
        if self._mirror is not None:
            parent, year = self._mirror
            tagged = f"{key}@{year}"
            parent.used[tagged] = Figure(tagged, fig.value, fig.unit, fig.status, fig.source, fig.as_at)
        return fig.value

    @property
    def draft(self) -> bool:
        return any(f.status != "VERIFIED" for f in self.used.values())

    def report(self) -> list[dict]:
        return [{"key": f.key, "value": f.value, "status": f.status, "source": f.source}
                for f in self.used.values()]
