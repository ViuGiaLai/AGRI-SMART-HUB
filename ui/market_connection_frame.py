# -*- coding: utf-8 -*-
"""
ui/market_connection_frame.py — Giao diện Kết nối Thị trường Nông sản.

Hiển thị:
  - Thống kê tổng quan (đối tác, tỉnh thành)
  - Danh mục kết nối (dạng card)
  - Đối tác nổi bật
  - Nút đăng ký / liên hệ
"""

import os
import webbrowser
import logging
from datetime import datetime
from typing import Optional

import customtkinter as ctk
from PIL import Image

from core.market_connection import (
    MarketConnectionManager,
    ConnectionCategory,
    FeaturedPartner,
    ConnectionData,
)
from ui import theme as T

logger = logging.getLogger(__name__)


class MarketConnectionFrame(ctk.CTkFrame):
    """
    Frame hiển thị Kết nối Thị trường Nông sản toàn quốc.
    Giao diện card hiện đại, dễ nhìn.
    """

    # Màu sắc cho từng danh mục
    CATEGORY_COLORS = {
        "Phân bón & Vật tư":     ("#27ae60", "#1e8449"),  # xanh lá
        "Đại lý thu mua":        ("#3498db", "#2874a6"),  # xanh dương
        "Máy móc nông cụ":       ("#e67e22", "#ca6f1e"),  # cam
        "Giống cây trồng":       ("#2ecc71", "#28b463"),  # xanh lá sáng
        "Doanh nghiệp XK":       ("#9b59b6", "#7d3c98"),  # tím
        "Tài chính - Vay vốn":   ("#f1c40f", "#d4ac0d"),  # vàng
    }

    PARTNER_COLORS = {
        "Agribank":       ("#e74c3c", "#c0392b"),  # đỏ
        "Đầu Trâu":       ("#27ae60", "#1e8449"),  # xanh
        "VINA CHO":       ("#8e44ad", "#6c3483"),  # tím
        "Trung Nguyên":   ("#d35400", "#a04000"),  # nâu
        "Vinacam":        ("#2980b9", "#1a5276"),  # xanh đậm
        "HAGL Agrico":    ("#1abc9c", "#148f77"),  # ngọc
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.manager = MarketConnectionManager()
        self.data: Optional[ConnectionData] = None

        # Scrollable container
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Xây dựng toàn bộ giao diện."""
        # ─────── HEADER ───────
        header = ctk.CTkFrame(self.container, corner_radius=0, fg_color=T.PRIMARY_DARK)
        header.pack(fill="x")

        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(padx=40, pady=28)

        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "GASH-VIU.png")
            logo_img = ctk.CTkImage(Image.open(logo_path), size=(36, 36))
            ctk.CTkLabel(h_inner, image=logo_img, text="").pack(side="left", padx=(0, 12))
        except:
            ctk.CTkLabel(h_inner, text="🌐", font=ctk.CTkFont(size=28)).pack(side="left", padx=(0, 12))

        texts = ctk.CTkFrame(h_inner, fg_color="transparent")
        texts.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            texts, text="KẾT NỐI THỊ TRƯỜNG NÔNG SẢN",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white", anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            texts,
            text="Cầu nối giữa nông dân và doanh nghiệp — tìm đại lý, nhà cung cấp và đối tác uy tín toàn quốc",
            font=ctk.CTkFont(size=12),
            text_color="#d5f5e3", anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # ─────── STATS BANNER ───────
        self.stats_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=40, pady=(24, 8))

        self.stat_cards = {}
        self.stat_value_labels = {}
        for key, label, icon, color in [
            ("total_partners", "Đối tác đăng ký", "🤝", T.INFO),
            ("total_provinces", "Tỉnh thành", "📍", T.SUCCESS),
        ]:
            card, val_label = self._make_stat_card(self.stats_frame, icon, label, "…", color)
            card.pack(side="left", fill="x", expand=True, padx=6, pady=6)
            self.stat_cards[key] = card
            self.stat_value_labels[key] = val_label

        # ─────── LAST UPDATED ───────
        self.update_label = ctk.CTkLabel(
            self.container, text="",
            font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED,
        )
        self.update_label.pack(anchor="e", padx=44, pady=(0, 4))

        # ─────── DANH MỤC KẾT NỐI ───────
        section = ctk.CTkFrame(self.container, fg_color="transparent")
        section.pack(fill="x", padx=40, pady=(8, 4))

        ctk.CTkLabel(
            section, text="📂 DANH MỤC KẾT NỐI",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            section, text="Tìm nhà cung cấp, đại lý và đối tác theo từng lĩnh vực",
            font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED,
        ).pack(anchor="w")

        # Grid container cho category cards
        self.cat_grid = ctk.CTkFrame(self.container, fg_color="transparent")
        self.cat_grid.pack(fill="x", padx=40, pady=(8, 16))

        # ─────── ĐỐI TÁC NỔI BẬT ───────
        partner_sec = ctk.CTkFrame(self.container, fg_color="transparent")
        partner_sec.pack(fill="x", padx=40, pady=(8, 4))

        ctk.CTkLabel(
            partner_sec, text="🌟 ĐỐI TÁC NỔI BẬT",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            partner_sec, text="Các doanh nghiệp và tổ chức uy tín trong ngành nông nghiệp",
            font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED,
        ).pack(anchor="w")

        # Grid cho partners
        self.partner_grid = ctk.CTkFrame(self.container, fg_color="transparent")
        self.partner_grid.pack(fill="x", padx=40, pady=(8, 16))

        # ─────── CTA ───────
        cta = ctk.CTkFrame(self.container, corner_radius=T.CORNER_RADIUS, fg_color=T.PRIMARY_LIGHT)
        cta.pack(fill="x", padx=40, pady=(8, 24))

        cta_inner = ctk.CTkFrame(cta, fg_color="transparent")
        cta_inner.pack(padx=30, pady=24)

        ctk.CTkLabel(
            cta_inner, text="Bạn là đại lý hoặc doanh nghiệp?",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack()

        ctk.CTkLabel(
            cta_inner,
            text="Đăng ký để kết nối với hàng nghìn nông dân trên toàn quốc — hoàn toàn miễn phí",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        ).pack(pady=(4, 12))

        btn_row = ctk.CTkFrame(cta_inner, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="📝 Đăng ký miễn phí",
            command=lambda: webbrowser.open("https://nongdanviet.vn/ket-noi"),
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
            height=38, font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="📞 Liên hệ hợp tác",
            command=lambda: webbrowser.open("https://nongdanviet.vn/lien-he"),
            fg_color=T.INFO, hover_color="#2874a6",
            height=38, font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=6)

        # ─────── LOADING / ERROR ───────
        self.loading_label = ctk.CTkLabel(
            self.container, text="",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        )
        self.loading_label.pack(pady=(0, 16))

    # ─────────────── HELPERS ───────────────

    def _make_stat_card(self, parent, icon, label, value, color):
        """Tạo một thẻ thống kê."""
        card = ctk.CTkFrame(parent, corner_radius=T.CORNER_RADIUS_SM, fg_color=T.BG_CARD)
        # border-like accent
        accent = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color)
        accent.pack(fill="x")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(padx=16, pady=(12, 16), fill="x")

        ctk.CTkLabel(body, text=icon, font=ctk.CTkFont(size=24)).pack(anchor="center")
        ctk.CTkLabel(body, text=label, font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED).pack(anchor="center")
        val_label = ctk.CTkLabel(body, text=str(value), font=ctk.CTkFont(size=28, weight="bold"),
                      text_color=color)
        val_label.pack(anchor="center", pady=(2, 0))
        return card, val_label

    def _make_category_card(self, parent, cat: ConnectionCategory, idx: int):
        """Tạo thẻ danh mục kết nối."""
        color, hover = self.CATEGORY_COLORS.get(cat.name, (T.INFO, T.PRIMARY_DARK))

        card = ctk.CTkFrame(parent, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD,
                            border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        card.pack(side="left", fill="both", expand=True,
                  padx=6, pady=6, ipadx=4, ipady=4)

        accent = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color=color)
        accent.pack(fill="x")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(padx=16, pady=(16, 16), fill="x")

        # Hàng icon + count
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=cat.icon, font=ctk.CTkFont(size=28)).pack(side="left")
        ctk.CTkLabel(top, text=str(cat.count), font=ctk.CTkFont(size=20, weight="bold"),
                      text_color=color).pack(side="right")

        # Tên danh mục
        ctk.CTkLabel(body, text=cat.name, font=ctk.CTkFont(size=14, weight="bold"),
                      anchor="w").pack(anchor="w", pady=(8, 2))

        # Mô tả
        desc = cat.description[:80] + "…" if len(cat.description) > 80 else cat.description
        ctk.CTkLabel(body, text=desc, font=ctk.CTkFont(size=11),
                      text_color=T.TEXT_MUTED, anchor="w",
                      wraplength=180, justify="left").pack(anchor="w", fill="x")

        # Nút Xem thêm
        ctk.CTkButton(
            body, text=f"Xem thêm ({cat.count})",
            command=lambda u=cat.source_url: webbrowser.open(u),
            fg_color=color, hover_color=hover,
            height=30, font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=T.CORNER_RADIUS_SM,
        ).pack(fill="x", pady=(10, 0))

        return card

    def _make_partner_card(self, parent, partner: FeaturedPartner):
        """Tạo thẻ đối tác nổi bật."""
        color, hover = self.PARTNER_COLORS.get(partner.name, (T.INFO, T.PRIMARY_DARK))

        card = ctk.CTkFrame(parent, corner_radius=T.CORNER_RADIUS_SM, fg_color=T.BG_CARD,
                            border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        card.pack(side="left", fill="both", expand=True,
                  padx=6, pady=6, ipadx=4, ipady=4)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(padx=14, pady=(14, 14), fill="x")

        ctk.CTkLabel(body, text=partner.icon, font=ctk.CTkFont(size=30)).pack(anchor="center")
        ctk.CTkLabel(body, text=partner.name, font=ctk.CTkFont(size=13, weight="bold"),
                      anchor="center").pack(anchor="center", pady=(6, 2))
        ctk.CTkLabel(body, text=partner.description, font=ctk.CTkFont(size=10),
                      text_color=T.TEXT_MUTED, anchor="center").pack(anchor="center")

        badge = ctk.CTkFrame(body, fg_color=color, corner_radius=8)
        badge.pack(pady=(8, 0))
        ctk.CTkLabel(badge, text="Đối tác", font=ctk.CTkFont(size=9, weight="bold"),
                      text_color="white").pack(padx=10, pady=2)

        return card

    # ─────────────── DATA ───────────────

    def load_data(self):
        """Tải dữ liệu kết nối thị trường."""
        self.loading_label.configure(text="⏳ Đang tải dữ liệu kết nối thị trường…")
        self.update()

        try:
            data = self.manager.get_connections(force_refresh=True)
            self.data = data
            self._render_data(data)
        except Exception as e:
            self.loading_label.configure(text=f"❌ Lỗi tải dữ liệu: {e}")
            logger.error(f"Lỗi load market connections: {e}")

    def refresh_data(self):
        """Tải lại dữ liệu (bỏ qua cache)."""
        self.manager.clear_cache()
        self.load_data()

    def _render_data(self, data: ConnectionData):
        """Hiển thị dữ liệu lên giao diện."""
        if data.error:
            self.loading_label.configure(text=f"⚠️ {data.error}")
            return

        # ── Stats (dùng reference trực tiếp từ stat_value_labels) ──
        for key, val_label in self.stat_value_labels.items():
            val = data.stats.get(key, 0)
            val_label.configure(text=str(val))

        # ── Thời gian ──
        self.update_label.configure(
            text=f"🕐 Cập nhật: {data.fetched_at}  ·  Nguồn: {data.source_name}"
        )

        # ── Categories ──
        for widget in self.cat_grid.winfo_children():
            widget.destroy()

        if data.categories:
            row_frame = None
            for i, cat in enumerate(data.categories):
                if i % 3 == 0:
                    row_frame = ctk.CTkFrame(self.cat_grid, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)
                self._make_category_card(row_frame, cat, i)
        else:
            ctk.CTkLabel(
                self.cat_grid, text="Không có dữ liệu danh mục",
                font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
            ).pack(pady=12)

        # ── Partners ──
        for widget in self.partner_grid.winfo_children():
            widget.destroy()

        if data.partners:
            row_frame = None
            for i, p in enumerate(data.partners):
                if i % 3 == 0:
                    row_frame = ctk.CTkFrame(self.partner_grid, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)
                self._make_partner_card(row_frame, p)
        else:
            ctk.CTkLabel(
                self.partner_grid, text="Không có dữ liệu đối tác",
                font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
            ).pack(pady=12)

        # ── Loading done ──
        self.loading_label.configure(text="✅ Dữ liệu đã được tải từ nongdanviet.vn")
        self.after(3000, lambda: self.loading_label.configure(text=""))
