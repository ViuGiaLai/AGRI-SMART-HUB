# -*- coding: utf-8 -*-
# ui/market_frame.py
import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from PIL import Image
from database.db_manager import DatabaseManager
from core.market_data import MarketDataManager


class MarketFrame(ctk.CTkFrame):
    """Quản lý dữ liệu thị trường"""

    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.market_manager = MarketDataManager(db_manager)

        self.setup_ui()
        self.load_market_data()

    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#e67e22", "#a85c1a"))
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        # Logo + Title
        header_content = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_content.pack()
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "GASH-VIU.png")
            logo_img = ctk.CTkImage(Image.open(logo_path), size=(32, 32))
            ctk.CTkLabel(header_content, image=logo_img, text="").pack(side="left", padx=(0, 10))
        except:
            ctk.CTkLabel(header_content, text="📈", font=ctk.CTkFont(size=24)).pack(side="left", padx=(0, 10))

        self.title_label = ctk.CTkLabel(
            header_content,
            text="DỮ LIỆU THỊ TRƯỜNG",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(side="left")

        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Fetch data
        self.left_panel = ctk.CTkFrame(self.main_container, width=400, corner_radius=15)
        self.left_panel.pack(side="left", fill="both", padx=(0, 10), pady=10)
        self.left_panel.pack_propagate(False)

        # Right panel - History
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)

        self.create_fetch_panel()
        self.create_history_panel()

    def create_fetch_panel(self):
        """Tạo panel lấy dữ liệu"""
        # Title
        fetch_title = ctk.CTkLabel(
            self.left_panel,
            text="📥 NẠP DỮ LIỆU THỊ TRƯỜNG",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        fetch_title.pack(pady=(20, 15))

        # Coffee section
        coffee_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        coffee_frame.pack(fill="x", padx=20, pady=10)

        coffee_title = ctk.CTkLabel(
            coffee_frame,
            text="☕ CÀ PHÊ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#8e44ad"
        )
        coffee_title.pack(pady=(10, 10))

        self.coffee_btn = ctk.CTkButton(
            coffee_frame,
            text="🌐 Lấy giá từ Giacaphe.com",
            command=self.fetch_coffee_prices,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.coffee_btn.pack(pady=(0, 10), padx=20, fill="x")

        self.coffee_status = ctk.CTkLabel(
            coffee_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.coffee_status.pack(pady=(0, 10))

        # Pepper section
        pepper_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        pepper_frame.pack(fill="x", padx=20, pady=10)

        pepper_title = ctk.CTkLabel(
            pepper_frame,
            text="🌶️ HỒ TIÊU",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        )
        pepper_title.pack(pady=(10, 10))

        self.pepper_btn = ctk.CTkButton(
            pepper_frame,
            text="🌐 Lấy giá từ Tintaynguyen.com",
            command=self.fetch_pepper_prices,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.pepper_btn.pack(pady=(0, 10), padx=20, fill="x")

        self.pepper_status = ctk.CTkLabel(
            pepper_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.pepper_status.pack(pady=(0, 10))

        # Cashew section
        cashew_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        cashew_frame.pack(fill="x", padx=20, pady=10)

        cashew_title = ctk.CTkLabel(
            cashew_frame,
            text="🥜 ĐIỀU",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#d35400"
        )
        cashew_title.pack(pady=(10, 10))

        self.cashew_btn = ctk.CTkButton(
            cashew_frame,
            text="🌐 Lấy giá từ web",
            command=self.fetch_cashew_prices,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.cashew_btn.pack(pady=(0, 10), padx=20, fill="x")

        self.cashew_status = ctk.CTkLabel(
            cashew_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.cashew_status.pack(pady=(0, 10))

        # Rubber section
        rubber_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        rubber_frame.pack(fill="x", padx=20, pady=10)

        rubber_title = ctk.CTkLabel(
            rubber_frame,
            text="🌳 CAO SU",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#27ae60"
        )
        rubber_title.pack(pady=(10, 10))

        self.rubber_btn = ctk.CTkButton(
            rubber_frame,
            text="🌐 Lấy giá từ web",
            command=self.fetch_rubber_prices,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.rubber_btn.pack(pady=(0, 10), padx=20, fill="x")

        self.rubber_status = ctk.CTkLabel(
            rubber_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.rubber_status.pack(pady=(0, 10))

        # Manual input
        manual_frame = ctk.CTkFrame(self.left_panel, corner_radius=10)
        manual_frame.pack(fill="x", padx=20, pady=10)

        manual_title = ctk.CTkLabel(
            manual_frame,
            text="✏️ NHẬP THỦ CÔNG",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        manual_title.pack(pady=(10, 10))

        # Coffee price input
        ctk.CTkLabel(manual_frame, text="Giá cà phê (VNĐ/kg):").pack(anchor="w", padx=20, pady=(5, 0))
        self.coffee_entry = ctk.CTkEntry(manual_frame, height=35)
        self.coffee_entry.pack(fill="x", padx=20, pady=5)

        # Pepper price input
        ctk.CTkLabel(manual_frame, text="Giá hồ tiêu (VNĐ/kg):").pack(anchor="w", padx=20, pady=(5, 0))
        self.pepper_entry = ctk.CTkEntry(manual_frame, height=35)
        self.pepper_entry.pack(fill="x", padx=20, pady=5)

        self.save_manual_btn = ctk.CTkButton(
            manual_frame,
            text="💾 LƯU GIÁ THỦ CÔNG",
            command=self.save_manual_prices,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60"
        )
        self.save_manual_btn.pack(pady=10, padx=20, fill="x")

    def create_history_panel(self):
        """Tạo panel lịch sử"""
        # Title
        history_title = ctk.CTkLabel(
            self.right_panel,
            text="📊 LỊCH SỬ GIÁ",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        history_title.pack(pady=(20, 15))

        # Filter
        filter_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(filter_frame, text="Sản phẩm:").pack(side="left", padx=(0, 10))

        self.product_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Tất cả", "Cà phê", "Hồ tiêu", "Điều", "Cao su", "Sắn", "Ngô", "Lúa gạo"],
            command=self.filter_history,
            width=150
        )
        self.product_filter.set("Tất cả")
        self.product_filter.pack(side="left", padx=(0, 10))

        self.refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄",
            command=self.load_market_data,
            width=40
        )
        self.refresh_btn.pack(side="right")

        # Treeview
        self.tree_frame = ctk.CTkFrame(self.right_panel)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        import tkinter.ttk as ttk
        scrollbar = ttk.Scrollbar(self.tree_frame)
        scrollbar.pack(side="right", fill="y")

        columns = ("Ngày", "Sản phẩm", "Giá nội địa", "Giá London")
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show="headings",
            height=15,
            yscrollcommand=scrollbar.set
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.column("Sản phẩm", width=100)
        self.tree.column("Giá nội địa", width=150)
        self.tree.column("Giá London", width=150)

        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

    def fetch_coffee_prices(self):
        """Lấy giá cà phê từ web"""
        self.coffee_status.configure(text="⏳ Đang tải...")
        self.update()

        try:
            result = self.market_manager.fetch_realtime_coffee()
            if result:
                self.market_manager.sync_to_supabase("Cà phê")
                self.coffee_status.configure(text=f"✅ Đã cập nhật: {result.get('domestic_gialai', 0):,} VNĐ")
                self.load_market_data()
            else:
                self.coffee_status.configure(text="❌ Lỗi tải dữ liệu")
        except Exception as e:
            self.coffee_status.configure(text=f"❌ Lỗi: {str(e)}")

    def fetch_pepper_prices(self):
        """Lấy giá hồ tiêu từ web"""
        self.pepper_status.configure(text="⏳ Đang tải...")
        self.update()

        try:
            result = self.market_manager.fetch_realtime_pepper()
            if result:
                self.market_manager.sync_to_supabase("Hồ tiêu")
                self.pepper_status.configure(text=f"✅ Đã cập nhật: {result.get('black_pepper', 0):,} VNĐ")
                self.load_market_data()
            else:
                self.pepper_status.configure(text="❌ Lỗi tải dữ liệu")
        except Exception as e:
            self.pepper_status.configure(text=f"❌ Lỗi: {str(e)}")

    def fetch_cashew_prices(self):
        """Lấy giá điều từ web"""
        self.cashew_status.configure(text="⏳ Đang tải...")
        self.update()

        try:
            result = self.market_manager.fetch_cashew_prices()
            if result:
                self.market_manager.sync_to_supabase("Điều")
                self.cashew_status.configure(text=f"✅ Đã cập nhật: {result.get('raw_cashew', 0):,} VNĐ")
                self.load_market_data()
            else:
                self.cashew_status.configure(text="❌ Lỗi tải dữ liệu")
        except Exception as e:
            self.cashew_status.configure(text=f"❌ Lỗi: {str(e)}")

    def fetch_rubber_prices(self):
        """Lấy giá cao su từ web"""
        self.rubber_status.configure(text="⏳ Đang tải...")
        self.update()

        try:
            result = self.market_manager.fetch_rubber_prices()
            if result:
                self.market_manager.sync_to_supabase("Cao su")
                self.rubber_status.configure(text=f"✅ Đã cập nhật: {result.get('rubber_scr20', 0):,} VNĐ")
                self.load_market_data()
            else:
                self.rubber_status.configure(text="❌ Lỗi tải dữ liệu")
        except Exception as e:
            self.rubber_status.configure(text=f"❌ Lỗi: {str(e)}")

    def save_manual_prices(self):
        """Lưu giá thủ công"""
        coffee_price = self.coffee_entry.get().strip()
        pepper_price = self.pepper_entry.get().strip()

        if coffee_price:
            try:
                self.market_manager.update_market_prices("Cà phê", {"domestic_gialai": float(coffee_price)})
            except ValueError:
                messagebox.showerror("Lỗi", "Giá cà phê phải là số!")
                return

        if pepper_price:
            try:
                self.market_manager.update_market_prices("Hồ tiêu", {"black_pepper": float(pepper_price)})
            except ValueError:
                messagebox.showerror("Lỗi", "Giá hồ tiêu phải là số!")
                return

        messagebox.showinfo("Thành công", "Đã lưu giá thị trường!")
        self.coffee_entry.delete(0, "end")
        self.pepper_entry.delete(0, "end")
        self.load_market_data()

    def load_market_data(self):
        """Tải dữ liệu thị trường"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        products = ["Cà phê", "Hồ tiêu", "Điều", "Cao su", "Sắn", "Ngô", "Lúa gạo"]

        try:
            for product in products:
                prices = self.db.get_market_prices(product, 30)
                if prices:
                    for p in prices:
                        self.tree.insert("", "end", values=(
                            p.get('log_date', '')[:10] if p.get('log_date') else '',
                            p.get('product_name', ''),
                            f"{p.get('price_local', 0):,.0f}",
                            f"{p.get('price_global_london', 0):,.0f}" if p.get('price_global_london') else ''
                        ))
        except Exception as e:
            print(f"Lỗi tải dữ liệu: {e}")

    def filter_history(self, choice=None):
        """Lọc lịch sử theo sản phẩm"""
        # Reload data with filter
        self.load_market_data()