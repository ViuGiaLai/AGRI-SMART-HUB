# -*- coding: utf-8 -*-
"""Dashboard — Digital Forest & Wealth layout."""
import customtkinter as ctk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database.db_manager import DatabaseManager
from ui import theme as T


class DashboardFrame(ctk.CTkFrame):
    """Dashboard tổng quan: 4 thẻ KPI, biểu đồ giá, hoạt động gần đây."""

    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, fg_color=T.BG_MAIN, **kwargs)
        self.db_manager = db_manager
        self.user_id = user_id
        self.stat_cards = {}
        self.setup_ui()
        self.load_dashboard_data()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Page title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=T.TEXT_DARK,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Tổng quan hoạt động đại lý",
            font=ctk.CTkFont(size=13),
            text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0))

        # Slot cho widget cảnh báo (NotificationSystem)
        self.alerts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.alerts_container.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 4))

        # 4 KPI cards
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=8)
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        specs = [
            ("stock", "📦", "Tổng tồn kho", "0 kg", T.CARD_STOCK),
            ("debt", "💰", "Tổng nợ", "0 VNĐ", T.CARD_DEBT),
            ("revenue", "📈", "Doanh thu tháng", "0 VNĐ", T.CARD_REVENUE),
            ("coffee_price", "☕", "Giá cà phê hôm nay", "— VNĐ/kg", T.CARD_PRICE),
        ]
        for col, (key, icon, title, default, color) in enumerate(specs):
            self.stat_cards[key] = self._create_stat_card(
                self.stats_frame, col, icon, title, default, color
            )

        # Middle: chart (left) + activity (right)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=3, column=0, sticky="nsew", padx=24, pady=(8, 24))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.chart_card = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD
        )
        self.chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            self.chart_card,
            text="📈 Xu hướng giá cà phê — 7 ngày qua",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=T.TEXT_DARK,
        ).pack(anchor="w", padx=20, pady=(16, 8))
        self.chart_container = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.activity_card = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD
        )
        self.activity_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(
            self.activity_card,
            text="🕐 Hoạt động gần đây",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=T.TEXT_DARK,
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.activity_scroll = ctk.CTkScrollableFrame(
            self.activity_card, fg_color="transparent", corner_radius=T.CORNER_RADIUS_SM
        )
        self.activity_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 16))

    def _create_stat_card(self, parent, col, icon, title, value, accent):
        card = ctk.CTkFrame(
            parent,
            corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=("#e8eaed", "#3d3d3d"),
        )
        card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")

        accent_bar = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=accent)
        accent_bar.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=icon, font=("Segoe UI Emoji", 28)).pack(side="left")
        ctk.CTkLabel(
            top,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(10, 0))

        value_label = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=accent,
            anchor="w",
        )
        value_label.pack(anchor="w", pady=(10, 0))
        return value_label

    def load_dashboard_data(self):
        stats = self.db_manager.get_dashboard_stats(self.user_id)
        self.stat_cards["stock"].configure(
            text=f"{stats.get('total_stock', 0):,.0f} kg"
        )
        self.stat_cards["debt"].configure(
            text=f"{stats.get('total_debt', 0):,.0f} VNĐ"
        )
        monthly = self._monthly_revenue()
        self.stat_cards["revenue"].configure(text=f"{monthly:,.0f} VNĐ")

        coffee_price = self._today_coffee_price()
        self.stat_cards["coffee_price"].configure(
            text=f"{coffee_price:,.0f} VNĐ/kg" if coffee_price else "— VNĐ/kg"
        )

        self._draw_price_chart()
        self._load_recent_activity()

    def _monthly_revenue(self):
        now = datetime.now()
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        txs = self.db_manager.get_transactions(
            self.user_id, start_date=start, end_date=end
        )
        return sum(t.get("total_amount", 0) for t in txs)

    def _today_coffee_price(self):
        prices = self.db_manager.get_market_prices("cà phê", days=1)
        if prices:
            return prices[0].get("price_local", 0) or 0
        prices = self.db_manager.get_market_prices("cà phê", days=7)
        return prices[0].get("price_local", 0) if prices else 0

    def _draw_price_chart(self):
        for w in self.chart_container.winfo_children():
            w.destroy()

        market_prices = self.db_manager.get_market_prices("cà phê", days=7)
        if not market_prices:
            ctk.CTkLabel(
                self.chart_container,
                text="Chưa có dữ liệu giá thị trường",
                text_color=T.TEXT_MUTED,
            ).pack(expand=True)
            return

        dates, prices = [], []
        for row in reversed(market_prices):
            dates.append(str(row.get("log_date", ""))[:10])
            prices.append(row.get("price_local", 0) or 0)

        fig = Figure(figsize=(7, 3.2), dpi=100, facecolor="none")
        ax = fig.add_subplot(111)
        ax.set_facecolor("none")
        ax.plot(
            dates, prices,
            color=T.PRIMARY, linewidth=2.5, marker="o",
            markersize=7, markerfacecolor=T.ACCENT,
        )
        ax.fill_between(range(len(prices)), prices, alpha=0.12, color=T.PRIMARY)
        ax.set_ylabel("VNĐ/kg", fontsize=9, color="#555")
        ax.tick_params(axis="both", labelsize=8)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _load_recent_activity(self):
        for w in self.activity_scroll.winfo_children():
            w.destroy()

        transactions = self.db_manager.get_transactions(self.user_id)[:12]
        if not transactions:
            ctk.CTkLabel(
                self.activity_scroll,
                text="Chưa có hoạt động",
                text_color=T.TEXT_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return

        for trans in transactions:
            farmer = trans.get("farmers", {}).get("name", "N/A")
            product = trans.get("products", {}).get("name", "nông sản")
            net = trans.get("net_weight", 0) or 0
            amount = trans.get("total_amount", 0) or 0
            paid = trans.get("payment_status") == "paid"
            icon = "✅" if paid else "📝"
            text = f"{icon} Nhập {net:,.0f}kg {product} từ {farmer}"
            sub = f"{amount:,.0f} VNĐ · {str(trans.get('created_at', ''))[:10]}"

            row = ctk.CTkFrame(
                self.activity_scroll,
                corner_radius=T.CORNER_RADIUS_SM,
                fg_color=("#f8f9fa", "#333333"),
            )
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text=text, font=ctk.CTkFont(size=12),
                text_color=T.TEXT_DARK, anchor="w", wraplength=220,
            ).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(
                row, text=sub, font=ctk.CTkFont(size=10),
                text_color=T.TEXT_MUTED,
            ).pack(anchor="w", padx=12, pady=(0, 8))
