# -*- coding: utf-8 -*-
"""
Web Market Researcher — Tự động tìm kiếm dữ liệu thật từ nhiều nguồn web.
Mỗi kết quả đều kèm source_url và thời gian lấy để AI có thể trích dẫn.

Tác giả: GASH System
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ==================== DATA STRUCTURES ====================

@dataclass
class SourceData:
    """Một điểm dữ liệu có nguồn gốc rõ ràng."""
    price: float
    source_url: str
    source_name: str
    fetched_at: str
    product_name: str
    unit: str = "VNĐ/kg"
    notes: str = ""

    def to_dict(self) -> Dict:
        """Chuyển đổi thành dict để JSON serialization."""
        return {
            "price": self.price,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "fetched_at": self.fetched_at,
            "product_name": self.product_name,
            "unit": self.unit,
            "notes": self.notes,
        }


@dataclass
class ResearchResult:
    """Kết quả nghiên cứu thị trường đầy đủ."""
    product_name: str
    sources: List[SourceData] = field(default_factory=list)
    used_fallback: bool = False
    error: Optional[str] = None
    total_sources_tried: int = 0
    successful_sources: int = 0

    def to_dict(self) -> Dict:
        return {
            "product_name": self.product_name,
            "sources": [asdict(s) for s in self.sources],
            "used_fallback": self.used_fallback,
            "error": self.error,
            "total_sources_tried": self.total_sources_tried,
            "successful_sources": self.successful_sources,
        }

    def best_price(self) -> Optional[float]:
        """Giá tốt nhất (từ nguồn đáng tin cậy nhất)."""
        if not self.sources:
            return None
        return self.sources[0].price

    def citation_text(self) -> str:
        """Trích dẫn ngắn gọn cho AI response."""
        if not self.sources:
            return "⚠️ Không tìm được dữ liệu giá thị trường thực tế"
        parts = []
        for s in self.sources:
            parts.append(f"{s.product_name}: {s.price:,.0f} {s.unit} (nguồn: {s.source_name}, {s.fetched_at})")
        return "\n".join(parts)

    def detailed_citations(self) -> str:
        """Trích dẫn đầy đủ cho báo cáo."""
        if not self.sources:
            return "Không có dữ liệu"
        lines = ["📋 DANH SÁCH NGUỒN DỮ LIỆU", "=" * 60]
        for i, s in enumerate(self.sources, 1):
            lines.extend([
                f"\n{i}. {s.source_name}",
                f"   Sản phẩm: {s.product_name}",
                f"   Giá: {s.price:,.0f} {s.unit}",
                f"   URL: {s.source_url}",
                f"   Thời điểm: {s.fetched_at}",
                f"   Ghi chú: {s.notes or 'Dữ liệu được trích xuất tự động'}",
            ])
        return "\n".join(lines)


# ==================== SITEMAP DISCOVERER ====================
# Tự động tìm bài viết mới nhất từ sitemap.xml — không hardcode URL

SITEMAP_SOURCES = {
    "nongdanviet.vn": {
        "sitemap_url": "https://nongdanviet.vn/sitemap.xml",
        "name": "Nông Dân Việt",
        "product_patterns": {
            "Cà phê": ["gia-ca-phe", "ca-phe"],
            "Hồ tiêu": ["gia-ho-tieu", "ho-tieu"],
            "Sầu riêng": ["gia-sau-rieng", "sau-rieng"],
            "Lúa gạo": ["gia-lua-gao", "lua-gao"],
            "Cao su": ["cao-su", "caosu"],
            "Điều nhân": ["dieu-nhan", "điều nhân"],
            "Cacao": ["cacao", "ca-cao"],
            "Mắc ca": ["mac-ca", "mắc ca"],
        },
    },
}


@dataclass
class SitemapEntry:
    """Một URL từ sitemap.xml."""
    url: str
    lastmod: Optional[datetime] = None
    changefreq: str = ""
    priority: float = 0.5


class SitemapDiscoverer:
    """
    Tự động khám phá bài viết mới nhất từ sitemap.xml.
    
    Thay vì hardcode URL, chúng ta:
      1. Fetch sitemap.xml
      2. Parse tất cả URL + lastmod
      3. Lọc theo sản phẩm (cà phê, tiêu, sầu riêng, lúa gạo)
      4. Sắp xếp theo thời gian (mới nhất trước)
      5. Trả về các bài viết mới nhất để trích xuất giá
    """

    def __init__(self, session: requests.Session):
        self.session = session

    def discover_latest_articles(
        self, source_key: str = "nongdanviet.vn",
        product: Optional[str] = None,
        max_results: int = 5
    ) -> List[SitemapEntry]:
        """
        Tìm các bài viết mới nhất từ sitemap.
        
        Args:
            source_key: Tên nguồn trong SITEMAP_SOURCES
            product: Lọc theo sản phẩm (None = tất cả)
            max_results: Số kết quả tối đa
        
        Returns:
            List[SitemapEntry] các URL mới nhất
        """
        source = SITEMAP_SOURCES.get(source_key)
        if not source:
            logger.warning(f"⚠️ Không tìm thấy nguồn sitemap: {source_key}")
            return []

        entries = self._fetch_and_parse(source["sitemap_url"])
        if not entries:
            return []

        # Lọc theo sản phẩm nếu có
        if product and product in source.get("product_patterns", {}):
            patterns = source["product_patterns"][product]
            entries = [
                e for e in entries
                if any(p in e.url.lower() for p in patterns)
            ]

        # Sắp xếp theo lastmod (mới nhất trước)
        entries.sort(key=lambda e: e.lastmod or datetime.min, reverse=True)
        return entries[:max_results]

    def discover_latest_for_all_products(
        self, source_key: str = "nongdanviet.vn",
        max_per_product: int = 3
    ) -> Dict[str, List[SitemapEntry]]:
        """Tìm bài mới nhất cho TẤT CẢ sản phẩm."""
        source = SITEMAP_SOURCES.get(source_key)
        if not source:
            return {}
        result = {}
        for product in source["product_patterns"]:
            result[product] = self.discover_latest_articles(
                source_key, product, max_per_product
            )
        return result

    def _fetch_and_parse(self, sitemap_url: str) -> List[SitemapEntry]:
        """Fetch và parse sitemap.xml."""
        try:
            resp = self.session.get(sitemap_url, timeout=15)
            if resp.status_code != 200:
                return []

            root = ET.fromstring(resp.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            entries = []

            for url_elem in root.findall("sm:url", ns):
                loc = url_elem.findtext("sm:loc", "", ns)
                lastmod_str = url_elem.findtext("sm:lastmod", "", ns)
                if not loc or "/tin-tuc/" not in loc:
                    continue

                lastmod = None
                if lastmod_str:
                    try:
                        ls = lastmod_str.replace("Z", "+00:00")
                        lastmod = datetime.fromisoformat(ls)
                    except:
                        pass
                entries.append(SitemapEntry(url=loc, lastmod=lastmod))

            logger.info(f"✅ Sitemap: {len(entries)} bài viết từ {sitemap_url}")
            return entries
        except Exception as e:
            logger.error(f"❌ Sitemap error: {e}")
            return []

    def _scrape_price_from_article(self, url: str, product: str,
                                     min_val: int, max_val: int) -> Optional[SourceData]:
        """Trích xuất giá từ một bài viết cụ thể."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            # Tìm giá gần "Gia Lai" hoặc "đồng/kg"
            price = None
            for kw in ["Gia Lai", "đồng/kg", "VNĐ/kg"]:
                price = self._extract_price_from_text(soup, page_text, kw, min_val, max_val)
                if price:
                    break

            if price:
                return SourceData(
                    price=price, source_url=url,
                    source_name="nongdanviet.vn",
                    fetched_at=now, product_name=product,
                    notes=f"Giá {product} từ bài báo mới nhất (phát hiện qua sitemap)",
                )
        except Exception as e:
            logger.warning(f"⚠️ Article scrape error ({url}): {e}")
        return None

    def _extract_price_from_text(self, soup, page_text, keyword, min_val, max_val):
        """Trích xuất giá từ text gần keyword."""
        # Trong bảng HTML
        for td in soup.find_all('td'):
            if keyword.lower() in td.get_text(strip=True).lower():
                next_td = td.find_next_sibling('td')
                if next_td:
                    val = self._clean_price_text(next_td.get_text(strip=True))
                    if val and min_val < val < max_val:
                        return float(val)
                parent_tr = td.find_parent('tr')
                if parent_tr:
                    for other_td in parent_tr.find_all('td'):
                        if other_td != td:
                            val = self._clean_price_text(other_td.get_text(strip=True))
                            if val and min_val < val < max_val:
                                return float(val)

        # Trong text gần keyword
        idx = page_text.lower().find(keyword.lower())
        if idx >= 0:
            nearby = page_text[max(0, idx - 30):idx + 150]
            numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
            for n in numbers:
                val = int(n.replace('.', ''))
                if min_val < val < max_val:
                    return float(val)
        return None

    def _clean_price_text(self, text: str) -> Optional[float]:
        if not text:
            return None
        cleaned = re.sub(r'[^\d.,]', '', text)
        cleaned = cleaned.replace(',', '.').strip()
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        try:
            val = float(cleaned)
            return val if val > 0 else None
        except ValueError:
            return None

