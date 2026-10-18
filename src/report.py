"""สร้างรายงานยอดขายรายเดือน reports/monthly_report.md

วิธีใช้:  python -m src.report 2026-03

ทุกตัวเลขคำนวณผ่านฟังก์ชันใน src/metrics.py เท่านั้น
"""
import re
import sys
from pathlib import Path

from src import metrics as m

REPORTS = Path(__file__).resolve().parent.parent / "reports"
TH_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
             "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def previous_month(month: str) -> str:
    """'2026-03' → '2026-02' และ '2026-01' → '2025-12'"""
    year, mon = int(month[:4]), int(month[5:7])
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def thai_month(month: str) -> str:
    """'2026-03' → 'มีนาคม 2569'"""
    return f"{TH_MONTHS[int(month[5:7]) - 1]} {int(month[:4]) + 543}"


def build_report(df, month: str) -> dict:
    """ตัวเลขของรายงานเดือนที่ระบุ"""
    current = m.orders_in_month(df, month)
    if current.empty:
        raise ValueError(f"ไม่มีข้อมูลเดือน {month}")
    prev_month = previous_month(month)
    previous = m.orders_in_month(df, prev_month)
    net = m.net_sales(current)
    prev_net = m.net_sales(previous) if not previous.empty else None
    return {
        "month": month,
        "rows": len(current),
        "net_sales": net,
        "prev_month": prev_month,
        "prev_net_sales": prev_net,
        "change_pct": (net - prev_net) / prev_net * 100 if prev_net else None,
        "top_products": m.top_products(current, 5),
        "cancel_rate": m.cancel_rate(current),
        "return_rate": m.return_rate(current),
    }


def render_markdown(r: dict) -> str:
    """แปลงตัวเลขเป็นรายงาน Markdown ภาษาไทย"""
    if r["prev_net_sales"] is None:
        compare = f"ไม่มีข้อมูลเดือนก่อน ({r['prev_month']})"
    else:
        arrow = "เพิ่มขึ้น" if r["change_pct"] >= 0 else "ลดลง"
        compare = (f"{arrow} {abs(r['change_pct']):.1f}% จาก {thai_month(r['prev_month'])} "
                   f"(฿{r['prev_net_sales']:,.0f})")
    lines = [
        f"# รายงานยอดขายประจำเดือน{thai_month(r['month'])}",
        "",
        f"บ้านสบาย ช็อป · เดือน {r['month']} · คำสั่งซื้อทั้งหมด {r['rows']:,} รายการ",
        "",
        "## ตัวชี้วัดหลัก",
        "",
        "| ตัวชี้วัด | ค่า |",
        "|---|---|",
        f"| ยอดขายสุทธิ | ฿{r['net_sales']:,.0f} |",
        f"| เทียบเดือนก่อน | {compare} |",
        f"| อัตรายกเลิก | {r['cancel_rate']:.2f}% |",
        f"| อัตราคืนสินค้า | {r['return_rate']:.2f}% |",
        "",
        "## 5 สินค้าขายดี",
        "",
        "| อันดับ | สินค้า | ยอดขายสุทธิ |",
        "|---|---|---|",
    ]
    for rank, (name, net) in enumerate(r["top_products"].items(), start=1):
        lines.append(f"| {rank} | {name} | ฿{net:,.0f} |")
    lines += [
        "",
        "---",
        "ยอดขายสุทธิ = qty × unit_price × (1 − discount_pct/100) เฉพาะสถานะ \"จัดส่งสำเร็จ\" ไม่รวมค่าส่ง · "
        "อัตรายกเลิก/คืน = จำนวนแถวสถานะนั้น ÷ คำสั่งซื้อทั้งหมดของเดือน × 100",
        "",
    ]
    return "\n".join(lines)


def write_report(month: str, out_dir: Path = REPORTS, df=None) -> Path:
    """สร้างไฟล์ monthly_report.md ของเดือนที่ระบุ แล้วคืน path ของไฟล์"""
    df = m.load_orders() if df is None else df
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "monthly_report.md"
    path.write_text(render_markdown(build_report(df, month)), encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not re.fullmatch(r"\d{4}-\d{2}", argv[0]):
        print("วิธีใช้: python -m src.report YYYY-MM  เช่น python -m src.report 2026-03", file=sys.stderr)
        return 2
    try:
        path = write_report(argv[0])
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"สร้างรายงานแล้ว: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
