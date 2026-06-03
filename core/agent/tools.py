# -*- coding: utf-8 -*-
"""
Bộ công cụ (Tools) cho Agentic AI — mỗi tool truy vấn dữ liệu thật từ Supabase.
Agent tự chọn tool phù hợp thay vì đoán số liệu.
"""
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from database.db_manager import DatabaseManager
from core.advisor_context import PRODUCT_ALIASES, _price_trend

# Import WebMarketResearcher cho web research tool
try:
    from core.web_researcher import WebMarketResearcher
except ImportError:
    WebMarketResearcher = None

StepCallback = Optional[Callable[[Dict[str, Any]], None]]


class AgriAgentToolkit:
    """Cung cấp callable cho Gemini Function Calling + thực thi theo tên."""

    def __init__(
        self,
        db: DatabaseManager,
        user_id: str,
        on_step: StepCallback = None,
    ):
        self.db = db
        self.user_id = user_id
        self.on_step = on_step

    def _emit(self, tool: str, args: dict, summary: str, data: Any = None):
        if self.on_step:
            self.on_step({
                "type": "tool",
                "tool": tool,
                "args": args,
                "summary": summary,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "preview": str(data)[:300] if data is not None else "",
            })

    # ——————————————————————————————————————————
    # TOOL 1: Tồn kho
    # ——————————————————————————————————————————
    def get_inventory_summary(self) -> dict:
        """
        Lấy tổng quan tồn kho hiện tại của đại lý (kg theo từng sản phẩm).

        Returns:
            dict: ton_kho (list), tong_kg, so_san_pham
        """
        items = []
        total_kg = 0.0
        for inv in self.db.get_inventory(self.user_id):
            name = inv.get("products", {}).get("name", "Không rõ")
            kg = float(inv.get("current_stock") or 0)
            total_kg += kg
            items.append({"san_pham": name, "ton_kg": round(kg, 2)})
        result = {
            "ton_kho": items,
            "tong_kg": round(total_kg, 2),
            "so_san_pham": len(items),
            "don_vi": "kg",
        }
        self._emit("get_inventory_summary", {}, f"{len(items)} sản phẩm, {total_kg:,.0f} kg", result)
        return result

    # ——————————————————————————————————————————
    # TOOL 2: Giá thị trường & xu hướng
    # ——————————————————————————————————————————
    def get_market_price_trend(self, product_name: str = "Cà phê", days: int = 7) -> dict:
        """
        Lấy lịch sử giá và xu hướng thị trường cho một sản phẩm.
        Hỗ trợ: Cà phê, Hồ tiêu, Sầu riêng, Lúa gạo, Cao su, Điều nhân, Cacao, Mắc ca.

        Args:
            product_name: Tên sản phẩm.
            days: Số ngày lịch sử giá (mặc định 7).

        Returns:
            dict: gia_hom_nay, xu_huong, bien_dong_pct, lich_su
        """
        # Map tên sản phẩm → key trong PRODUCT_ALIASES
        product_key_map = {
            "cà phê": "coffee", "ca phe": "coffee", "coffee": "coffee",
            "hồ tiêu": "pepper", "ho tieu": "pepper", "tiêu": "pepper", "tieu": "pepper", "pepper": "pepper",
            "sầu riêng": "durian", "sau rieng": "durian", "durian": "durian",
            "lúa gạo": "rice", "lua gao": "rice", "gạo": "rice", "gao": "rice",
            "cao su": "caosu", "caosu": "caosu", "rubber": "caosu",
            "điều nhân": "dieunhan", "dieu nhan": "dieunhan", "dieunhan": "dieunhan", "cashew": "dieunhan",
            "cacao": "cacao", "ca cao": "cacao", "cocoa": "cacao",
            "mắc ca": "macca", "mac ca": "macca", "macca": "macca", "macadamia": "macca",
        }
        p_lower = product_name.lower().strip()
        key = "coffee"  # default
        # Sắp xếp keys theo độ dài giảm dần để match chính xác ("hồ tiêu" trước "tiêu")
        sorted_keys = sorted(product_key_map.items(), key=lambda x: -len(x[0]))
        for k, v in sorted_keys:
            if k in p_lower:
                key = v
                break
        aliases = PRODUCT_ALIASES.get(key, [product_name, product_name.lower()])
        rows = self.db.get_market_prices_any(aliases, days=max(days, 2))
        trend = _price_trend(rows)
        trend["san_pham"] = product_name
        trend["don_vi_gia"] = "VNĐ/kg"
        self._emit(
            "get_market_price_trend",
            {"product_name": product_name, "days": days},
            f"xu hướng: {trend.get('xu_huong', 'N/A')}",
            trend,
        )
        return trend

    # ——————————————————————————————————————————
    # TOOL 3: Giao dịch
    # ——————————————————————————————————————————
    def get_transaction_summary(self, days: int = 30) -> dict:
        """
        Thống kê giao dịch thu mua trong N ngày gần đây.

        Args:
            days: Số ngày thống kê (mặc định 30).

        Returns:
            dict: so_giao_dich, tong_kg, tong_vnd, theo_san_pham
        """
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        txs = self.db.get_transactions(self.user_id, start_date=start)
        by_product: Dict[str, Dict] = {}
        total_kg = total_vnd = 0.0
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

        result = {
            "trong_vong_days": days,
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
        self._emit(
            "get_transaction_summary", {"days": days},
            f"{len(txs)} GD, {total_vnd:,.0f} VNĐ", result,
        )
        return result

    # ——————————————————————————————————————————
    # TOOL 4: Công nợ
    # ——————————————————————————————————————————
    def get_debt_summary(self, top_n: int = 5) -> dict:
        """
        Tổng hợp công nợ nông dân và danh sách hộ nợ cao nhất.

        Args:
            top_n: Số hộ nợ lớn cần liệt kê (mặc định 5).

        Returns:
            dict: tong_cong_no_vnd, so_ho_no, top_no
        """
        farmers = self.db.get_farmers(self.user_id)
        with_debt = [
            {
                "ten": f.get("name", "N/A"),
                "phone": f.get("phone", ""),
                "cong_no_vnd": round(float(f.get("total_debt") or 0), 0),
            }
            for f in farmers
            if (f.get("total_debt") or 0) > 0
        ]
        with_debt.sort(key=lambda x: x["cong_no_vnd"], reverse=True)
        total = sum(x["cong_no_vnd"] for x in with_debt)
        result = {
            "tong_cong_no_vnd": total,
            "so_ho_no": len(with_debt),
            "top_no": with_debt[:top_n],
        }
        self._emit("get_debt_summary", {"top_n": top_n}, f"{total:,.0f} VNĐ, {len(with_debt)} hộ", result)
        return result

    # ——————————————————————————————————————————
    # TOOL 5: Dashboard tổng quan
    # ——————————————————————————————————————————
    def get_dashboard_overview(self) -> dict:
        """
        Lấy chỉ số tổng quan: nông dân, giao dịch, tồn kho, giá trị.

        Returns:
            dict: các KPI tổng hợp từ hệ thống GASH
        """
        stats = self.db.get_dashboard_stats(self.user_id)
        farmers = self.db.get_farmers(self.user_id)
        total_debt = sum(float(f.get("total_debt") or 0) for f in farmers)
        result = {
            "tong_nong_dan": stats.get("total_farmers", 0),
            "tong_giao_dich": stats.get("total_transactions", 0),
            "tong_ton_kho_kg": round(stats.get("total_stock", 0) or 0, 2),
            "tong_gia_tri_giao_dich_vnd": round(stats.get("total_value", 0) or 0, 0),
            "tong_cong_no_vnd": round(total_debt, 0),
        }
        self._emit("get_dashboard_overview", {}, "KPI đại lý", result)
        return result

    # ——————————————————————————————————————————
    # TOOL 6: Giao dịch gần đây (chi tiết)
    # ——————————————————————————————————————————
    def get_recent_transactions(self, limit: int = 10) -> dict:
        """
        Liệt kê các giao dịch thu mua gần nhất.

        Args:
            limit: Số giao dịch tối đa (mặc định 10).

        Returns:
            dict: danh_sach giao dịch với nông dân, sản phẩm, kg, VNĐ
        """
        txs = self.db.get_transactions(self.user_id)[:limit]
        rows = []
        for t in txs:
            rows.append({
                "ngay": str(t.get("created_at", ""))[:10],
                "nong_dan": t.get("farmers", {}).get("name", "N/A"),
                "san_pham": t.get("products", {}).get("name", "N/A"),
                "can_tinh_kg": round(float(t.get("net_weight") or 0), 2),
                "thanh_tien_vnd": round(float(t.get("total_amount") or 0), 0),
                "thanh_toan": t.get("payment_status", ""),
            })
        result = {"so_luong": len(rows), "giao_dich": rows}
        self._emit("get_recent_transactions", {"limit": limit}, f"{len(rows)} giao dịch", result)
        return result

    # ——————————————————————————————————————————
    # TOOL 7: Khuyến nghị mua/bán (logic nghiệp vụ)
    # ——————————————————————————————————————————
    def recommend_buy_sell_strategy(self, product_name: str = "Cà phê") -> dict:
        """
        Đưa ra khuyến nghị GIỮ / BÁN / MUA thêm dựa trên tồn kho và xu hướng giá thực tế.

        Args:
            product_name: Sản phẩm cần tư vấn ('Cà phê' hoặc 'Hồ tiêu').

        Returns:
            dict: khuyen_nghi, ly_do, ton_kg, xu_huong_gia, do_tin_cay
        """
        inv = self.get_inventory_summary()
        ton = 0.0
        for item in inv.get("ton_kho", []):
            if product_name.lower() in item.get("san_pham", "").lower():
                ton = item.get("ton_kg", 0)
                break

        trend = self.get_market_price_trend(product_name=product_name, days=7)
        xu_huong = trend.get("xu_huong", "không rõ")
        co_gia = trend.get("co_du_lieu", False)

        LOW_STOCK = 100
        HIGH_STOCK = 5000

        if not co_gia:
            khuyen_nghi = "THẬN TRỌNG"
            ly_do = "Thiếu dữ liệu giá thị trường — chỉ căn cứ tồn kho."
            do_tin_cay = "Thấp"
        elif ton >= HIGH_STOCK and xu_huong in ("tăng", "ổn định"):
            khuyen_nghi = "BÁN BỚT"
            ly_do = f"Tồn cao ({ton:,.0f} kg) trong khi giá {xu_huong} — giải phóng vốn."
            do_tin_cay = "Cao"
        elif ton >= HIGH_STOCK and xu_huong == "giảm":
            khuyen_nghi = "BÁN SỚM"
            ly_do = f"Tồn cao + giá giảm — hạn chế tổn thất thêm."
            do_tin_cay = "Cao"
        elif ton <= LOW_STOCK and xu_huong in ("tăng", "ổn định"):
            khuyen_nghi = "MUA / GIỮ"
            ly_do = f"Tồn thấp ({ton:,.0f} kg), giá {xu_huong} — tích lũy hàng."
            do_tin_cay = "Trung bình"
        elif ton <= LOW_STOCK:
            khuyen_nghi = "GIỮ / CHỜ"
            ly_do = f"Tồn thấp, chờ giá phục hồi trước khi bán."
            do_tin_cay = "Trung bình"
        else:
            khuyen_nghi = "GIỮ"
            ly_do = f"Tồn mức trung bình ({ton:,.0f} kg), theo dõi giá tuần tới."
            do_tin_cay = "Trung bình"

        result = {
            "san_pham": product_name,
            "khuyen_nghi": khuyen_nghi,
            "ly_do": ly_do,
            "ton_kg": ton,
            "xu_huong_gia_7_ngay": xu_huong,
            "bien_dong_pct": trend.get("bien_dong_pct"),
            "gia_hom_nay_vnd_kg": trend.get("gia_hom_nay_vnd_kg"),
            "do_tin_cay": do_tin_cay,
        }
        self._emit("recommend_buy_sell_strategy", {"product_name": product_name}, khuyen_nghi, result)
        return result

    # ——————————————————————————————————————————
    # TOOL 8: Tìm nông dân
    # ——————————————————————————————————————————
    def search_farmers(self, keyword: str = "") -> dict:
        """
        Tìm nông dân theo tên hoặc số điện thoại.

        Args:
            keyword: Chuỗi tìm kiếm (để trống = tất cả).

        Returns:
            dict: danh_sach nông dân kèm công nợ
        """
        farmers = self.db.get_farmers(self.user_id)
        kw = keyword.strip().lower()
        matched = []
        for f in farmers:
            name = f.get("name", "")
            phone = str(f.get("phone", ""))
            if not kw or kw in name.lower() or kw in phone:
                matched.append({
                    "ten": name,
                    "phone": phone,
                    "cong_no_vnd": round(float(f.get("total_debt") or 0), 0),
                })
        result = {"keyword": keyword, "so_luong": len(matched), "nong_dan": matched[:20]}
        self._emit("search_farmers", {"keyword": keyword}, f"{len(matched)} nông dân", result)
        return result

    # ——————————————————————————————————————————
    # TOOL 9: Nghiên cứu thị trường từ web (có dẫn chứng)
    # ——————————————————————————————————————————
    def research_market_news(self, product: str = "cà phê") -> dict:
        """
        [WEB RESEARCH] Tự động tìm kiếm và phân tích dữ liệu thị trường THẬT từ web.
        Hỗ trợ: Cà phê, Hồ tiêu, Sầu riêng, Lúa gạo, Cao su, Điều nhân, Cacao, Mắc ca.
        Trả về giá cả, tin tức, xu hướng KÈM NGUỒN (URL) để trích dẫn.
        KHÔNG dùng dữ liệu mẫu — chỉ dùng dữ liệu thực tế từ các trang chuyên gia.

        Args:
            product: Sản phẩm cần nghiên cứu.

        Returns:
            dict: {
                product_name, sources (list of {price, source_url, source_name, fetched_at}),
                citation_text, news
            }
        """
        result = {
            "product_name": product,
            "sources": [],
            "citation_text": "",
            "news": [],
            "error": None,
        }

        if WebMarketResearcher is None:
            result["error"] = "WebMarketResearcher chưa được cài đặt"
            return result

        # Map sản phẩm → phương thức research
        product_research_map = [
            (["cà phê", "coffee", "ca phe"], lambda r: r.research_coffee()),
            (["hồ tiêu", "ho tieu", "tiêu", "tieu", "pepper"], lambda r: r.research_pepper()),
            (["sầu riêng", "sau rieng", "durian"], lambda r: r.research_durian()),
            (["lúa gạo", "lua gao", "gạo", "gao", "rice"], lambda r: r.research_rice()),
            (["cao su", "caosu", "rubber"], lambda r: r.research_caosu()),
            (["điều nhân", "dieu nhan", "dieunhan", "cashew"], lambda r: r.research_dieunhan()),
            (["cacao", "ca cao", "cocoa"], lambda r: r.research_cacao()),
            (["mắc ca", "mac ca", "macca", "macadamia"], lambda r: r.research_macca()),
        ]

        try:
            researcher = WebMarketResearcher()
            p_lower = product.lower().strip()

            matched = False
            for keywords, research_fn in product_research_map:
                if any(kw in p_lower for kw in keywords):
                    research = research_fn(researcher)
                    result["sources"] = [s.to_dict() for s in research.sources]
                    result["citation_text"] = research.citation_text()
                    result["error"] = research.error
                    result["news"] = researcher.get_market_news(product)
                    matched = True
                    break

            if not matched:
                # Không xác định được sản phẩm → nghiên cứu tất cả
                results_list = [
                    researcher.research_coffee(),
                    researcher.research_pepper(),
                    researcher.research_durian(),
                    researcher.research_rice(),
                    researcher.research_caosu(),
                    researcher.research_dieunhan(),
                    researcher.research_cacao(),
                    researcher.research_macca(),
                ]
                all_sources = []
                all_citations = []
                for r in results_list:
                    all_sources.extend([s.to_dict() for s in r.sources])
                    ct = r.citation_text()
                    if ct and "⚠️" not in ct:
                        all_citations.append(ct)
                result["sources"] = all_sources
                result["citation_text"] = "\n".join(all_citations) if all_citations else "⚠️ Không có dữ liệu giá thị trường"
                result["news"] = researcher.get_market_news("cà phê") + researcher.get_market_news("hồ tiêu")
                result["error"] = None if all_sources else "Không tìm được dữ liệu giá cho bất kỳ sản phẩm nào"

            summary = f"{len(result['sources'])} nguồn"
            if result.get("sources") and len(result["sources"]) > 0:
                first_price = result["sources"][0].get("price", 0)
                if first_price:
                    summary += f", giá: {first_price:,.0f} VNĐ/kg"

            self._emit(
                "research_market_news", {"product": product},
                summary, result,
            )
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"research_market_news error: {e}")

        return result

    # ——————————————————————————————————————————
    # TOOL 10: Báo cáo thị trường đầy đủ (có citations)
    # ——————————————————————————————————————————
    def get_full_market_report(self) -> dict:
        """
        [WEB RESEARCH] Tạo báo cáo thị trường đầy đủ với dẫn chứng nguồn.
        Tự động tìm kiếm trên web, tổng hợp từ nhiều nguồn chuyên gia,
        trả về dữ liệu kèm URL cụ thể để kiểm chứng.

        Returns:
            dict: {
                coffee: ResearchResult dict,
                pepper: ResearchResult dict,
                report_summary: str (tóm tắt báo cáo)
            }
        """
        result = {
            "coffee": None,
            "pepper": None,
            "report_summary": "",
            "error": None,
        }

        if WebMarketResearcher is None:
            result["error"] = "WebMarketResearcher chưa được cài đặt"
            return result

        try:
            researcher = WebMarketResearcher()
            coffee = researcher.research_coffee()
            pepper = researcher.research_pepper()

            result["coffee"] = coffee.to_dict()
            result["pepper"] = pepper.to_dict()
            result["report_summary"] = f"""📊 BÁO CÁO THỊ TRƯỜNG HÔM NAY
{'=' * 60}

☕ CÀ PHÊ:
{coffee.citation_text()}

🌶️ HỒ TIÊU:
{pepper.citation_text()}

📋 CHI TIẾT NGUỒN:
{coffee.detailed_citations()}
{pepper.detailed_citations()}"""

            self._emit(
                "get_full_market_report", {},
                f"cà phê: {len(coffee.sources)} nguồn, tiêu: {len(pepper.sources)} nguồn",
                result,
            )
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"get_full_market_report error: {e}")

        return result

    def get_callables(self) -> List[Callable]:
        """Danh sách hàm cho Gemini automatic function calling."""
        return [
            self.get_inventory_summary,
            self.get_market_price_trend,
            self.get_transaction_summary,
            self.get_debt_summary,
            self.get_dashboard_overview,
            self.get_recent_transactions,
            self.recommend_buy_sell_strategy,
            self.search_farmers,
            self.research_market_news,
            self.get_full_market_report,
        ]

    def execute(self, name: str, args: dict) -> Any:
        """Thực thi tool theo tên (fallback thủ công)."""
        mapping = {
            "get_inventory_summary": lambda: self.get_inventory_summary(),
            "get_market_price_trend": lambda: self.get_market_price_trend(
                **{k: v for k, v in args.items() if k in ("product_name", "days")}
            ),
            "get_transaction_summary": lambda: self.get_transaction_summary(
                days=int(args.get("days", 30))
            ),
            "get_debt_summary": lambda: self.get_debt_summary(
                top_n=int(args.get("top_n", 5))
            ),
            "get_dashboard_overview": lambda: self.get_dashboard_overview(),
            "get_recent_transactions": lambda: self.get_recent_transactions(
                limit=int(args.get("limit", 10))
            ),
            "recommend_buy_sell_strategy": lambda: self.recommend_buy_sell_strategy(
                product_name=args.get("product_name", "Cà phê")
            ),
            "search_farmers": lambda: self.search_farmers(
                keyword=args.get("keyword", "")
            ),
            "research_market_news": lambda: self.research_market_news(
                product=args.get("product", "cà phê")
            ),
            "get_full_market_report": lambda: self.get_full_market_report(),
        }
        fn = mapping.get(name)
        if not fn:
            return {"error": f"Tool không tồn tại: {name}"}
        return fn()
