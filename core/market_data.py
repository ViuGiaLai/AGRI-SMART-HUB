# -*- coding: utf-8 -*-
# core/market_data.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import Any, Dict, Optional, List
import json
import logging
import os
import customtkinter as ctk
from dotenv import load_dotenv
from database.db_manager import DatabaseManager

load_dotenv()

logger = logging.getLogger(__name__)

# Import WebMarketResearcher — bộ nghiên cứu thị trường tự động từ web
try:
    from core.web_researcher import WebMarketResearcher, ResearchResult
except ImportError:
    WebMarketResearcher = None
    ResearchResult = None

class MarketDataFetcher:
    """Market Data Fetcher - Lấy dữ liệu thị trường nông sản"""
    
    def __init__(self):
        # Headers quan trọng để tránh bị chặn (403 Forbidden)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
    
    def fetch_coffee_price(self):
        """Lấy giá cà phê - Nguồn: Giacaphe.com"""
        url = "https://giacaphe.com/gia-ca-phe-noi-dia/"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Tìm giá Gia Lai trong bảng
                price_row = soup.find('td', string=lambda t: t and 'Gia Lai' in t)
                if price_row:
                    price_val = price_row.find_next_sibling('td').text
                    return int(price_val.replace('.', '').strip())
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá cà phê: {e}")
            return None
    
    def fetch_pepper_price(self):
        """Lấy giá hồ tiêu - Nguồn: Tintaynguyen.com"""
        url = "https://tintaynguyen.com/gia-ho-tieu/"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Tìm giá tại Gia Lai
                td_gialai = soup.find('td', string=lambda t: t and 'Gia Lai' in t)
                if td_gialai:
                    price_text = td_gialai.find_next_sibling('td').text
                    return int(price_text.replace('.', '').replace('đ', '').strip())
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá hồ tiêu: {e}")
            return None
    
    def fetch_exchange_rate(self):
        """Tỷ giá USD/VND - Sử dụng API"""
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('rates', {}).get('VND', 25450)
            return 25450
        except:
            return 25450
    
    def diagnose(self):
        """Công cụ chẩn đoán lỗi"""
        urls = [
            "https://giacaphe.com/gia-ca-phe-noi-dia/",
            "https://tintaynguyen.com/gia-ho-tieu/",
        ]
        
        results = {}
        for url in urls:
            try:
                res = requests.get(url, headers=self.headers, timeout=5)
                results[url] = f"Status: {res.status_code}"
            except Exception as e:
                results[url] = f"Error: {e}"
        
        return results
    
    def fetch_coffee_price_robust(self):
        """
        Lấy giá cà phê — thử nhiều selector phòng khi website thay đổi cấu trúc.
        Returns None nếu không lấy được.
        """
        url = "https://giacaphe.com/gia-ca-phe-noi-dia/"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Thử nhiều cách tìm giá Gia Lai
            # Cách 1: td chứa "Gia Lai"
            for td in soup.find_all('td'):
                text = td.get_text(strip=True)
                if 'Gia Lai' in text:
                    next_td = td.find_next_sibling('td')
                    if next_td:
                        try:
                            val = next_td.get_text(strip=True)
                            val = val.replace('.', '').replace(',', '.').replace('đ', '').strip()
                            if val.replace('.', '').replace(',', '').isdigit():
                                return int(float(val))
                        except:
                            pass
            
            # Cách 2: tìm trong table rows
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                for td in tds:
                    if 'Gia Lai' in td.get_text(strip=True):
                        for sibling in tds:
                            try:
                                val = sibling.get_text(strip=True).replace('.', '').replace('đ', '').strip()
                                if val.isdigit() and int(val) > 1000:
                                    return int(val)
                            except:
                                pass
            
            # Cách 3: tìm bất kỳ số nào > 10000 gần chữ "Gia Lai"
            page_text = soup.get_text()
            import re
            numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*)\s*(?:đ|vnd|vnđ)?', page_text, re.IGNORECASE)
            gia_lai_idx = page_text.find('Gia Lai')
            if gia_lai_idx >= 0:
                nearby = page_text[gia_lai_idx:gia_lai_idx+200]
                nearby_nums = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
                for n in nearby_nums:
                    val = int(n.replace('.', ''))
                    if 10000 < val < 200000:
                        return val
            
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá cà phê robust: {e}")
            return None
    
    def fetch_pepper_price_robust(self):
        """
        Lấy giá hồ tiêu — thử nhiều selector phòng khi website thay đổi cấu trúc.
        Returns None nếu không lấy được.
        """
        url = "https://tintaynguyen.com/gia-ho-tieu/"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cách 1: td chứa "Gia Lai"
            for td in soup.find_all('td'):
                text = td.get_text(strip=True)
                if 'Gia Lai' in text:
                    next_td = td.find_next_sibling('td')
                    if next_td:
                        try:
                            val = next_td.get_text(strip=True)
                            val = val.replace('.', '').replace(',', '.').replace('đ', '').strip()
                            if val.replace('.', '').replace(',', '').isdigit():
                                return int(float(val))
                        except:
                            pass
            
            # Cách 2: tìm bất kỳ số lớn > 50000 gần "Gia Lai"
            import re
            page_text = soup.get_text()
            gia_lai_idx = page_text.find('Gia Lai')
            if gia_lai_idx >= 0:
                nearby = page_text[gia_lai_idx:gia_lai_idx+200]
                nearby_nums = re.findall(r'(\d{1,3}(?:\.\d{3})*)', nearby)
                for n in nearby_nums:
                    val = int(n.replace('.', ''))
                    if 50000 < val < 500000:
                        return val
            
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá hồ tiêu robust: {e}")
            return None

