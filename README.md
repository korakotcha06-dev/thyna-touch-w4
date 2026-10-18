# บ้านสบาย ช็อป · โปรเจกต์วิเคราะห์ยอดขาย

งานเวิร์กช็อป "AI Model, LLM และ Vibe Coding สำหรับงานวิเคราะห์ข้อมูล" (ADT-RAISE) ร้านค้าออนไลน์สมมติ ข้อมูลปีงบ 1 ต.ค. 2025 – 30 ก.ย. 2026 ข้อมูลส่วนบุคคลทั้งหมดเป็นของปลอม

**เปิดแดชบอร์ด:** [https://claude.ai/artifact/X7AcjLQVgjWYd8EmnNJqzw?sk=OvtGPsxxKY2bBVHaP5nTLQ](https://claude.ai/artifact/X7AcjLQVgjWYd8EmnNJqzw?sk=OvtGPsxxKY2bBVHaP5nTLQ) (ปุ่มบทสรุปผู้บริหารและดาวน์โหลด PDF ใช้ได้เมื่อเปิดผ่านลิงก์นี้)

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `dashboard/` | แดชบอร์ด React (คาบ 3 · W3-A/W3-B) อัปโหลด `orders.csv` แล้วดู KPI กราฟ แผนที่ วันเมกะเซล และบทสรุปผู้บริหาร |
| `src/metrics.py` | ฟังก์ชันตัวชี้วัดตามนิยามใน `CLAUDE.md` (คาบ 4) |
| `src/report.py` | สร้างรายงานรายเดือน `python -m src.report 2026-03` → `reports/monthly_report.md` (คาบ 4 · W4-B) |
| `tests/` | `test_metrics.py` (สัญญาของโปรเจกต์) และ `test_report.py` |
| `data/` | ชุดข้อมูลของคาบ (UTF-8 มี BOM) |
| `prompts/` | prompt จัดหมวดตั๋วลูกค้า สำหรับคาบ 5 |

## รัน test

```bash
pip install -r requirements.txt
pytest -q
```
