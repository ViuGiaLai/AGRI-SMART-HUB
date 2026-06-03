# -*- coding: utf-8 -*-
"""
core/market_connection.py — Kết nối thị trường nông sản toàn quốc.

Tổng hợp dữ liệu từ nhiều nguồn (nongdanviet.vn, các sàn TMĐT, chợ đầu mối)
và cung cấp giao diện dữ liệu thống nhất cho UI.

Sơ đồ:
  WebScraper → MarketConnectionManager → UI Frame
      ↑               ↑
  nongdanviet       Supabase (tuỳ chọn)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ==================== DATA STRUCTURES ====================

@dataclass
class ConnectionCategory:
    """Một danh mục kết nối (vd: Phân bón, Đại lý thu mua...)."""
    name: str
    icon: str
    count: int
    unit: str               # "đại lý", "cơ sở", "doanh nghiệp", "tổ chức"
    description: str
    source_url: str = ""

@dataclass
class FeaturedPartner:
    """Một đối tác nổi bật."""
    name: str
    icon: str
    description: str
    source_url: str = ""

@dataclass
class ConnectionData:
    """Toàn bộ dữ liệu kết nối thị trường."""
    categories: List[ConnectionCategory] = field(default_factory=list)
    partners: List[FeaturedPartner] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        "total_partners": 0,
        "total_provinces": 0,
    })
    fetched_at: str = ""
    source_name: str = "nongdanviet.vn"
    source_url: str = "https://nongdanviet.vn/ket-noi"
    error: Optional[str] = None


# ==================== SCRAPER ====================

class NongDanVietConnector:
    """
    Scrape dữ liệu kết nối từ nongdanviet.vn/ket-noi.
    Tự động parse danh mục, đối tác nổi bật và thống kê.
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_connections(self) -> ConnectionData:
        """
        Lấy toàn bộ dữ liệu kết nối từ nongdanviet.vn/ket-noi.
        Returns ConnectionData với đầy đủ categories, partners, stats.
        """
        data = ConnectionData()
        data.fetched_at = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            resp = self.session.get(data.source_url, timeout=15)
            if resp.status_code != 200:
                data.error = f"HTTP {resp.status_code}"
                return data

            soup = BeautifulSoup(resp.content, 'html.parser')
            page_text = soup.get_text()

            # === 1. Thống kê ===
            data.stats = self._parse_stats(page_text)

            # === 2. Danh mục kết nối ===
            data.categories = self._parse_categories(page_text)

            # === 3. Đối tác nổi bật ===
            data.partners = self._parse_partners(soup, page_text)

            logger.info(
                f"✅ Đã lấy {len(data.categories)} danh mục, "
                f"{len(data.partners)} đối tác từ {data.source_url}"
            )

        except requests.RequestException as e:
            data.error = f"Lỗi kết nối: {e}"
            logger.error(f"❌ Lỗi fetch {data.source_url}: {e}")
        except Exception as e:
            data.error = f"Lỗi xử lý: {e}"
            logger.error(f"❌ Lỗi parse {data.source_url}: {e}")

        return data

    def _parse_stats(self, page_text: str) -> Dict[str, int]:
        """Trích xuất thống kê (đối tác, tỉnh thành)."""
        stats = {"total_partners": 0, "total_provinces": 0}

        # Tìm số sau "đối tác đăng ký"
        match = re.search(r'(\d+)\s*đối tác', page_text)
        if match:
            stats["total_partners"] = int(match.group(1))

        # Tìm số sau "tỉnh thành"
        match = re.search(r'(\d+)\s*tỉnh thành', page_text)
        if match:
            stats["total_provinces"] = int(match.group(1))

        return stats

    def _parse_categories(self, page_text: str) -> List[ConnectionCategory]:
        """Trích xuất danh mục kết nối từ text."""
        categories = []
        lines = page_text.split('\n')

        # Map icon → tên
        icon_map = {
            "🌿": "Phân bón & Vật tư",
            "🏪": "Đại lý thu mua",
            "🚜": "Máy móc nông cụ",
            "🌱": "Giống cây trồng",
            "🏭": "Doanh nghiệp XK",
            "🏦": "Tài chính - Vay vốn",
        }

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Phát hiện dòng có icon
            for icon, name in icon_map.items():
                if icon in line:
                    # Dòng này: "🌿1" hoặc "🌿 1"
                    count_match = re.search(r'(\d+)', line)
                    count = int(count_match.group(1)) if count_match else 0

                    # Dòng tiếp theo: "đại lý", "cơ sở", ...
                    unit = ""
                    if i + 1 < len(lines):
                        unit = lines[i + 1].strip()

                    # Dòng tiếp theo nữa: tên danh mục
                    cat_name = name
                    desc = ""
                    if i + 2 < len(lines):
                        desc = lines[i + 2].strip()

                    # Dòng tiếp theo nữa: mô tả (nếu có)
                    full_desc = desc
                    if i + 3 < len(lines) and len(lines[i + 3].strip()) > 20:
                        full_desc = lines[i + 3].strip()

                    categories.append(ConnectionCategory(
                        name=cat_name,
                        icon=icon,
                        count=count,
                        unit=unit,
                        description=full_desc,
                        source_url="https://nongdanviet.vn/ket-noi",
                    ))
                    break
            i += 1

        return categories

    def _parse_partners(self, soup: BeautifulSoup, page_text: str) -> List[FeaturedPartner]:
        """Trích xuất đối tác nổi bật."""
        partners = []

        # Dùng regex để tìm các đối tác trong text
        partner_patterns = [
            ("Agribank", "🏦", "Ngân hàng nông nghiệp"),
            ("Đầu Trâu", "🌿", "Phân bón"),
            ("VINA CHO", "☕", "Thu mua cà phê"),
            ("Trung Nguyên", "☕", "Chế biến cà phê"),
            ("Vinacam", "🌱", "Xuất khẩu nông sản"),
            ("HAGL Agrico", "🏭", "Nông nghiệp lớn"),
        ]

        for name, icon, desc in partner_patterns:
            if name.lower() in page_text.lower():
                partners.append(FeaturedPartner(
                    name=name,
                    icon=icon,
                    description=desc,
                    source_url="https://nongdanviet.vn/ket-noi",
                ))

        return partners