class MarketDataManager:
    """Quản lý dữ liệu thị trường từ nhiều nguồn"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.fetcher = MarketDataFetcher()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.google.com/'
        }
        
        # Các API endpoints thực tế
        self.apis = {
            # Coffee
            "coffee_vietnam": "https://giacaphe.com/gia-ca-phe-noi-dia/",
            "coffee_london": "https://giacaphe.com/gia-ca-phe-truc-tuyen/london/",
            "coffee_ico": "https://www.ico.org/prices/new-prices",
            # Pepper
            "pepper_vietnam": "https://tintaynguyen.com/gia-ho-tieu/",
            "pepper_global": "https://www.indexmundi.com/agricultural/?country=vn&commodity=black-pepper",
            # Cashew
            "cashew_vietnam": "https://vietnambusiness.gov.vn/",
            # Rubber
            "rubber_vietnam": "https://www.vnr.org.vn/",
            # Cassava
            "cassava_vietnam": "https://tintaynguyen.com/gia-san-xay/",
            # Exchange rate
            "exchange_rate": "https://api.exchangerate-api.com/v4/latest/USD",
            "vietcombank": "https://www.vietcombank.com.vn/",
        }
    
    def fetch_coffee_prices(self) -> Dict:
        """
        Lấy giá cà phê từ các nguồn
        Trong thực tế, có thể dùng:
        - ICO (International Coffee Organization)
        - London ICE Futures
        - New York ICE Futures
        - Giá nội địa từ các sàn giao dịch VN
        """
        # Demo data - Trong thực tế sẽ gọi API thật
        return {
            "robusta_london": 3800,  # USD/ton
            "arabica_ny": 185,       # UScent/lb
            "domestic_daklak": 45000, # VND/kg
            "domestic_gialai": 44500, # VND/kg
            "domestic_lamdong": 46000, # VND/kg
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_pepper_prices(self) -> Dict:
        """Lấy giá hồ tiêu"""
        return {
            "black_pepper": 180000,  # VND/kg
            "white_pepper": 220000,  # VND/kg
            "global_price": 4200,    # USD/ton
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_cashew_prices(self) -> Dict:
        """Lấy giá điều"""
        return {
            "cashew_kernel": 250000,  # VND/kg
            "raw_cashew": 15000,     # VND/kg
            "global_price": 3500,     # USD/ton
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_rubber_prices(self) -> Dict:
        """Lấy giá cao su"""
        return {
            "rubber_scr20": 45000,    # VND/kg
            "rubper_scr5": 55000,    # VND/kg
            "latex": 35000,        # VND/kg
            "global_price": 1600,   # USD/ton
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_cassava_prices(self) -> Dict:
        """Lấy giá sắn"""
        return {
            "cassava_chip": 6500,   # VND/kg
            "cassava_starch": 12000, # VND/kg
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_corn_prices(self) -> Dict:
        """Lấy giá ngô"""
        return {
            "corn_yellow": 6500,    # VND/kg
            "corn_white": 7000,     # VND/kg
            "global_price": 250,     # USD/ton
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_rice_prices(self) -> Dict:
        """Lấy giá lúa gạo"""
        return {
            "rice_ir504": 12000,    # VND/kg
            "rice_jasmine": 18000,   # VND/kg
            "rice_st25": 22000,    # VND/kg
            "global_price": 550,     # USD/ton
            "updated_at": datetime.now().isoformat()
        }

    def fetch_caosu_prices(self) -> Dict:
        """Lấy giá Cao su"""
        return {
            "rubber_scr20": 45000,    # VND/kg
            "rubber_scr5": 55000,     # VND/kg
            "latex": 35000,           # VND/kg
            "global_price": 1600,     # USD/ton
            "updated_at": datetime.now().isoformat()
        }

    def fetch_dieunhan_prices(self) -> Dict:
        """Lấy giá Điều nhân"""
        return {
            "cashew_kernel_ws": 250000,  # VND/kg
            "cashew_kernel_wp": 280000,  # VND/kg
            "global_price": 3800,        # USD/ton
            "updated_at": datetime.now().isoformat()
        }

    def fetch_cacao_prices(self) -> Dict:
        """Lấy giá Cacao"""
        return {
            "cacao_butter": 180000,      # VND/kg
            "cacao_powder": 120000,      # VND/kg
            "cacao_bean": 85000,         # VND/kg
            "global_price": 3200,        # USD/ton
            "updated_at": datetime.now().isoformat()
        }

    def fetch_macca_prices(self) -> Dict:
        """Lấy giá Mắc ca"""
        return {
            "macca_kernel": 250000,      # VND/kg
            "macca_raw": 80000,          # VND/kg
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_exchange_rate(self) -> float:
        """Lấy tỷ giá USD/VND"""
        try:
            # Gọi API tỷ giá
            response = requests.get(
                "https://v6.exchangerate-api.com/v6/YOUR_API_KEY/latest/USD",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('conversion_rates', {}).get('VND', 25500)
        except:
            pass
        
        # Default rate
        return 25500
    
    def update_market_prices(self, product_name: str, manual_data: Optional[Dict] = None) -> bool:
        """Cập nhật giá thị trường vào database"""
        try:
            if product_name == "Cà phê":
                prices = manual_data or self.fetch_coffee_prices()
                
                price_data = {
                    "product_name": "Cà phê",
                    "price_local": prices.get("domestic_gialai", 0),
                    "price_global_london": prices.get("robusta_london", 0),
                    "price_global_ny": prices.get("arabica_ny", 0),
                    "log_date": date.today().isoformat()
                }
                
            elif product_name == "Hồ tiêu":
                prices = manual_data or self.fetch_pepper_prices()
                
                price_data = {
                    "product_name": "Hồ tiêu",
                    "price_local": prices.get("black_pepper", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Điều":
                prices = manual_data or self.fetch_cashew_prices()
                
                price_data = {
                    "product_name": "Điều",
                    "price_local": prices.get("raw_cashew", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Cao su":
                prices = manual_data or self.fetch_rubber_prices()
                
                price_data = {
                    "product_name": "Cao su",
                    "price_local": prices.get("rubber_scr20", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Sắn":
                prices = manual_data or self.fetch_cassava_prices()
                
                price_data = {
                    "product_name": "Sắn",
                    "price_local": prices.get("cassava_chip", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Ngô":
                prices = manual_data or self.fetch_corn_prices()
                
                price_data = {
                    "product_name": "Ngô",
                    "price_local": prices.get("corn_yellow", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Lúa gạo":
                prices = manual_data or self.fetch_rice_prices()
                
                price_data = {
                    "product_name": "Lúa gạo",
                    "price_local": prices.get("rice_ir504", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Cao su":
                prices = manual_data or self.fetch_caosu_prices()
                price_data = {
                    "product_name": "Cao su",
                    "price_local": prices.get("rubber_scr20", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Điều nhân":
                prices = manual_data or self.fetch_dieunhan_prices()
                price_data = {
                    "product_name": "Điều nhân",
                    "price_local": prices.get("cashew_kernel_ws", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Cacao":
                prices = manual_data or self.fetch_cacao_prices()
                price_data = {
                    "product_name": "Cacao",
                    "price_local": prices.get("cacao_bean", 0),
                    "price_global_london": prices.get("global_price", 0),
                    "log_date": date.today().isoformat()
                }
            elif product_name == "Mắc ca":
                prices = manual_data or self.fetch_macca_prices()
                price_data = {
                    "product_name": "Mắc ca",
                    "price_local": prices.get("macca_kernel", 0),
                    "log_date": date.today().isoformat()
                }
            else:
                return False
            
            # Save to database
            result = self.db.add_market_price(price_data)
            logger.info(f"Updated market price for {product_name}: {price_data}")
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating market prices: {e}")
            return False
    
    def update_all_prices(self) -> Dict:
        """Cập nhật tất cả giá thị trường"""
        results = {
            "coffee": self.update_market_prices("Cà phê"),
            "pepper": self.update_market_prices("Hồ tiêu"),
            "cashew": self.update_market_prices("Điều"),
            "cassava": self.update_market_prices("Sắn"),
            "corn": self.update_market_prices("Ngô"),
            "rice": self.update_market_prices("Lúa gạo"),
            "caosu": self.update_market_prices("Cao su"),
            "dieunhan": self.update_market_prices("Điều nhân"),
            "cacao": self.update_market_prices("Cacao"),
            "macca": self.update_market_prices("Mắc ca"),
            "timestamp": datetime.now().isoformat()
        }
        return results
    
    def get_price_analysis(self, product_name: str, days: int = 30) -> Dict:
        """Phân tích giá trong khoảng thời gian"""
        prices = self.db.get_market_prices(product_name, days)
        
        if not prices:
            return {"error": "No data available"}
        
        # Tính toán thống kê
        local_prices = [p.get('price_local', 0) for p in prices if p.get('price_local')]
        
        if not local_prices:
            return {"error": "No price data"}
        
        analysis = {
            "product": product_name,
            "current_price": local_prices[0],
            "avg_price_7d": sum(local_prices[:7]) / min(7, len(local_prices)),
            "avg_price_30d": sum(local_prices) / len(local_prices),
            "min_price": min(local_prices),
            "max_price": max(local_prices),
            "volatility": self.calculate_volatility(local_prices),
            "trend": self.calculate_trend(local_prices),
            "data_points": len(local_prices)
        }
        
        return analysis
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """Tính độ biến động giá"""
        if len(prices) < 2:
            return 0
        
        changes = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                change = abs((prices[i] - prices[i-1]) / prices[i-1]) * 100
                changes.append(change)
        
        return sum(changes) / len(changes) if changes else 0
    
    def calculate_trend(self, prices: List[float]) -> str:
        """Xác định xu hướng giá"""
        if len(prices) < 3:
            return "Chưa đủ dữ liệu"
        
        # So sánh giá hiện tại với trung bình
        current = prices[0]
        avg_7d = sum(prices[:7]) / min(7, len(prices))
        
        if current > avg_7d * 1.02:
            return "📈 Tăng mạnh"
        elif current > avg_7d:
            return "📈 Tăng nhẹ"
        elif current < avg_7d * 0.98:
            return "📉 Giảm mạnh"
        elif current < avg_7d:
            return "📉 Giảm nhẹ"
        else:
            return "➡️ Ổn định"

    def fetch_realtime_coffee(self):
        """Lấy giá cà phê thật từ Giacaphe.com (có fallback robust)"""
        try:
            # Thử phương pháp cũ trước
            price = self.fetcher.fetch_coffee_price()
            if price:
                return {
                    "domestic_gialai": price,
                    "robusta_london": 0,
                    "updated_at": datetime.now().isoformat()
                }
            # Fallback: thử phương pháp robust
            price = self.fetcher.fetch_coffee_price_robust()
            if price:
                logger.info("Lấy giá cà phê thành công (robust fallback)")
                return {
                    "domestic_gialai": price,
                    "robusta_london": 0,
                    "updated_at": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá cà phê: {e}")
            return None

    def fetch_realtime_pepper(self):
        """Lấy giá hồ tiêu từ Tintaynguyen.com (có fallback robust)"""
        try:
            # Thử phương pháp cũ trước
            price = self.fetcher.fetch_pepper_price()
            if price:
                return {
                    "black_pepper": price,
                    "updated_at": datetime.now().isoformat()
                }
            # Fallback: thử phương pháp robust
            price = self.fetcher.fetch_pepper_price_robust()
            if price:
                logger.info("Lấy giá hồ tiêu thành công (robust fallback)")
                return {
                    "black_pepper": price,
                    "updated_at": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy giá hồ tiêu: {e}")
            return None

    def fetch_exchange_rate(self):
        """Lấy tỷ giá USD/VND thật từ API"""
        try:
            # Sử dụng fetcher
            return self.fetcher.fetch_exchange_rate()
        except:
            return 25500

    def sync_to_supabase(self, product_name):
        """Đẩy dữ liệu thật lên Supabase để AI Agent sử dụng"""
        data = None
        if product_name == "Cà phê":
            raw = self.fetch_realtime_coffee()
            if raw:
                data = {
                    "product_name": "Cà phê",
                    "price_local": raw['domestic_gialai'],
                    "price_global_london": raw['robusta_london'],
                    "log_date": date.today().isoformat()
                }
        elif product_name == "Hồ tiêu":
            raw = self.fetch_realtime_pepper()
            if raw:
                data = {
                    "product_name": "Hồ tiêu",
                    "price_local": raw['black_pepper'],
                    "log_date": date.today().isoformat()
                }

        if data:
            result = self.db.add_market_price(data)
            return result
        return None

    # ==================== AUTO-FETCH REAL DATA ====================

    def auto_fetch_latest_data(self) -> Dict[str, Any]:
        """
        Tự động lấy dữ liệu giá thị trường THẬT từ nhiều nguồn web.
        Không dùng dữ liệu mẫu — chỉ dùng dữ liệu thực tế từ chuyên gia.
        
        Quy trình:
          1. Dùng WebMarketResearcher để scrape từ 3+ nguồn
          2. Lưu vào Supabase để AI Agent có thể truy xuất
          3. Trả về kết quả kèm source URLs để trích dẫn
        
        Returns:
            Dict: {
                "success": bool,
                "results": {product: ResearchResult},
                "total_saved": int,
                "citations": str  # Văn bản trích dẫn đầy đủ
            }
        """
        result = {
            "success": False,
            "results": {},
            "total_saved": 0,
            "citations": "",
            "errors": [],
        }

        if WebMarketResearcher is None:
            result["errors"].append("WebMarketResearcher chưa được cài đặt")
            return result

        researcher = WebMarketResearcher()

        # Nghiên cứu giá tất cả sản phẩm — 8 loại
        products_to_fetch = [
            ("Cà phê", researcher.research_coffee),
            ("Hồ tiêu", researcher.research_pepper),
            ("Sầu riêng", researcher.research_durian),
            ("Lúa gạo", researcher.research_rice),
            ("Cao su", researcher.research_caosu),
            ("Điều nhân", researcher.research_dieunhan),
            ("Cacao", researcher.research_cacao),
            ("Mắc ca", researcher.research_macca),
        ]

        saved_count = 0
        for product_name, research_func in products_to_fetch:
            try:
                research_result: ResearchResult = research_func()
                result["results"][product_name] = research_result.to_dict()

                if research_result.best_price():
                    # Lưu giá tốt nhất vào database
                    price_data = {
                        "product_name": product_name,
                        "price_local": research_result.best_price(),
                        "log_date": date.today().isoformat(),
                    }
                    db_result = self.db.add_market_price(price_data)
                    if db_result:
                        saved_count += 1
                        logger.info(
                            f"✅ Đã lưu giá {product_name}: {research_result.best_price():,.0f} VNĐ/kg "
                            f"(nguồn: {research_result.sources[0].source_name if research_result.sources else 'unknown'})"
                        )
                    else:
                        result["errors"].append(f"Không lưu được {product_name} vào DB")
                else:
                    result["errors"].append(
                        f"{product_name}: {research_result.error or 'Không lấy được giá từ web'}"
                    )
            except Exception as e:
                logger.error(f"Lỗi khi fetch {product_name}: {e}")
                result["errors"].append(f"{product_name}: {str(e)}")

        # Tổng hợp citations — làm trực tiếp từ dict, không cần reconstruct object
        citation_lines = []
        for product_name, r in result["results"].items():
            sources = r.get("sources", [])
            for s in sources:
                citation_lines.append(
                    f"{s['product_name']}: {s['price']:,.0f} {s.get('unit', 'VNĐ/kg')} "
                    f"(nguồn: {s['source_name']}, {s['fetched_at']})"
                )

        result["total_saved"] = saved_count
        result["citations"] = "\n".join(citation_lines)
        result["success"] = saved_count > 0

        if saved_count > 0:
            logger.info(f"✅ Auto-fetch: đã lưu {saved_count} bản ghi giá thị trường THẬT")
        else:
            logger.warning("⚠️ Auto-fetch: không lưu được dữ liệu nào từ web")

        return result

    def ensure_real_data_available(self) -> Dict[str, Any]:
        """
        Đảm bảo luôn có dữ liệu thị trường thật trong DB.
        Nếu chưa có dữ liệu hôm nay → tự động fetch từ web.
        
        Returns:
            Dict với kết quả fetch + citation text
        """
        today = date.today().isoformat()
        
        # Kiểm tra đã có dữ liệu hôm nay chưa
        existing_coffee = self.db.get_market_prices("Cà phê", days=1)
        existing_pepper = self.db.get_market_prices("Hồ tiêu", days=1)
        
        has_today_coffee = any(
            e.get("log_date") == today and (e.get("price_local") or 0) > 0
            for e in existing_coffee
        )
        has_today_pepper = any(
            e.get("log_date") == today and (e.get("price_local") or 0) > 0
            for e in existing_pepper
        )
        
        if has_today_coffee and has_today_pepper:
            logger.info("✅ Dữ liệu giá hôm nay đã có sẵn trong DB (dữ liệu thật)")
            return {
                "success": True,
                "message": "Dữ liệu giá hôm nay đã có sẵn",
                "total_saved": 0,
                "citations": "",
            }
        
        # Fetch dữ liệu mới
        return self.auto_fetch_latest_data()


class PriceInputDialog(ctk.CTkToplevel):
    """Dialog nhập giá thủ công"""
    
    def __init__(self, parent, market_manager: MarketDataManager):
        super().__init__(parent)
        self.market_manager = market_manager
        self.title("Nhập giá thị trường")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Thiết lập giao diện nhập giá"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            main_frame,
            text="📊 NHẬP GIÁ THỊ TRƯỜNG",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Coffee section
        coffee_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        coffee_frame.pack(fill="x", pady=(0, 15))
        
        coffee_title = ctk.CTkLabel(
            coffee_frame,
            text="☕ CÀ PHÊ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#8e44ad"
        )
        coffee_title.pack(pady=(10, 10))
        
        # Domestic price
        coffee_local_frame = ctk.CTkFrame(coffee_frame, fg_color="transparent")
        coffee_local_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(coffee_local_frame, text="Giá nội địa (VNĐ/kg):", width=200).pack(side="left")
        self.coffee_local_entry = ctk.CTkEntry(coffee_local_frame, width=200)
        self.coffee_local_entry.pack(side="right")
        
        # London price
        coffee_london_frame = ctk.CTkFrame(coffee_frame, fg_color="transparent")
        coffee_london_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(coffee_london_frame, text="Giá London (USD/ton):", width=200).pack(side="left")
        self.coffee_london_entry = ctk.CTkEntry(coffee_london_frame, width=200)
        self.coffee_london_entry.pack(side="right")
        
        # Pepper section
        pepper_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        pepper_frame.pack(fill="x", pady=(0, 20))
        
        pepper_title = ctk.CTkLabel(
            pepper_frame,
            text="🌶️ HỒ TIÊU",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e67e22"
        )
        pepper_title.pack(pady=(10, 10))
        
        # Black pepper
        pepper_black_frame = ctk.CTkFrame(pepper_frame, fg_color="transparent")
        pepper_black_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(pepper_black_frame, text="Tiêu đen (VNĐ/kg):", width=200).pack(side="left")
        self.pepper_black_entry = ctk.CTkEntry(pepper_black_frame, width=200)
        self.pepper_black_entry.pack(side="right")
        
        # Button frame
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 LƯU DỮ LIỆU",
            command=self.save_prices,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60"
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ HỦY",
            command=self.destroy,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#7f8c8d"
        )
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    def save_prices(self):
        """Lưu giá đã nhập"""
        try:
            # Save coffee prices
            coffee_local = self.coffee_local_entry.get()
            coffee_london = self.coffee_london_entry.get()
            
            if coffee_local:
                coffee_data = {
                    "domestic_gialai": float(coffee_local)
                }
                if coffee_london:
                    coffee_data["robusta_london"] = float(coffee_london)
                
                self.market_manager.update_market_prices("Cà phê", coffee_data)
            
            # Save pepper prices
            pepper_black = self.pepper_black_entry.get()
            if pepper_black:
                pepper_data = {"black_pepper": float(pepper_black)}
                self.market_manager.update_market_prices("Hồ tiêu", pepper_data)
            
            messagebox.showinfo("Thành công", "Đã cập nhật giá thị trường!")
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi lưu dữ liệu: {e}")