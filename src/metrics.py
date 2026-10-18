"""ฟังก์ชันคำนวณตัวชี้วัดของบ้านสบาย ช็อป

ทุกฟังก์ชันรับ DataFrame ที่ได้จาก load_orders() เป็นพารามิเตอร์แรก
นิยามตัวชี้วัดอยู่ใน CLAUDE.md

หลักการเลือกแถว:
- ตัวชี้วัดด้านยอดขาย (net, gp, AOV, รายเดือน, ช่องทาง, จังหวัด) ใช้เฉพาะ status == "จัดส่งสำเร็จ"
  คอลัมน์ net และ gp ของแถวสถานะอื่นจึงเป็น 0
- อัตรายกเลิก / อัตราคืน ใช้ทุกแถวในกลุ่มเป็นตัวหาร
- ระยะส่งและคะแนนรีวิว ใช้ทุกแถวที่มีค่า (ตัดค่าว่างออก) ไม่กรองสถานะ
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

DELIVERED = "จัดส่งสำเร็จ"
CANCELLED = "ยกเลิก"
RETURNED = "คืนสินค้า"
SHIP_BUCKETS = [("1-2", 1, 2), ("3-4", 3, 4), ("5-6", 5, 6), ("7+", 7, None)]


def load_orders(path: Path | str = DATA / "orders.csv") -> pd.DataFrame:
    """อ่าน orders.csv แล้วเพิ่มคอลัมน์ที่ใช้บ่อย: net, unit_cost, gp, month, date"""
    orders = pd.read_csv(path, encoding="utf-8-sig")
    products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig")[["product_id", "unit_cost"]]
    # validate="many_to_one" กันจำนวนแถวเพิ่มถ้า product_id ใน products.csv ซ้ำ
    df = orders.merge(products, on="product_id", how="left", validate="many_to_one")

    delivered = df["status"] == DELIVERED
    gross = df["qty"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    df["net"] = gross.where(delivered, 0.0)
    df["gp"] = (gross - df["qty"] * df["unit_cost"]).where(delivered, 0.0)
    df["month"] = df["order_datetime"].astype(str).str[:7]
    df["date"] = df["order_datetime"].astype(str).str[:10]
    return df


def _delivered(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == DELIVERED]


def _between(series: pd.Series, start: str | None, end: str | None) -> pd.Series:
    """ตัวกรองช่วงแบบรวมปลายทั้งสองข้าง เทียบเป็นสตริง (YYYY-MM หรือ YYYY-MM-DD)"""
    mask = pd.Series(True, index=series.index)
    if start is not None:
        mask &= series >= start
    if end is not None:
        mask &= series <= end
    return mask


def _status_rate(df: pd.DataFrame, status: str) -> float:
    """จำนวนแถวสถานะนั้น ÷ จำนวนแถวทั้งหมดใน df × 100"""
    if len(df) == 0:
        return float("nan")
    return float((df["status"] == status).sum() / len(df) * 100)


def net_sales(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิรวม (บาท)"""
    return float(_delivered(df)["net"].sum())


def gross_profit(df: pd.DataFrame) -> float:
    """กำไรขั้นต้นรวม (บาท)"""
    return float(_delivered(df)["gp"].sum())


def aov(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิเฉลี่ยต่อคำสั่งซื้อที่จัดส่งสำเร็จ (บาท)"""
    delivered = _delivered(df)
    orders = delivered["order_id"].nunique()
    return float(delivered["net"].sum() / orders) if orders else float("nan")


def cancel_rate(df: pd.DataFrame) -> float:
    """อัตรายกเลิกของคำสั่งซื้อทั้งหมดใน df (เปอร์เซ็นต์ 0–100)"""
    return _status_rate(df, CANCELLED)


def monthly_sales(df: pd.DataFrame) -> pd.Series:
    """ยอดขายสุทธิรายเดือน index = 'YYYY-MM' เรียงตามเวลา"""
    return _delivered(df).groupby("month")["net"].sum().sort_index()


def best_month(df: pd.DataFrame) -> str:
    """เดือนที่ยอดขายสุทธิสูงสุด ('YYYY-MM')"""
    return str(monthly_sales(df).idxmax())


def channel_share(df: pd.DataFrame, channel: str, start_month: str, end_month: str) -> float:
    """สัดส่วนยอดขายสุทธิของช่องทางในช่วงเดือน start_month..end_month (รวมทั้งสองเดือน) เป็นเปอร์เซ็นต์"""
    delivered = _delivered(df)
    period = delivered[_between(delivered["month"], start_month, end_month)]
    total = period["net"].sum()
    if total == 0:
        return float("nan")
    return float(period.loc[period["channel"] == channel, "net"].sum() / total * 100)


def rating_by_ship_bucket(df: pd.DataFrame) -> dict[str, float]:
    """คะแนนรีวิวเฉลี่ยตามระยะส่ง คืน dict คีย์ '1-2', '3-4', '5-6', '7+'"""
    rated = df.dropna(subset=["ship_days", "rating"])
    result = {}
    for label, low, high in SHIP_BUCKETS:
        in_bucket = rated["ship_days"] >= low
        if high is not None:
            in_bucket &= rated["ship_days"] <= high
        result[label] = float(rated.loc[in_bucket, "rating"].mean())
    return result


def top_products(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """สินค้าขายดี n อันดับแรกตามยอดขายสุทธิ index = product_name เรียงจากมากไปน้อย"""
    return _delivered(df).groupby("product_name")["net"].sum().sort_values(ascending=False).head(n)


def top_province(df: pd.DataFrame, region: str) -> str:
    """จังหวัดที่มียอดขายสุทธิสูงสุดในภูมิภาคที่ระบุ"""
    delivered = _delivered(df)
    by_province = delivered[delivered["region"] == region].groupby("province")["net"].sum()
    return str(by_province.idxmax())


def avg_ship_days(df: pd.DataFrame, region: str | None = None, carrier: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> float:
    """ระยะส่งเฉลี่ย (วัน) ตามตัวกรองที่ให้มา วันที่เป็น 'YYYY-MM-DD' และรวมทั้งสองวัน"""
    mask = _between(df["date"], start_date, end_date)
    if region is not None:
        mask &= df["region"] == region
    if carrier is not None:
        mask &= df["carrier"] == carrier
    return float(df.loc[mask, "ship_days"].dropna().mean())


def orders_in_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """แถวทั้งหมดของเดือนที่ระบุ ('YYYY-MM') ทุกสถานะ"""
    return df[df["month"] == month]


def return_rate(df: pd.DataFrame, product_id: str | None = None,
                start_date: str | None = None, end_date: str | None = None) -> float:
    """อัตราคืนสินค้า (เปอร์เซ็นต์) ของสินค้าและช่วงวันที่ที่ระบุ"""
    mask = _between(df["date"], start_date, end_date)
    if product_id is not None:
        mask &= df["product_id"] == product_id
    return _status_rate(df[mask], RETURNED)
