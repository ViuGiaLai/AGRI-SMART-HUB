# -*- coding: utf-8 -*-
# ui/report_frame.py
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from core.report_manager import ReportManager
from ui import theme as T


class ReportFrame(ctk.CTkFrame):
    """Báo cáo & Thống kê"""

    def __init__(self, master, db_manager, user_id, **kwargs):
        super().__init__(master, fg_color=T.BG_MAIN, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.report_manager = ReportManager(db_manager, user_id)
        self.setup_ui()

    def setup_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(
            hdr, text="Báo cáo & Thống kê",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="Xuất Excel / PDF chỉ vài giây",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0))

        # Grid 2×2 thẻ báo cáo
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=24, pady=(8, 24))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        reports = [
            {
                "icon": "📊",
                "title": "Giao dịch thu mua",
                "desc": "Toàn bộ lịch sử giao dịch\nvới chi tiết cân đo, đơn giá",
                "btn": "Xuất Excel",
                "command": self._export_transactions,
                "color": T.PRIMARY,
            },
            {
                "icon": "📈",
                "title": "Doanh thu",
                "desc": "Thống kê doanh thu\ntheo sản phẩm và theo tháng",
                "btn": "Xuất Excel",
                "command": self._export_revenue,
                "color": T.INFO if hasattr(T, "INFO") else "#3498db",
            },
            {
                "icon": "👨‍🌾",
                "title": "Danh sách nông dân",
                "desc": "Thông tin và công nợ\ncủa tất cả nông dân",
                "btn": "Xuất Excel",
                "command": self._export_farmers,
                "color": T.ACCENT if hasattr(T, "ACCENT") else "#f39c12",
            },
            {
                "icon": "📦",
                "title": "Tồn kho sản phẩm",
                "desc": "Khối lượng hiện có trong kho\ntheo từng loại nông sản",
                "btn": "Xuất Excel",
                "command": self._export_products,
                "color": T.SECONDARY,
            },
        ]

        for i, r in enumerate(reports):
            row, col = divmod(i, 2)
            self._build_report_card(grid, r, row, col)

        # Nút PDF riêng phía dưới
        pdf_frame = ctk.CTkFrame(self, fg_color="transparent")
        pdf_frame.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(
            pdf_frame,
            text="📄  Xuất Báo Cáo Tổng Hợp PDF",
            command=self._export_pdf,
            height=50,
            corner_radius=T.CORNER_RADIUS,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=T.DANGER if hasattr(T, "DANGER") else "#e74c3c",
            hover_color="#c0392b",
        ).pack(fill="x")

    def _build_report_card(self, parent, config: dict, row: int, col: int):
        """Tạo một thẻ báo cáo."""
        card = ctk.CTkFrame(
            parent, corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD,
            border_width=1, border_color=config["color"],
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(
            card, text=config["icon"],
            font=ctk.CTkFont(size=36),
        ).pack(pady=(24, 6))

        ctk.CTkLabel(
            card, text=config["title"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=T.TEXT_DARK,
        ).pack()

        ctk.CTkLabel(
            card, text=config["desc"],
            font=ctk.CTkFont(size=12),
            text_color=T.TEXT_MUTED,
            justify="center",
        ).pack(pady=(6, 16))

        ctk.CTkButton(
            card,
            text=f"📥  {config['btn']}",
            command=config["command"],
            width=160, height=40,
            corner_radius=T.CORNER_RADIUS_SM,
            fg_color=config["color"],
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(0, 24))

    # ──────────────────────────────────────────────
    # HANDLERS — gọi đúng tên method trong ReportManager
    # ──────────────────────────────────────────────
    def _export_transactions(self):
        try:
            self.report_manager.export_transactions_to_excel()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo giao dịch:\n{e}")

    def _export_revenue(self):
        try:
            self.report_manager.export_revenue_report()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo doanh thu:\n{e}")

    def _export_farmers(self):
        try:
            self.report_manager.export_farmers_to_excel()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất danh sách nông dân:\n{e}")

    def _export_products(self):
        try:
            self.report_manager.export_products_to_excel()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo tồn kho:\n{e}")

    def _export_pdf(self):
        try:
            self.report_manager.export_full_report_to_pdf()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất PDF:\n{e}")