# -*- coding: utf-8 -*-
"""Thu thập & chuẩn hóa dữ liệu cho AI Advisor — tránh AI bịa số liệu."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database.db_manager import DatabaseManager

PRODUCT_ALIASES = {
    "coffee": ["Cà phê", "cà phê", "Ca phe"],
    "pepper": ["Hồ tiêu", "hồ tiêu", "Ho tieu"],
}


def _price_trend(rows: List[Dict]) -> Dict[str, Any]:
    """Tính xu hướng từ danh sách giá (mới → cũ)."""
    if not rows:
        return {"co_du_lieu": False}
    prices = [r.get("price_local") or 0 for r in rows if (r.get("price_local") or 0) > 0]
    if not prices:
        return {"co_du_lieu": False}

    latest = prices[0]
    oldest = prices[-1] if len(prices) > 1 else latest
    change_pct = ((latest - oldest) / oldest * 100) if oldest else 0
    if change_pct > 0.5:
        trend = "tăng"
    elif change_pct < -0.5:
        trend = "giảm"
    else:
        trend = "ổn định"

    history = []
    for r in reversed(rows[:7]):
        history.append({
            "ngay": str(r.get("log_date", ""))[:10],
            "gia_vnd_kg": r.get("price_local"),
        })

    return {
        "co_du_lieu": True,
        "gia_hom_nay_vnd_kg": latest,
        "gia_7_ngay_truoc_vnd_kg": oldest,
        "bien_dong_pct": round(change_pct, 2),
        "xu_huong": trend,
        "lich_su_7_ngay": history,
        "so_mau": len(prices),
    }


def build_advisor_context(db: DatabaseManager, user_id: str) -> Dict[str, Any]:
    """Dữ liệu có cấu trúc + cờ chất lượng để AI trả lời đáng tin."""
    ctx: Dict[str, Any] = {
        "nguon": "GASH — Supabase (tồn kho, giao dịch, giá thị trường)",
        "thoi_diem": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "ton_kho": [],
        "gia_thi_truong": {},
        "giao_dich_30_ngay": {},
        "cong_no": {},
        "chat_luong_du_lieu": {},
    }

    # —— Tồn kho (kg) ——
    try:
        for inv in db.get_inventory(user_id):
            name = inv.get("products", {}).get("name", "Không rõ")
            stock = float(inv.get("current_stock") or 0)
            ctx["ton_kho"].append({
                "san_pham": name,
                "ton_kg": round(stock, 2),
                "don_vi": "kg",
            })
    except Exception:
        pass

    # —— Giá thị trường ——
    for key, aliases in PRODUCT_ALIASES.items():
        rows = db.get_market_prices_any(aliases, days=7)
        label = "Cà phê" if key == "coffee" else "Hồ tiêu"
        ctx["gia_thi_truong"][label] = _price_trend(rows)

    # —— Giao dịch 30 ngày ——
    try:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        txs = db.get_transactions(user_id, start_date=start)
        by_product: Dict[str, Dict[str, float]] = {}
        total_kg = 0.0
        total_vnd = 0.0
        for t in txs:
            pname = t.get("products", {}).get("name", "Khác")
            kg = float(t.get("net_weight") or 0)
            vnd = float(t.get("total_amount") or 0)
            total_kg += kg
            total_vnd += vnd
            if pname not in by_product:
                by_product[pname] = {"so_giao_dich": 0, "tong_kg": 0.0, "tong_vnd": 0.0}
            by_product[pname]["so_giao_dich"] += 1
            by_product[pname]["tong_kg"] += kg
            by_product[pname]["tong_vnd"] += vnd

        ctx["giao_dich_30_ngay"] = {
            "so_giao_dich": len(txs),
            "tong_kg_mua": round(total_kg, 2),
            "tong_tien_vnd": round(total_vnd, 0),
            "theo_san_pham": {
                k: {
                    "so_giao_dich": int(v["so_giao_dich"]),
                    "tong_kg": round(v["tong_kg"], 2),
                    "tong_vnd": round(v["tong_vnd"], 0),
                }
                for k, v in by_product.items()
            },
        }
    except Exception:
        ctx["giao_dich_30_ngay"] = {"so_giao_dich": 0}

    # —— Công nợ ——
    try:
        farmers = db.get_farmers(user_id)
        total_debt = sum(float(f.get("total_debt") or 0) for f in farmers)
        ctx["cong_no"] = {
            "tong_vnd": round(total_debt, 0),
            "so_ho_no": sum(1 for f in farmers if (f.get("total_debt") or 0) > 0),
        }
    except Exception:
        pass

    coffee = ctx["gia_thi_truong"].get("Cà phê", {})
    pepper = ctx["gia_thi_truong"].get("Hồ tiêu", {})
    ctx["chat_luong_du_lieu"] = {
        "co_gia_ca_phe": coffee.get("co_du_lieu", False),
        "co_gia_tieu": pepper.get("co_du_lieu", False),
        "co_ton_kho": len(ctx["ton_kho"]) > 0,
        "co_giao_dich": (ctx["giao_dich_30_ngay"].get("so_giao_dich") or 0) > 0,
    }

    return ctx


def format_context_for_display(ctx: Dict[str, Any]) -> str:
    """Một dòng tóm tắt nguồn dữ liệu hiển thị dưới câu trả lời AI."""
    q = ctx.get("chat_luong_du_lieu", {})
    parts = []
    if q.get("co_gia_ca_phe"):
        g = ctx["gia_thi_truong"]["Cà phê"].get("gia_hom_nay_vnd_kg")
        parts.append(f"giá cà phê {g:,.0f} đ/kg" if g else "giá cà phê")
    if q.get("co_ton_kho"):
        parts.append("tồn kho")
    if q.get("co_giao_dich"):
        n = ctx["giao_dich_30_ngay"].get("so_giao_dich", 0)
        parts.append(f"{n} giao dịch/30 ngày")
    if not parts:
        return "⚠️ Thiếu dữ liệu giá thị trường — câu trả lời chỉ mang tính tham khảo"
    return "📊 Dữ liệu: " + ", ".join(parts) + f" · {ctx.get('thoi_diem', '')}"
