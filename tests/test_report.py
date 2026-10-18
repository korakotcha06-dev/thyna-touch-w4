"""test ของรายงานรายเดือน (W4-B)"""
import pytest

from src import metrics as m
from src import report


@pytest.fixture(scope="module")
def df():
    return m.load_orders()


def test_report_march_net_sales(df):
    r = report.build_report(df, "2026-03")
    assert r["net_sales"] == pytest.approx(1_147_155, abs=1)


def test_report_markdown_shows_march_net_sales(df, tmp_path):
    path = report.write_report("2026-03", out_dir=tmp_path, df=df)
    text = path.read_text(encoding="utf-8")
    assert path.name == "monthly_report.md"
    assert "มีนาคม 2569" in text
    assert "฿1,147,155" in text
    for rank in range(1, 6):  # ตารางสินค้าขายดีมีอันดับ 1–5
        assert f"\n| {rank} | " in text


def test_report_compares_previous_month(df):
    r = report.build_report(df, "2026-03")
    assert r["prev_month"] == "2026-02"
    assert r["prev_net_sales"] == pytest.approx(m.net_sales(m.orders_in_month(df, "2026-02")))
    assert len(r["top_products"]) == 5


def test_report_first_month_has_no_previous(df):
    r = report.build_report(df, "2025-10")
    assert r["prev_net_sales"] is None
    assert "ไม่มีข้อมูลเดือนก่อน" in report.render_markdown(r)


def test_previous_month_wraps_year():
    assert report.previous_month("2026-01") == "2025-12"


def test_unknown_month_raises(df):
    with pytest.raises(ValueError):
        report.build_report(df, "2030-01")
