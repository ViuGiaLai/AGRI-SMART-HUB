# -*- coding: utf-8 -*-
# ui/report_frame.py
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from core.report_manager import ReportManager


class ReportFrame(ctk.CTkFrame):
    """Báo cáo & Thống kê"""

    def __init__(self, master, db_manager, user_id, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.report_manager = ReportManager(db_manager, user_id)

        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header with consistent style
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#2ecc71", "#1a5d1a"))
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            self.header_frame,
            text="📄 BÁO CÁO & THỐNG KÊ",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        title.pack(pady=15)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Report options
        reports = [
            {"icon": "📊", "title": "Báo cáo giao dịch", "desc": "Xuất Excel danh sách giao dịch", "command": self.export_transactions},
            {"icon": "📈", "title": "Báo cáo doanh thu", "desc": "Xuất Excel doanh thu theo thời gian", "command": self.export_revenue},
            {"icon": "👨‍🌾", "title": "Báo cáo nông dân", "desc": "Xuất Excel thông tin nông dân", "command": self.export_farmers},
            {"icon": "📦", "title": "Báo cáo sản phẩm", "desc": "Xuất Excel tồn kho sản phẩm", "command": self.export_products},
        ]

        for i, report in enumerate(reports):
            row = i // 2
            col = i % 2

            card = ctk.CTkFrame(main_frame, corner_radius=15)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            icon_label = ctk.CTkLabel(
                card,
                text=report["icon"],
                font=ctk.CTkFont(size=36)
            )
            icon_label.pack(pady=(20, 10))

            title_label = ctk.CTkLabel(
                card,
                text=report["title"],
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack()

            desc_label = ctk.CTkLabel(
                card,
                text=report["desc"],
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            desc_label.pack(pady=(5, 15))

            export_btn = ctk.CTkButton(
                card,
                text="📥 Xuất Excel",
                command=report["command"],
                width=150
            )
            export_btn.pack(pady=(0, 20))

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

    def export_transactions(self):
        """Xuất báo cáo giao dịch"""
        try:
            result = self.report_manager.export_transactions_to_excel()
            if result:
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo!\n{result}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {e}")

    def export_revenue(self):
        """Xuất báo cáo doanh thu"""
        try:
            result = self.report_manager.export_revenue_report()
            if result:
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo!\n{result}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {e}")

    def export_farmers(self):
        """Xuất báo cáo nông dân"""
        try:
            result = self.report_manager.export_farmers_to_excel()
            if result:
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo!\n{result}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {e}")

    def export_products(self):
        """Xuất báo cáo sản phẩm"""
        try:
            result = self.report_manager.export_products_to_excel()
            if result:
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo!\n{result}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {e}")