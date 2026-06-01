# -*- coding: utf-8 -*-
# ui/dashboard.py (hoàn thiện)
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from database.db_manager import DatabaseManager

class DashboardFrame(ctk.CTkFrame):
    """Dashboard tổng quan với biểu đồ thống kê"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db_manager = db_manager
        self.user_id = user_id
        
        self.setup_ui()
        self.load_dashboard_data()
    
    def setup_ui(self):
        """Thiết lập giao diện dashboard"""
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#2ecc71", "#1a5d1a"))
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📊 TỔNG QUAN HỆ THỐNG",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(pady=15)
        
        # Stats cards frame
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.create_stat_cards()
        
        # Charts frame
        self.charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.create_charts()
        
        # Recent transactions frame
        self.recent_frame = ctk.CTkFrame(self, corner_radius=15)
        self.recent_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.create_recent_transactions()
    
    def create_stat_cards(self):
        """Tạo các thẻ thống kê"""
        # Configure grid
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)
        
        # Card 1: Total farmers
        self.farmer_card = self.create_stat_card(
            self.stats_frame, 0, 0,
            "👨‍🌾", "Tổng số nông dân", "0", "#3498db"
        )
        
        # Card 2: Total debt
        self.debt_card = self.create_stat_card(
            self.stats_frame, 0, 1,
            "💰", "Tổng công nợ", "0 VNĐ", "#e74c3c"
        )
        
        # Card 3: Monthly revenue
        self.revenue_card = self.create_stat_card(
            self.stats_frame, 0, 2,
            "📈", "Doanh thu tháng này", "0 VNĐ", "#27ae60"
        )
        
        # Card 4: Total stock
        self.stock_card = self.create_stat_card(
            self.stats_frame, 0, 3,
            "📦", "Tổng tồn kho", "0 kg", "#f39c12"
        )
    
    def create_stat_card(self, parent, row, col, icon, title, value, color):
        """Tạo một thẻ thống kê"""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=("white", "#2b2b2b"))
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        icon_label = ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 32))
        icon_label.pack(pady=(10, 5))
        
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray")
        title_label.pack()
        
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=(5, 10))
        
        return {"card": card, "value_label": value_label}
    
    def create_charts(self):
        """Tạo biểu đồ"""
        # Configure grid
        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_columnconfigure(1, weight=1)
        
        # Chart 1: Monthly revenue chart
        self.revenue_chart_frame = ctk.CTkFrame(self.charts_frame, corner_radius=10)
        self.revenue_chart_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        revenue_title = ctk.CTkLabel(
            self.revenue_chart_frame,
            text="📊 DOANH THU THEO THÁNG",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        revenue_title.pack(pady=10)
        
        # Chart 2: Product distribution
        self.product_chart_frame = ctk.CTkFrame(self.charts_frame, corner_radius=10)
        self.product_chart_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        product_title = ctk.CTkLabel(
            self.product_chart_frame,
            text="🥧 TỶ LỆ SẢN PHẨM",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        product_title.pack(pady=10)
        
        # Chart 3: Weekly trend
        self.trend_frame = ctk.CTkFrame(self.charts_frame, corner_radius=10)
        self.trend_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        trend_title = ctk.CTkLabel(
            self.trend_frame,
            text="📈 XU HƯỚNG GIÁ CÀ PHÊ 7 NGÀY QUA",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        trend_title.pack(pady=10)
    
    def create_recent_transactions(self):
        """Tạo bảng giao dịch gần đây"""
        recent_title = ctk.CTkLabel(
            self.recent_frame,
            text="🕐 GIAO DỊCH GẦN ĐÂY",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        recent_title.pack(pady=10)
        
        # Treeview for recent transactions
        from tkinter import ttk
        self.recent_tree_frame = ctk.CTkFrame(self.recent_frame)
        self.recent_tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(self.recent_tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Ngày", "Nông dân", "Sản phẩm", "Cân tịnh(kg)", "Thành tiền(VNĐ)", "Trạng thái")
        self.recent_tree = ttk.Treeview(
            self.recent_tree_frame,
            columns=columns,
            show="headings",
            height=8,
            yscrollcommand=scrollbar.set
        )
        
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=120)
        
        self.recent_tree.column("Ngày", width=100)
        self.recent_tree.column("Nông dân", width=150)
        self.recent_tree.column("Sản phẩm", width=120)
        self.recent_tree.column("Thành tiền(VNĐ)", width=150)
        
        self.recent_tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.recent_tree.yview)
    
    def load_dashboard_data(self):
        """Tải dữ liệu cho dashboard"""
        # Load statistics
        stats = self.db_manager.get_dashboard_stats(self.user_id)
        
        # Update stat cards
        self.farmer_card["value_label"].configure(text=str(stats.get('total_farmers', 0)))
        self.debt_card["value_label"].configure(text=f"{stats.get('total_debt', 0):,.0f} VNĐ")
        self.stock_card["value_label"].configure(text=f"{stats.get('total_stock', 0):,.0f} kg")
        
        # Load monthly revenue
        monthly_revenue = self.calculate_monthly_revenue()
        self.revenue_card["value_label"].configure(text=f"{monthly_revenue:,.0f} VNĐ")
        
        # Create charts
        self.create_revenue_chart()
        self.create_product_chart()
        self.create_price_trend_chart()
        
        # Load recent transactions
        self.load_recent_transactions()
    
    def calculate_monthly_revenue(self):
        """Tính doanh thu tháng này"""
        # Get current month
        now = datetime.now()
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        transactions = self.db_manager.get_transactions(
            self.user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        total_revenue = sum(t.get('total_amount', 0) for t in transactions)
        return total_revenue
    
    def create_revenue_chart(self):
        """Tạo biểu đồ doanh thu"""
        # Get last 6 months data
        months = []
        revenues = []
        
        for i in range(5, -1, -1):
            date = datetime.now() - timedelta(days=30*i)
            month_name = date.strftime("%m/%Y")
            months.append(month_name)
            
            # Get revenue for that month
            start_date = date.replace(day=1).strftime("%Y-%m-%d")
            end_date = (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            end_date = end_date.strftime("%Y-%m-%d")
            
            transactions = self.db_manager.get_transactions(
                self.user_id,
                start_date=start_date,
                end_date=end_date
            )
            monthly_revenue = sum(t.get('total_amount', 0) for t in transactions)
            revenues.append(monthly_revenue / 1_000_000)  # Convert to millions
        
        # Clear previous chart
        for widget in self.revenue_chart_frame.winfo_children():
            if widget != self.revenue_chart_frame.winfo_children()[0]:
                widget.destroy()
        
        # Create figure
        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        bars = ax.bar(months, revenues, color='#27ae60', alpha=0.7)
        ax.set_xlabel('Tháng')
        ax.set_ylabel('Doanh thu (Triệu VNĐ)')
        ax.set_title('Doanh thu theo tháng')
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, revenue in zip(bars, revenues):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{revenue:.1f}M', ha='center', va='bottom')
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.revenue_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def create_product_chart(self):
        """Tạo biểu đồ tròn tỷ lệ sản phẩm"""
        # Get product distribution
        transactions = self.db_manager.get_transactions(self.user_id)
        
        product_weights = {}
        for trans in transactions:
            product_name = trans.get('products', {}).get('name', 'Khác')
            net_weight = trans.get('net_weight', 0)
            product_weights[product_name] = product_weights.get(product_name, 0) + net_weight
        
        # Clear previous chart
        for widget in self.product_chart_frame.winfo_children():
            if widget != self.product_chart_frame.winfo_children()[0]:
                widget.destroy()
        
        if not product_weights:
            no_data_label = ctk.CTkLabel(
                self.product_chart_frame,
                text="Chưa có dữ liệu",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_data_label.pack(expand=True)
            return
        
        # Create figure
        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        products = list(product_weights.keys())
        weights = list(product_weights.values())
        colors = ['#27ae60', '#3498db', '#e74c3c', '#f39c12', '#9b59b6']
        
        wedges, texts, autotexts = ax.pie(
            weights,
            labels=products,
            autopct='%1.1f%%',
            colors=colors[:len(products)],
            startangle=90
        )
        
        ax.set_title('Tỷ lệ sản lượng theo sản phẩm')
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.product_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def create_price_trend_chart(self):
        """Tạo biểu đồ xu hướng giá"""
        # Get market prices for coffee
        market_prices = self.db_manager.get_market_prices("cà phê", days=7)
        
        # Clear previous chart
        for widget in self.trend_frame.winfo_children():
            if widget != self.trend_frame.winfo_children()[0]:
                widget.destroy()
        
        if not market_prices:
            no_data_label = ctk.CTkLabel(
                self.trend_frame,
                text="Chưa có dữ liệu giá thị trường",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_data_label.pack(expand=True)
            return
        
        # Prepare data
        dates = []
        prices = []
        
        for price in market_prices:
            dates.append(price['log_date'])
            prices.append(price.get('price_local', 0))
        
        # Create figure
        fig = Figure(figsize=(10, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        ax.plot(dates, prices, marker='o', linewidth=2, markersize=8, color='#e74c3c')
        ax.fill_between(dates, prices, alpha=0.3, color='#e74c3c')
        ax.set_xlabel('Ngày')
        ax.set_ylabel('Giá (VNĐ/kg)')
        ax.set_title('Xu hướng giá cà phê 7 ngày qua')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add value labels
        for i, (date, price) in enumerate(zip(dates, prices)):
            ax.annotate(f'{price:,.0f}', (date, price), 
                       textcoords="offset points", xytext=(0,10), 
                       ha='center', fontsize=9)
        
        fig.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.trend_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def load_recent_transactions(self):
        """Tải giao dịch gần đây"""
        transactions = self.db_manager.get_transactions(self.user_id)
        
        # Clear existing
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        # Show last 10 transactions
        for trans in transactions[:10]:
            farmer_name = trans.get('farmers', {}).get('name', 'N/A')[:20]
            product_name = trans.get('products', {}).get('name', 'N/A')[:15]
            payment_status = "✅ Đã trả" if trans['payment_status'] == 'paid' else "📝 Ghi nợ"
            
            self.recent_tree.insert("", "end", values=(
                trans['created_at'][:10] if trans.get('created_at') else '',
                farmer_name,
                product_name,
                f"{trans['net_weight']:,.1f}",
                f"{trans['total_amount']:,.0f}",
                payment_status
            ))