# ==================== WEB FETCHER ====================

class WebMarketFetcher:
    """
    Bộ thu thập dữ liệu thị trường từ nhiều nguồn web.
    Mỗi phương thức đều:
      - Thử nhiều selector khác nhau (phòng web đổi cấu trúc)
      - Trả về SourceData kèm URL gốc
      - Ghi log chi tiết
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.sitemap = SitemapDiscoverer(self.session)
        # Cache cho _try_gia_nong_san_page — tránh 4 HTTP request đến cùng URL
        self._gia_nong_san_cache: Optional[List[SourceData]] = None
        # Redis cache cho kết quả scrape (tránh request lặp trong nhiều phút)
        try:
            from core.cache_manager import get_cache
            self._cache = get_cache()
        except ImportError:
            self._cache = None

    # ──────────────────────────────────────────────
    # THỜI BÁO TÀI CHÍNH VN — Nguồn chính, chính xác nhất
    # https://thoibaotaichinhvietnam.vn — báo tài chính nhà nước
    # ──────────────────────────────────────────────

    def _find_latest_tbtc_article(self, keywords: List[str]) -> Optional[str]:
        """
        Tìm bài viết mới nhất trên Thời báo Tài chính VN có chứa keywords.
        Dùng sitemap tháng hiện tại — cache Redis 15 phút.
        """
        # Cache key: web:tbtc:{keyword1}-{keyword2}
        cache_key = "-".join(k.lower().replace("-", "") for k in keywords)
        if self._cache:
            cached = self._cache.get("web", "tbtc", cache_key)
            if cached is not None:
                logger.info(f"✅ TBTC: dùng cache cho {keywords}")
                return cached if cached else None

        today = datetime.now().date()
        sitemap_url = (
            f"https://thoibaotaichinhvietnam.vn/stores/lookssitemaps/site_1/"
            f"sitemap-month-{today.year}-{today.month}.xml"
        )
        try:
            resp = self.session.get(sitemap_url, timeout=15)
            if resp.status_code != 200:
                return None
            root = ET.fromstring(resp.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            entries = []
            for url_elem in root.findall("sm:url", ns):
                loc = url_elem.findtext("sm:loc", "", ns)
                if not loc:
                    continue
                loc_lower = loc.lower()
                if all(kw.lower() in loc_lower for kw in keywords):
                    lastmod_str = url_elem.findtext("sm:lastmod", "", ns)
                    lastmod = None
                    if lastmod_str:
                        try:
                            lastmod = datetime.fromisoformat(
                                lastmod_str.replace("Z", "+00:00")
                            )
                        except:
                            pass
                    entries.append((loc, lastmod or datetime.min))
            if entries:
                entries.sort(key=lambda x: x[1], reverse=True)
                best_url = entries[0][0]
                logger.info(f"✅ TBTC: tìm thấy bài viết {best_url}")
                # Cache kết quả 15 phút
                if self._cache:
                    self._cache.set("web", best_url, "tbtc", cache_key, ttl=900)
                return best_url
        except Exception as e:
            logger.warning(f"⚠️ TBTC sitemap error: {e}")

        # Cache cả khi không tìm thấy (tránh retry)
        if self._cache:
            self._cache.set("web", None, "tbtc", cache_key, ttl=900)
        return None

    def _extract_price_from_tbtc_article(
        self, url: str, product: str,
        gia_lai_keywords: List[str],
        price_keywords: List[str],
        min_val: int, max_val: int
    ) -> Optional[SourceData]:
        """
        Trích xuất giá từ bài viết Thời báo Tài chính VN.
        Tìm giá gần "Gia Lai" hoặc giá trong vùng.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            # Chiến lược 1: Tìm giá gần "Gia Lai"
            price = None
            for kw in gia_lai_keywords:
                idx = page_text.lower().find(kw.lower())
                if idx >= 0:
                    nearby = page_text[max(0, idx - 30):idx + 200]
                    # Tìm số có format 1.234
                    numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
                    for n in numbers:
                        val = int(n.replace('.', ''))
                        if min_val < val < max_val:
                            price = float(val)
                            break
                    if price:
                        break

            # Chiến lược 2: Tìm trong toàn bài giá gần keyword sản phẩm
            if not price:
                for kw in price_keywords:
                    prices_found = self._extract_prices_from_text(
                        page_text, kw, min_val, max_val
                    )
                    if prices_found:
                        price = prices_found[0]
                        break

            if price:
                logger.info(
                    f"✅ TBTC ({product}): tìm thấy giá Gia Lai = {price:,.0f} VNĐ/kg "
                    f"từ {url}"
                )
                return SourceData(
                    price=price,
                    source_url=url,
                    source_name="thoibaotaichinhvietnam.vn",
                    fetched_at=now,
                    product_name=product,
                    notes=f"Giá {product} tại Gia Lai từ Thời báo Tài chính Việt Nam (nguồn chính thống)",
                )
        except Exception as e:
            logger.warning(f"⚠️ TBTC article parse error ({url}): {e}")
        return None

    def _extract_prices_from_text(
        self, page_text: str, keyword: str,
        min_val: int, max_val: int
    ) -> List[float]:
        """Trích xuất tất cả giá gần keyword trong text."""
        prices = []
        idx = page_text.lower().find(keyword.lower())
        if idx >= 0:
            nearby = page_text[max(0, idx - 50):idx + 300]
            numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
            for n in numbers:
                val = int(n.replace('.', ''))
                if min_val < val < max_val and val not in prices:
                    prices.append(float(val))
        return prices

    def _try_thoibaotaichinh_coffee(self) -> Optional[SourceData]:
        """
        Nguồn #1 (ưu tiên cao nhất): Thời báo Tài chính Việt Nam.
        Tìm bài viết mới nhất về giá cà phê, trích xuất giá Gia Lai.
        """
        url = self._find_latest_tbtc_article(["gia-ca-phe"])
        if not url:
            return None
        return self._extract_price_from_tbtc_article(
            url=url, product="Cà phê",
            gia_lai_keywords=["Gia Lai", "Đắk Lắk", "Tây Nguyên"],
            price_keywords=["cà phê", "cà phê nhân", "cà phê Robusta"],
            min_val=50000, max_val=200000,
        )

    def _try_thoibaotaichinh_pepper(self) -> Optional[SourceData]:
        """
        Nguồn #1 (ưu tiên cao nhất): Thời báo Tài chính Việt Nam.
        Tìm bài viết mới nhất về giá hồ tiêu, trích xuất giá Gia Lai.
        """
        url = self._find_latest_tbtc_article(["ho-tieu"])
        if not url:
            # Fallback: tìm bài có cả cà phê và tiêu (thường viết chung)
            url = self._find_latest_tbtc_article(["gia-ca-phe", "ho-tieu"])
        if not url:
            return None
        return self._extract_price_from_tbtc_article(
            url=url, product="Hồ tiêu",
            gia_lai_keywords=["Gia Lai", "Đắk Lắk", "Tây Nguyên"],
            price_keywords=["hồ tiêu", "tiêu", "giá tiêu"],
            min_val=80000, max_val=500000,
        )

    # ──────────────────────────────────────────────
    # CÀ PHÊ — Coffee
    # ──────────────────────────────────────────────

    def fetch_coffee_price(self) -> ResearchResult:
        """
        Lấy giá cà phê từ 7+ nguồn — DỪNG SỚM sau nguồn đầu tiên thành công.
        
        Nguồn (ưu tiên từ trên xuống):
          1. thoibaotaichinhvietnam.vn — Thời báo Tài chính VN ✅ chính xác nhất
          2. giacaphe.com — chuyên giá cà phê
          3. nongdanviet.vn — tin tức nông dân
          4. gianongsan247.com — giá nông sản cập nhật nhiều lần/ngày
          5. mxv.com.vn — Sở Giao dịch Hàng hóa VN
          6. congthuong.vn — Bộ Công Thương
          7. asemconnectvietnam.gov.vn — Cổng TT Thị trường Nông sản
        """
        result = ResearchResult(product_name="Cà phê")

        # TỐI ƯU: short-circuit — dừng ngay khi có nguồn thành công
        for fn in [self._try_thoibaotaichinh_coffee, self._try_giacaphe_coffee,
                    self._try_nongdanviet_coffee, self._try_gianongsan247_coffee,
                    self._try_mxv_coffee, self._try_congthuong_coffee,
                    self._try_asemconnect_coffee]:
            src = fn()
            result.total_sources_tried += 1
            if src:
                result.sources.append(src)
                result.successful_sources += 1
                break  # 🚀 DỪNG SỚM — không thử thêm nguồn nào nữa

        if not result.sources:
            result.error = "Không thể lấy giá cà phê từ bất kỳ nguồn nào"
            result.used_fallback = True

        return result

    def _try_giacaphe_coffee(self) -> Optional[SourceData]:
        """Nguồn 2: giacaphe.com — chuyên về giá cà phê Việt Nam."""
        urls_to_try = [
            "https://giacaphe.com/gia-ca-phe-noi-dia/",
            "https://giacaphe.com/",
        ]
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        for url in urls_to_try:
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.content, 'html.parser')
                page_text = soup.get_text()

                # === CHIẾN LƯỢC TÌM GIÁ GIA LAI ===

                # Cách A: Tìm dòng chứa "Gia Lai" trong bảng
                gia_lai_price = self._extract_price_near_text(
                    soup, page_text, "Gia Lai",
                    min_val=10000, max_val=200000
                )
                if gia_lai_price:
                    logger.info(f"✅ Giacaphe: tìm thấy giá Gia Lai = {gia_lai_price} VNĐ/kg")
                    return SourceData(
                        price=gia_lai_price,
                        source_url=url,
                        source_name="giacaphe.com",
                        fetched_at=now,
                        product_name="Cà phê",
                        notes=f"Giá cà phê Robusta tại Gia Lai — nguồn giacaphe.com",
                    )

                # Cách B: Tìm bất kỳ giá cà phê nào trong bảng
                any_price = self._find_any_coffee_price(soup, page_text)
                if any_price:
                    logger.info(f"✅ Giacaphe: tìm thấy giá cà phê = {any_price} VNĐ/kg (không xác định vùng)")
                    return SourceData(
                        price=any_price,
                        source_url=url,
                        source_name="giacaphe.com",
                        fetched_at=now,
                        product_name="Cà phê",
                        notes=f"Giá cà phê tham khảo — nguồn giacaphe.com (không xác định vùng cụ thể)",
                    )

                logger.warning(f"⚠️ Giacaphe: không tìm thấy giá ({url})")
            except Exception as e:
                logger.warning(f"⚠️ Giacaphe error ({url}): {e}")

        return None

    def _try_nongdanviet_coffee(self) -> Optional[SourceData]:
        """Nguồn 2: nongdanviet.vn — tin tức nông dân Việt."""
        url = "https://nongdanviet.vn/gia-ca-phe/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            price = self._extract_price_near_text(
                soup, page_text, "Gia Lai",
                min_val=10000, max_val=200000
            )
            if price:
                logger.info(f"✅ Nongdanviet (CF): tìm thấy giá = {price} VNĐ/kg")
                return SourceData(
                    price=price,
                    source_url=url,
                    source_name="nongdanviet.vn",
                    fetched_at=now,
                    product_name="Cà phê",
                    notes="Giá cà phê Gia Lai từ nongdanviet.vn",
                )
        except Exception as e:
            logger.warning(f"⚠️ Nongdanviet (CF) error: {e}")

        return None

    def _try_congthuong_coffee(self) -> Optional[SourceData]:
        """Nguồn 3: congthuong.vn — Bộ Công Thương."""
        url = "https://congthuong.vn/gia-ca-phe-hom-nay/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            price = self._extract_price_near_text(
                soup, page_text, "Gia Lai",
                min_val=10000, max_val=200000
            )
            if price:
                logger.info(f"✅ Congthuong.vn (CF): tìm thấy giá = {price} VNĐ/kg")
                return SourceData(
                    price=price,
                    source_url=url,
                    source_name="congthuong.vn",
                    fetched_at=now,
                    product_name="Cà phê",
                    notes="Giá cà phê từ Bộ Công Thương",
                )
        except Exception as e:
            logger.warning(f"⚠️ Congthuong.vn (CF) error: {e}")

        return None

    # ──────────────────────────────────────────────
    # HỒ TIÊU — Pepper
    # ──────────────────────────────────────────────

    def fetch_pepper_price(self) -> ResearchResult:
        """Lấy giá hồ tiêu từ 7+ nguồn — DỪNG SỚM sau nguồn đầu tiên thành công."""
        result = ResearchResult(product_name="Hồ tiêu")

        # TỐI ƯU: short-circuit
        for fn in [self._try_thoibaotaichinh_pepper, self._try_nongdanviet_pepper,
                    self._try_giacaphe_pepper, self._try_gianongsan247_pepper,
                    self._try_mxv_pepper, self._try_congthuong_pepper,
                    self._try_asemconnect_pepper]:
            src = fn()
            result.total_sources_tried += 1
            if src:
                result.sources.append(src)
                result.successful_sources += 1
                break  # 🚀 DỪNG SỚM

        if not result.sources:
            result.error = "Không thể lấy giá hồ tiêu từ bất kỳ nguồn nào"
            result.used_fallback = True

        return result

    def _try_nongdanviet_pepper(self) -> Optional[SourceData]:
        """Nguồn 1: nongdanviet.vn/gia-ho-tieu/"""
        url = "https://nongdanviet.vn/gia-ho-tieu/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            price = self._extract_price_near_text(
                soup, page_text, "Gia Lai",
                min_val=50000, max_val=500000
            )
            if price:
                logger.info(f"✅ Nongdanviet (Tieu): tìm thấy giá = {price} VNĐ/kg")
                return SourceData(
                    price=price,
                    source_url=url,
                    source_name="nongdanviet.vn",
                    fetched_at=now,
                    product_name="Hồ tiêu",
                    notes="Giá hồ tiêu Gia Lai từ nongdanviet.vn",
                )
        except Exception as e:
            logger.warning(f"⚠️ Nongdanviet (Tieu) error: {e}")

        return None

    def _try_giacaphe_pepper(self) -> Optional[SourceData]:
        """Nguồn 2: giacaphe.com cũng có giá hồ tiêu."""
        urls = [
            "https://giacaphe.com/gia-ho-tieu/",
            "https://giacaphe.com/",
        ]
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        for url in urls:
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.content, 'html.parser')
                page_text = soup.get_text()

                price = self._extract_price_near_text(
                    soup, page_text, "Gia Lai",
                    min_val=50000, max_val=500000
                )
                if price:
                    logger.info(f"✅ Giacaphe (Tieu): tìm thấy giá = {price} VNĐ/kg")
                    return SourceData(
                        price=price,
                        source_url=url,
                        source_name="giacaphe.com",
                        fetched_at=now,
                        product_name="Hồ tiêu",
                        notes="Giá hồ tiêu từ giacaphe.com",
                    )
            except Exception as e:
                logger.warning(f"⚠️ Giacaphe (Tieu) error ({url}): {e}")

        return None

    def _try_congthuong_pepper(self) -> Optional[SourceData]:
        """Nguồn 3: congthuong.vn — giá tiêu."""
        url = "https://congthuong.vn/gia-ho-tieu-hom-nay/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            price = self._extract_price_near_text(
                soup, page_text, "Gia Lai",
                min_val=50000, max_val=500000
            )
            if price:
                logger.info(f"✅ Congthuong (Tieu): tìm thấy giá = {price} VNĐ/kg")
                return SourceData(
                    price=price,
                    source_url=url,
                    source_name="congthuong.vn",
                    fetched_at=now,
                    product_name="Hồ tiêu",
                    notes="Giá hồ tiêu từ Bộ Công Thương",
                )
        except Exception as e:
            logger.warning(f"⚠️ Congthuong (Tieu) error: {e}")

        return None

    # ──────────────────────────────────────────────
    # GIANONGSAN247 — Giá Nông Sản 247 (cập nhật nhiều lần/ngày)
    # ──────────────────────────────────────────────

    def _try_gianongsan247_coffee(self) -> Optional[SourceData]:
        """Nguồn: gianongsan247.com — giá cà phê."""
        url = "https://gianongsan247.com/gia-ca-phe/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Gia Lai", min_val=10000, max_val=200000)
            if price:
                return SourceData(price=price, source_url=url, source_name="gianongsan247.com",
                    fetched_at=now, product_name="Cà phê", notes="Giá cà phê từ Giá Nông Sản 247")
        except Exception as e:
            logger.warning(f"⚠️ Gianongsan247 CF error: {e}")
        return None

    def _try_gianongsan247_pepper(self) -> Optional[SourceData]:
        """Nguồn: gianongsan247.com — giá hồ tiêu."""
        url = "https://gianongsan247.com/gia-ho-tieu/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Gia Lai", min_val=50000, max_val=500000)
            if price:
                return SourceData(price=price, source_url=url, source_name="gianongsan247.com",
                    fetched_at=now, product_name="Hồ tiêu", notes="Giá hồ tiêu từ Giá Nông Sản 247")
        except Exception as e:
            logger.warning(f"⚠️ Gianongsan247 Tieu error: {e}")
        return None

    def fetch_durian_price(self) -> ResearchResult:
        """Nghiên cứu giá sầu riêng từ nhiều nguồn."""
        result = ResearchResult(product_name="Sầu riêng")
        for fn in [self._try_gianongsan247_durian, self._try_nongdanviet_durian]:
            src = fn()
            result.total_sources_tried += 1
            if src:
                result.sources.append(src)
                result.successful_sources += 1
        if not result.sources:
            result.error = "Không thể lấy giá sầu riêng từ các nguồn"
            result.used_fallback = True
        return result

    def _try_gianongsan247_durian(self) -> Optional[SourceData]:
        """Nguồn: gianongsan247.com — giá sầu riêng."""
        url = "https://gianongsan247.com/gia-sau-rieng/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Riêng", min_val=10000, max_val=200000)
            # Sầu riêng thường có giá theo kg, rất dao động theo loại
            if price:
                return SourceData(price=price, source_url=url, source_name="gianongsan247.com",
                    fetched_at=now, product_name="Sầu riêng",
                    notes="Giá sầu riêng các loại từ Giá Nông Sản 247 (giá tham khảo theo loại)")
        except Exception as e:
            logger.warning(f"⚠️ Gianongsan247 Durian error: {e}")
        return None

    def _try_nongdanviet_durian(self) -> Optional[SourceData]:
        """Nguồn: nongdanviet.vn — giá sầu riêng."""
        url = "https://nongdanviet.vn/gia-sau-rieng/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Riêng", min_val=10000, max_val=200000)
            if price:
                return SourceData(price=price, source_url=url, source_name="nongdanviet.vn",
                    fetched_at=now, product_name="Sầu riêng",
                    notes="Giá sầu riêng từ Nông Dân Việt")
        except Exception as e:
            logger.warning(f"⚠️ Nongdanviet Durian error: {e}")
        return None

    def fetch_rice_price(self) -> ResearchResult:
        """Nghiên cứu giá lúa gạo từ nhiều nguồn."""
        result = ResearchResult(product_name="Lúa gạo")
        for fn in [self._try_gianongsan247_rice, self._try_nongdanviet_rice]:
            src = fn()
            result.total_sources_tried += 1
            if src:
                result.sources.append(src)
                result.successful_sources += 1
        if not result.sources:
            result.error = "Không thể lấy giá lúa gạo từ các nguồn"
            result.used_fallback = True
        return result

    # ──────────────────────────────────────────────
    # GIÁ NÔNG SẢN TỔNG HỢP — nongdanviet.vn/gia-nong-san
    # Trang này có bảng giá cho: Cao su, Điều nhân, Cacao, Mắc ca theo vùng
    # ──────────────────────────────────────────────

    def fetch_caosu_price(self) -> ResearchResult:
        """Giá Cao su từ nongdanviet.vn/gia-nong-san."""
        result = ResearchResult(product_name="Cao su")
        prices = self._try_gia_nong_san_page()
        for p in prices:
            if p.product_name == "Cao su":
                result.sources.append(p)
        if not result.sources:
            result.error = "Không lấy được giá Cao su"
            result.used_fallback = True
        else:
            result.successful_sources = 1
        result.total_sources_tried = 1
        return result

    def fetch_dieunhan_price(self) -> ResearchResult:
        """Giá Điều nhân từ nongdanviet.vn/gia-nong-san."""
        result = ResearchResult(product_name="Điều nhân")
        prices = self._try_gia_nong_san_page()
        for p in prices:
            if p.product_name == "Điều nhân":
                result.sources.append(p)
        if not result.sources:
            result.error = "Không lấy được giá Điều nhân"
            result.used_fallback = True
        else:
            result.successful_sources = 1
        result.total_sources_tried = 1
        return result

    def fetch_cacao_price(self) -> ResearchResult:
        """Giá Cacao từ nongdanviet.vn/gia-nong-san."""
        result = ResearchResult(product_name="Cacao")
        prices = self._try_gia_nong_san_page()
        for p in prices:
            if p.product_name == "Cacao":
                result.sources.append(p)
        if not result.sources:
            result.error = "Không lấy được giá Cacao"
            result.used_fallback = True
        else:
            result.successful_sources = 1
        result.total_sources_tried = 1
        return result

    def fetch_macca_price(self) -> ResearchResult:
        """Giá Mắc ca từ nongdanviet.vn/gia-nong-san."""
        result = ResearchResult(product_name="Mắc ca")
        prices = self._try_gia_nong_san_page()
        for p in prices:
            if p.product_name == "Mắc ca":
                result.sources.append(p)
        if not result.sources:
            result.error = "Không lấy được giá Mắc ca"
            result.used_fallback = True
        else:
            result.successful_sources = 1
        result.total_sources_tried = 1
        return result

    def _try_gia_nong_san_page(self) -> List[SourceData]:
        """
        Scrape https://nongdanviet.vn/gia-nong-san — bảng giá tổng hợp nhiều sản phẩm theo vùng.
        Trả về danh sách SourceData cho: Cao su, Điều nhân, Cacao, Mắc ca.
        
        TỐI ƯU: cache kết quả trong session — 4 sản phẩm chỉ gọi 1 HTTP request.
        """
        # Dùng cache nếu đã fetch trong session này
        if self._gia_nong_san_cache is not None:
            logger.info("✅ Dùng cache _try_gia_nong_san_page (đã fetch trước đó)")
            return self._gia_nong_san_cache

        url = "https://nongdanviet.vn/gia-nong-san"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        sources = []

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return sources

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            lines = page_text.split('\n')

            # Map tên sản phẩm → (từ khóa, min, max)
            product_map = {
                "Cao su": (["cao su", "caosu"], 5000, 50000),
                "Điều nhân": (["điều nhân", "dieu nhan"], 50000, 500000),
                "Cacao": (["cacao", "ca cao"], 10000, 200000),
                "Mắc ca": (["mắc ca", "mac ca", "macadamia"], 30000, 300000),
            }

            for product_name, (keywords, min_v, max_v) in product_map.items():
                price = self._extract_price_from_text_generic(lines, keywords, min_v, max_v)
                if price:
                    # Tìm vùng trong text gần giá
                    region = self._find_region_near_price(page_text, price)
                    notes = f"Giá {product_name}{' - ' + region if region else ''} từ bảng giá nông sản tổng hợp nongdanviet.vn"
                    sources.append(SourceData(
                        price=price, source_url=url,
                        source_name="nongdanviet.vn",
                        fetched_at=now, product_name=product_name,
                        notes=notes,
                    ))
                    logger.info(f"✅ GiaNongSan: {product_name} = {price:,} VNĐ/kg{region}')")

            # Lưu cache cho các lần gọi tiếp theo (Mắc ca, Cacao,...)
            self._gia_nong_san_cache = sources
            return sources

        except Exception as e:
            logger.error(f"❌ GiaNongSan error: {e}")
            self._gia_nong_san_cache = sources  # cache cả khi rỗng (tránh retry)
            return sources

    def _extract_price_from_text_generic(self, lines: List[str],
                                           keywords: List[str],
                                           min_val: int, max_val: int) -> Optional[float]:
        """Tìm giá trong list lines gần từ khóa."""
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                # Tìm trong dòng này và 5 dòng tiếp theo
                for j in range(i, min(i + 5, len(lines))):
                    numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', lines[j])
                    for n in numbers:
                        val = int(n.replace('.', ''))
                        if min_val < val < max_val:
                            return float(val)
                # Nếu không tìm thấy số, thử tìm số trong toàn bộ gần keyword
                nearby = ' '.join(lines[i:min(i + 5, len(lines))])
                numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
                for n in numbers:
                    val = int(n.replace('.', ''))
                    if min_val < val < max_val:
                        return float(val)
        return None

    def _find_region_near_price(self, page_text: str, price: float) -> str:
        """Xác định vùng gần giá trong text."""
        regions = ["Tây Nguyên", "Đông Nam Bộ", "ĐBSCL", "Miền Trung", "Miền Bắc",
                   "Tây Nguyên", "Gia Lai", "Đắk Lắk", "Đắk Nông", "Lâm Đồng",
                   "Kon Tum", "Bình Phước", "Đồng Nai", "Bà Rịa"]
        idx = page_text.find(f"{int(price):,}".replace(',', '.'))
        if idx < 0:
            idx = page_text.find(f"{int(price)}")
        if idx >= 0:
            before = page_text[max(0, idx - 100):idx]
            for r in regions:
                if r in before:
                    return r
        return ""

    def _try_gianongsan247_rice(self) -> Optional[SourceData]:
        """Nguồn: gianongsan247.com — giá lúa gạo."""
        url = "https://gianongsan247.com/gia-lua-gao/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "lúa", min_val=3000, max_val=30000)
            if price:
                return SourceData(price=price, source_url=url, source_name="gianongsan247.com",
                    fetched_at=now, product_name="Lúa gạo",
                    notes="Giá lúa gạo từ Giá Nông Sản 247")
        except Exception as e:
            logger.warning(f"⚠️ Gianongsan247 Rice error: {e}")
        return None

    def _try_nongdanviet_rice(self) -> Optional[SourceData]:
        """Nguồn: nongdanviet.vn — giá lúa gạo."""
        url = "https://nongdanviet.vn/gia-lua-gao/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "lúa", min_val=3000, max_val=30000)
            if price:
                return SourceData(price=price, source_url=url, source_name="nongdanviet.vn",
                    fetched_at=now, product_name="Lúa gạo",
                    notes="Giá lúa gạo từ Nông Dân Việt")
        except Exception as e:
            logger.warning(f"⚠️ Nongdanviet Rice error: {e}")
        return None

    # ──────────────────────────────────────────────
    # MXV — Sở Giao dịch Hàng hóa Việt Nam
    # ──────────────────────────────────────────────

    def _try_mxv_coffee(self) -> Optional[SourceData]:
        """Nguồn: mxv.com.vn — giá cà phê từ Sở Giao dịch HH VN."""
        url = "https://mxv.com.vn/thi-truong-hang-hoa/ca-phe/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                url = "https://mxv.com.vn/"
                resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            # Tìm giá Robusta hoặc cà phê
            price = self._extract_price_near_text(soup, page_text, "Robusta", min_val=10000, max_val=200000)
            if not price:
                price = self._find_any_coffee_price(soup, page_text)
            if price:
                return SourceData(price=price, source_url=url, source_name="mxv.com.vn",
                    fetched_at=now, product_name="Cà phê",
                    notes="Giá cà phê từ Sở Giao dịch Hàng hóa Việt Nam (MXV)")
        except Exception as e:
            logger.warning(f"⚠️ MXV CF error: {e}")
        return None

    def _try_mxv_pepper(self) -> Optional[SourceData]:
        """Nguồn: mxv.com.vn — giá hồ tiêu."""
        url = "https://mxv.com.vn/thi-truong-hang-hoa/ho-tieu/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                url = "https://mxv.com.vn/"
                resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "tiêu", min_val=50000, max_val=500000)
            if price:
                return SourceData(price=price, source_url=url, source_name="mxv.com.vn",
                    fetched_at=now, product_name="Hồ tiêu",
                    notes="Giá hồ tiêu từ Sở Giao dịch Hàng hóa Việt Nam (MXV)")
        except Exception as e:
            logger.warning(f"⚠️ MXV Tieu error: {e}")
        return None

    # ──────────────────────────────────────────────
    # ASEM CONNECT — Cổng TT Thị trường Nông sản VN
    # ──────────────────────────────────────────────

    def _try_asemconnect_coffee(self) -> Optional[SourceData]:
        """Nguồn: asemconnectvietnam.gov.vn — cổng thông tin thị trường nông sản."""
        url = "https://asemconnectvietnam.gov.vn/thi-truong/ca-phe/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                url = "https://asemconnectvietnam.gov.vn"
                resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Gia Lai", min_val=10000, max_val=200000)
            if not price:
                price = self._find_any_coffee_price(soup, page_text)
            if price:
                return SourceData(price=price, source_url=url, source_name="asemconnectvietnam.gov.vn",
                    fetched_at=now, product_name="Cà phê",
                    notes="Giá cà phê từ Cổng TT Thị trường Nông sản Việt Nam (ASEM Connect — Bộ Công Thương)")
        except Exception as e:
            logger.warning(f"⚠️ Asemconnect CF error: {e}")
        return None

    def _try_asemconnect_pepper(self) -> Optional[SourceData]:
        """Nguồn: asemconnectvietnam.gov.vn — giá hồ tiêu."""
        url = "https://asemconnectvietnam.gov.vn/thi-truong/ho-tieu/"
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()
            price = self._extract_price_near_text(soup, page_text, "Gia Lai", min_val=50000, max_val=500000)
            if price:
                return SourceData(price=price, source_url=url, source_name="asemconnectvietnam.gov.vn",
                    fetched_at=now, product_name="Hồ tiêu",
                    notes="Giá hồ tiêu từ ASEM Connect (Bộ Công Thương)")
        except Exception as e:
            logger.warning(f"⚠️ Asemconnect Tieu error: {e}")
        return None

    # ──────────────────────────────────────────────
    # TIN TỨC THỊ TRƯỜNG
    # ──────────────────────────────────────────────

    def fetch_market_news(self, product: str = "cà phê") -> List[Dict]:
        """
        Lấy tin tức thị trường mới nhất về sản phẩm.
        Trả về list các dict: {title, url, snippet, source, date}
        """
        news_sources = {
            "cà phê": [
                "https://giacaphe.com/",
                "https://congthuong.vn/gia-ca-phe-hom-nay/",
            ],
            "hồ tiêu": [
                "https://nongdanviet.vn/gia-ho-tieu/",
                "https://congthuong.vn/gia-ho-tieu-hom-nay/",
            ],
        }

        results = []
        urls = news_sources.get(product.lower(), news_sources["cà phê"])

        for url in urls:
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.content, 'html.parser')
                page_text = soup.get_text()[:500].strip()

                # Trích xuất title
                title = ""
                if soup.title:
                    title = soup.title.get_text(strip=True)

                results.append({
                    "title": title or f"Báo cáo thị trường {product}",
                    "url": url,
                    "snippet": page_text[:300],
                    "source": url.split("//")[1].split("/")[0] if "//" in url else url,
                    "fetched_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
            except Exception as e:
                logger.warning(f"⚠️ News fetch error ({url}): {e}")

        return results

    # ──────────────────────────────────────────────
    # HELPER METHODS
    # ──────────────────────────────────────────────

    def _extract_price_near_text(
        self, soup: BeautifulSoup, page_text: str,
        keyword: str, min_val: int = 0, max_val: int = 999999
    ) -> Optional[float]:
        """
        Cố gắng tìm giá (số) gần keyword trong trang web.
        Thử nhiều chiến lược khác nhau.
        """
        # Chiến lược 1: Tìm trong bảng HTML — td chứa keyword, td kế tiếp chứa giá
        for td in soup.find_all('td'):
            if keyword.lower() in td.get_text(strip=True).lower():
                next_td = td.find_next_sibling('td')
                if next_td:
                    val = self._clean_price_text(next_td.get_text(strip=True))
                    if val and min_val < val < max_val:
                        return float(val)

                # Thử tìm td tiếp theo trong cùng hàng
                parent_tr = td.find_parent('tr')
                if parent_tr:
                    all_tds = parent_tr.find_all('td')
                    for other_td in all_tds:
                        if other_td != td:
                            val = self._clean_price_text(other_td.get_text(strip=True))
                            if val and min_val < val < max_val:
                                return float(val)

        # Chiến lược 2: Tìm số gần keyword trong text
        idx = page_text.lower().find(keyword.lower())
        if idx >= 0:
            nearby = page_text[max(0, idx - 30):idx + 150]
            # Tìm tất cả số có format 1.234 hoặc 1234
            numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
            for n in numbers:
                val = int(n.replace('.', ''))
                if min_val < val < max_val:
                    return float(val)

            # Thử tìm số không có dấu chấm
            numbers2 = re.findall(r'(\d{5,6})', nearby)
            for n in numbers2:
                val = int(n)
                if min_val < val < max_val:
                    return float(val)

        return None

    def _clean_price_text(self, text: str) -> Optional[float]:
        """Làm sạch text giá và trả về số."""
        if not text:
            return None
        # Loại bỏ ký tự đặc biệt, giữ lại số và dấu chấm/phẩy
        cleaned = re.sub(r'[^\d.,]', '', text)
        cleaned = cleaned.replace(',', '.').strip()
        # Xử lý nhiều dấu chấm (vd: 1.234.567)
        if cleaned.count('.') > 1:
            # Bỏ dấu chấm hàng nghìn, giữ lại phần thập phân
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        try:
            val = float(cleaned)
            if val > 0:
                return val
        except ValueError:
            pass
        return None

    def _find_any_coffee_price(self, soup: BeautifulSoup, page_text: str) -> Optional[float]:
        """Tìm bất kỳ giá cà phê nào trong trang (khi không tìm thấy Gia Lai)."""
        # Tìm trong bảng
        for table in soup.find_all('table'):
            for td in table.find_all('td'):
                text = td.get_text(strip=True)
                val = self._clean_price_text(text)
                if val and 10000 < val < 200000:
                    return float(val)

        # Tìm trong toàn bộ text
        numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)', page_text)
        for n in numbers:
            val = int(n.replace('.', ''))
            if 10000 < val < 200000:
                return float(val)

        return None


# ==================== PUBLIC API ====================

class WebMarketResearcher:
    """
    Giao diện chính cho web research.
    Được sử dụng bởi:
      - MarketDataManager (để lưu vào DB)
      - AI Agent (để phân tích + trích dẫn)
      - UI (để hiển thị)
    """

    def __init__(self):
        self.fetcher = WebMarketFetcher()

    def research_coffee(self) -> ResearchResult:
        """Nghiên cứu giá cà phê — 6 nguồn (giacaphe, nongdanviet, gianongsan247, mxv, congthuong, asemconnect)."""
        return self.fetcher.fetch_coffee_price()

    def research_pepper(self) -> ResearchResult:
        """Nghiên cứu giá hồ tiêu — 6 nguồn."""
        return self.fetcher.fetch_pepper_price()

    def research_durian(self) -> ResearchResult:
        """Nghiên cứu giá sầu riêng — 2+ nguồn."""
        return self.fetcher.fetch_durian_price()

    def research_rice(self) -> ResearchResult:
        """Nghiên cứu giá lúa gạo — 2+ nguồn."""
        return self.fetcher.fetch_rice_price()

    def research_caosu(self) -> ResearchResult:
        """Giá Cao su từ nongdanviet.vn/gia-nong-san."""
        return self.fetcher.fetch_caosu_price()

    def research_dieunhan(self) -> ResearchResult:
        """Giá Điều nhân từ nongdanviet.vn/gia-nong-san."""
        return self.fetcher.fetch_dieunhan_price()

    def research_cacao(self) -> ResearchResult:
        """Giá Cacao từ nongdanviet.vn/gia-nong-san."""
        return self.fetcher.fetch_cacao_price()

    def research_macca(self) -> ResearchResult:
        """Giá Mắc ca từ nongdanviet.vn/gia-nong-san."""
        return self.fetcher.fetch_macca_price()

    def research_all(self) -> Dict[str, ResearchResult]:
        """Nghiên cứu tất cả sản phẩm (8 loại)."""
        return {
            "coffee": self.research_coffee(),
            "pepper": self.research_pepper(),
            "durian": self.research_durian(),
            "rice": self.research_rice(),
            "caosu": self.research_caosu(),
            "dieunhan": self.research_dieunhan(),
            "cacao": self.research_cacao(),
            "macca": self.research_macca(),
        }

    def get_market_news(self, product: str = "cà phê") -> List[Dict]:
        """Lấy tin tức thị trường."""
        return self.fetcher.fetch_market_news(product)

    def get_citation_summary(self) -> str:
        """Lấy bảng trích dẫn đầy đủ cho tất cả sản phẩm."""
        results = self.research_all()
        lines = ["📊 BÁO CÁO THỊ TRƯỜNG HÔM NAY", "=" * 60]
        lines.append("Nguồn: giacaphe.com, nongdanviet.vn, gianongsan247.com, mxv.com.vn, congthuong.vn, asemconnectvietnam.gov.vn")
        lines.append(f"Thời điểm: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        for key, result in results.items():
            lines.append(f"\n--- {result.product_name} ---")
            if result.error:
                lines.append(f"❌ {result.error}")
            else:
                lines.append(result.detailed_citations())
        return "\n".join(lines)


# ==================== CLI TEST ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    researcher = WebMarketResearcher()

    print("🌐 ĐANG NGHIÊN CỨU THỊ TRƯỜNG...\n")

    coffee = researcher.research_coffee()
    print(coffee.citation_text())
    print()
    print(coffee.detailed_citations())

    print("\n" + "=" * 60 + "\n")

    pepper = researcher.research_pepper()
    print(pepper.citation_text())
    print()
    print(pepper.detailed_citations())
