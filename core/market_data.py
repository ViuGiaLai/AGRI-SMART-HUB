# -*- coding: utf-8 -*-
# core/market_data.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import Dict, Optional, List
import json
import logging
import os
import customtkinter as ctk
from dotenv import load_dotenv
from database.db_manager import DatabaseManager

load_dotenv()

logger = logging.getLogger(__name__)

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
            "rubber": self.update_market_prices("Cao su"),
            "cassava": self.update_market_prices("Sắn"),
            "corn": self.update_market_prices("Ngô"),
            "rice": self.update_market_prices("Lúa gạo"),
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
        """Lấy giá cà phê thật từ Giacaphe.com"""
        try:
            # Sử dụng fetcher
            price = self.fetcher.fetch_coffee_price()
            if price:
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
        """Lấy giá hồ tiêu từ Tintaynguyen.com"""
        try:
            # Sử dụng fetcher
            price = self.fetcher.fetch_pepper_price()
            if price:
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