# ==================== MANAGER ====================

class MarketConnectionManager:
    """
    Quản lý dữ liệu kết nối thị trường.
    - Fetch từ nhiều nguồn (nongdanviet.vn, mở rộng sau)
    - Cache dữ liệu
    - Cung cấp API cho UI
    """

    def __init__(self):
        self._cache: Optional[ConnectionData] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 phút

    def get_connections(self, force_refresh: bool = False) -> ConnectionData:
        """
        Lấy dữ liệu kết nối thị trường.
        Dùng cache nếu có và chưa hết hạn.
        """
        now = datetime.now()

        if not force_refresh and self._cache and self._cache_time:
            elapsed = (now - self._cache_time).total_seconds()
            if elapsed < self._cache_ttl_seconds:
                return self._cache

        # Fetch mới
        connector = NongDanVietConnector()
        data = connector.fetch_connections()

        # Cache
        self._cache = data
        self._cache_time = now

        return data

    def get_categories(self) -> List[ConnectionCategory]:
        """Lấy danh sách danh mục."""
        return self.get_connections().categories

    def get_partners(self) -> List[FeaturedPartner]:
        """Lấy danh sách đối tác nổi bật."""
        return self.get_connections().partners

    def get_stats(self) -> Dict[str, int]:
        """Lấy thống kê."""
        return self.get_connections().stats

    def clear_cache(self):
        """Xoá cache để lần sau fetch mới."""
        self._cache = None
        self._cache_time = None


# ==================== MỞ RỘNG: CÁC NGUỒN KHÁC ====================
# Sau này có thể thêm:
# - chodautmua.vn — chợ đầu mối nông sản
# - agromonitor.vn — giám sát thị trường
# - sàn giao dịch nông sản các tỉnh

# ==================== CLI TEST ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mgr = MarketConnectionManager()
    data = mgr.get_connections(force_refresh=True)

    print(f"\n{'='*60}")
    print(f"🌐 KẾT NỐI THỊ TRƯỜNG NÔNG SẢN")
    print(f"{'='*60}")
    print(f"Nguồn: {data.source_url}")
    print(f"Lúc: {data.fetched_at}")

    if data.error:
        print(f"❌ Lỗi: {data.error}")
    else:
        print(f"\n📊 THỐNG KÊ:")
        print(f"  • Đối tác: {data.stats.get('total_partners', 0)}")
        print(f"  • Tỉnh thành: {data.stats.get('total_provinces', 0)}")

        print(f"\n📂 DANH MỤC KẾT NỐI:")
        for cat in data.categories:
            print(f"  {cat.icon} {cat.name}: {cat.count} {cat.unit}")
            print(f"     {cat.description}")

        print(f"\n🌟 ĐỐI TÁC NỔI BẬT:")
        for p in data.partners:
            print(f"  {p.icon} {p.name} — {p.description}")
