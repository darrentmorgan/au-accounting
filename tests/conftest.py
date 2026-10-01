"""Shared fixtures.

`synthetic_post_2027_cpi` exists only to test the indexation ARITHMETIC (ITAA 1997 s110-36(1A), s960-275(1B)) while
the real cgt.indexation_cpi_from_2027 figure is null (no post-2027 quarter is published). Its index numbers are
invented for the tests, labelled as such, and never touch the data files: the fixture patches the loaded data in memory
and restores it after each test. It also lets an income year 2028-29 resolve to a copy of the 2027-28 data so that a
sale in 2028-29 can be exercised before that rates file exists.
"""

import copy
import datetime as dt

import pytest

from au_tax import figures as figures_module

# Invented quarterly index numbers (quarter label = quarter end month). Test data only.
SYNTHETIC_CPI = [
    (dt.date(2027, 7, 1), dt.date(2027, 9, 30), 150.0),     # September 2027 quarter
    (dt.date(2027, 10, 1), dt.date(2027, 12, 31), 153.0),   # December 2027 quarter
    (dt.date(2028, 1, 1), dt.date(2028, 3, 31), 156.0),     # March 2028 quarter
    (dt.date(2028, 4, 1), dt.date(2028, 6, 30), 157.5),     # June 2028 quarter
    (dt.date(2028, 7, 1), dt.date(2028, 9, 30), 159.0),     # September 2028 quarter
    (dt.date(2028, 10, 1), dt.date(2028, 12, 31), 160.5),   # December 2028 quarter
]


@pytest.fixture
def synthetic_post_2027_cpi(monkeypatch):
    base = figures_module.load_year("2027-28")
    monkeypatch.setitem(base["cgt"], "indexation_cpi_from_2027", {
        "value": [{"from": a, "to": b, "rate": r} for a, b, r in SYNTHETIC_CPI],
        "unit": "index number", "status": "VERIFIED", "source": "https://example.invalid/synthetic-test-cpi",
        "as_at": dt.date(2026, 9, 29)})
    real_load = figures_module.load_year

    def load(year):
        if year == "2028-29":
            d = copy.deepcopy(real_load("2027-28"))
            d["meta"].update(income_year="2028-29", start=dt.date(2028, 7, 1), end=dt.date(2029, 6, 30))
            return d
        return real_load(year)

    monkeypatch.setattr(figures_module, "load_year", load)
    yield
