"""Rate-file integrity and provenance safeguards, using synthetic figures only."""

import pytest
import yaml

from au_tax import figures as module
from au_tax.figures import FigureError, Figures


@pytest.fixture
def rates_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "RATES_DIR", tmp_path)
    module.load_year.cache_clear()
    yield tmp_path
    module.load_year.cache_clear()


def write_rates(root, year, status="VERIFIED", value=10):
    (root / f"{year}.yaml").write_text(yaml.safe_dump({
        "demo": {"amount": {"value": value, "status": status,
                             "unit": "AUD", "source": "https://example.invalid/test"}},
    }))


def test_overlay_cannot_replace_base_rate(rates_dir):
    write_rates(rates_dir, "2025-26")
    overlay = rates_dir / "2025-26.d"
    overlay.mkdir()
    (overlay / "override.yaml").write_text(yaml.safe_dump({
        "demo": {"amount": {"value": 999, "status": "VERIFIED"}},
    }))

    with pytest.raises(FigureError, match=r"override.yaml redefines demo.amount"):
        Figures("2025-26")


def test_overlay_cannot_replace_another_overlay_rate(rates_dir):
    write_rates(rates_dir, "2025-26")
    overlay = rates_dir / "2025-26.d"
    overlay.mkdir()
    for name in ("a.yaml", "b.yaml"):
        (overlay / name).write_text(yaml.safe_dump({
            "other": {"amount": {"value": 20, "status": "VERIFIED"}},
        }))

    with pytest.raises(FigureError, match=r"b.yaml redefines other.amount"):
        Figures("2025-26")


@pytest.mark.parametrize("status,draft", [("VERIFIED", False), ("SOURCE-CITED", True)])
def test_cross_year_views_preserve_root_provenance(rates_dir, status, draft):
    write_rates(rates_dir, "2025-26")
    write_rates(rates_dir, "2026-27", status=status, value=20)
    write_rates(rates_dir, "2027-28", value=30)
    root = Figures("2025-26", allow_draft=True)
    assert root.for_year("2025-26") is root
    view = root.for_year("2026-27")
    assert view.get("demo.amount") == 20
    assert view.get("demo.amount") == 20
    assert root.draft is draft
    assert root.report() == [{"key": "demo.amount@2026-27", "value": 20,
                              "status": status, "source": "https://example.invalid/test"}]

    # A view for a third year must still report to the original root.
    assert view.for_year("2027-28").get("demo.amount") == 30
    assert [r["key"] for r in root.report()] == ["demo.amount@2026-27", "demo.amount@2027-28"]
    assert [r["key"] for r in view.report()] == ["demo.amount"]


@pytest.mark.parametrize("value,status,code,allow_draft", [
    (None, "SUSPECT", "AU-GEN-003", True),
    (20, "SOURCE-CITED", "AU-GEN-001", False),
])
def test_refused_cross_year_rate_is_not_recorded(rates_dir, value, status, code, allow_draft):
    write_rates(rates_dir, "2025-26")
    write_rates(rates_dir, "2026-27", status=status, value=value)
    root = Figures("2025-26", allow_draft=allow_draft)
    view = root.for_year("2026-27")
    with pytest.raises(FigureError) as error:
        view.get("demo.amount")
    assert error.value.code == code
    assert root.report() == view.report() == []
    assert root.draft is view.draft is False


def test_path_like_year_is_rejected_before_file_access(rates_dir, monkeypatch):
    def unexpected_read(*args, **kwargs):
        pytest.fail("invalid income year reached file reading")

    monkeypatch.setattr(type(rates_dir), "read_text", unexpected_read)
    with pytest.raises(FigureError, match="income year must look like"):
        Figures("../2025-26")
