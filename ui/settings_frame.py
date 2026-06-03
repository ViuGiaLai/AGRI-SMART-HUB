# -*- coding: utf-8 -*-
"""
ui/settings_frame.py — Cài đặt hệ thống GASH.

5 Tab:
  1. Quy chuẩn Thu mua — dẫn đến GradingRulesFrame
  2. Hồ sơ Đại lý — thông tin in trên báo cáo
  3. AI & API — Gemini key, Agentic mode, System Prompt
  4. Giao diện & Hệ thống — theme, ngôn ngữ, đường dẫn
  5. Kết nối & Bảo mật — Supabase status, đổi mật khẩu, xóa cache
"""

import json
import logging
import os
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox, filedialog
from typing import Any, Dict, Optional

import customtkinter as ctk
from PIL import Image

from ui import theme as T

logger = logging.getLogger(__name__)


class SettingsFrame(ctk.CTkFrame):
    """Cài đặt hệ thống — 5 tab chức năng."""

    def __init__(self, master, db_manager=None, user_id=None, main_app=None, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.main_app = main_app  # reference đến MainApp để gọi toggle_theme,...

        self.prefs = self._load_prefs()

        # ─────── HEADER ───────
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=T.SECONDARY)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="⚙️ CÀI ĐẶT HỆ THỐNG",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(padx=30, pady=18)

        # ─────── TAB VIEW ───────
        self.tab_view = ctk.CTkTabview(
            self, corner_radius=T.CORNER_RADIUS,
            fg_color="transparent",
            segmented_button_fg_color=T.PRIMARY_LIGHT,
            segmented_button_selected_color=T.PRIMARY,
            segmented_button_selected_hover_color=T.PRIMARY_DARK,
        )
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)

        # Tạo 5 tab
        self.tab1 = self.tab_view.add("📏 Quy chuẩn")
        self.tab2 = self.tab_view.add("👤 Hồ sơ Đại lý")
        self.tab3 = self.tab_view.add("🤖 AI & API")
        self.tab4 = self.tab_view.add("🎨 Giao diện")
        self.tab5 = self.tab_view.add("🔒 Bảo mật")

        self._build_tab_quy_chuan()
        self._build_tab_ho_so()
        self._build_tab_ai()
        self._build_tab_giao_dien()
        self._build_tab_bao_mat()

        # Lưu ref preferences để sync với MainApp
        if self.main_app and hasattr(self.main_app, 'prefs'):
            # Dùng chung prefs dictionary với MainApp nếu có
            pass

    # ════════════════════════════════════════════
    # TAB 1 — Quy chuẩn Thu mua
    # ════════════════════════════════════════════
    def _build_tab_quy_chuan(self):
        """Hiển thị link đến GradingRulesFrame + tổng quan."""
        t = self.tab1

        # Card hướng dẫn
        guide = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        guide.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            guide, text="📏 QUY CHUẨN THU MUA (TRỪ LÙI)",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=20, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            guide,
            text="Thiết lập các thông số để máy tính tự động trừ ẩm, trừ tạp chất.\n"
                 "• Độ ẩm chuẩn: Nếu hàng nông dân cao hơn mức này → trừ cân\n"
                 "• Tỷ lệ trừ: 1% vượt → trừ X% trọng lượng\n"
                 "• Mỗi sản phẩm có thể có quy tắc riêng",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
            justify="left", wraplength=600,
        ).pack(padx=20, pady=(0, 15), anchor="w")

        ctk.CTkButton(
            guide, text="🔧 Mở Cấu hình Quy tắc Trừ lùi",
            command=self._open_grading_rules,
            height=44, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
        ).pack(pady=(0, 18))

        # Hiển thị tóm tắt các quy tắc hiện có
        summary = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        summary.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        ctk.CTkLabel(
            summary, text="📋 TÓM TẮT QUY TẮC HIỆN TẠI",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=20, pady=(12, 8), anchor="w")

        self.rule_summary_frame = ctk.CTkFrame(summary, fg_color="transparent")
        self.rule_summary_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # ─── Đơn vị tính mặc định ───
        unit_row = ctk.CTkFrame(guide, fg_color="transparent")
        unit_row.pack(fill="x", padx=20, pady=(4, 4))
        ctk.CTkLabel(unit_row, text="📦 Đơn vị tính mặc định:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.default_unit_var = ctk.StringVar(value=self.prefs.get("default_unit", "kg"))
        unit_combo = ctk.CTkComboBox(unit_row, values=["kg", "tấn", "bao"],
                                      variable=self.default_unit_var, width=100,
                                      command=self._save_default_unit)
        unit_combo.pack(side="right")

        # ─── Sản phẩm mặc định ───
        prod_row = ctk.CTkFrame(guide, fg_color="transparent")
        prod_row.pack(fill="x", padx=20, pady=(4, 10))
        ctk.CTkLabel(prod_row, text="⭐ Sản phẩm ưu tiên hiển thị:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.default_product_var = ctk.StringVar(value=self.prefs.get("default_product", "Cà phê"))
        prod_combo = ctk.CTkComboBox(prod_row, values=["Cà phê", "Hồ tiêu", "Sầu riêng", "Lúa gạo"],
                                      variable=self.default_product_var, width=150,
                                      command=self._save_default_product)
        prod_combo.pack(side="right")

        self._refresh_rule_summary()

    def _save_default_unit(self, choice):
        self.prefs["default_unit"] = choice
        self._save_to_mainapp()

    def _save_default_product(self, choice):
        self.prefs["default_product"] = choice
        self._save_to_mainapp()

    def _open_grading_rules(self):
        """Chuyển đến GradingRulesFrame thông qua main_app."""
        if self.main_app:
            self.main_app.show_grading_rules()
        else:
            messagebox.showinfo("Thông tin", "Vui lòng dùng menu 'Quy tắc trừ lùi' ở sidebar.")

    def _refresh_rule_summary(self):
        """Làm mới bảng tóm tắt quy tắc."""
        for w in self.rule_summary_frame.winfo_children():
            w.destroy()

        if not self.db or not self.user_id:
            ctk.CTkLabel(
                self.rule_summary_frame,
                text="Chưa đăng nhập — không thể tải dữ liệu",
                font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
            ).pack(pady=10)
            return

        try:
            rules = self.db.get_grading_rules(self.user_id)
            if not rules:
                ctk.CTkLabel(
                    self.rule_summary_frame,
                    text="Chưa có quy tắc nào. Hãy nhấn nút trên để tạo mới.",
                    font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
                ).pack(pady=10)
                return

            for rule in rules:
                pname = rule.get("products", {}).get("name", "N/A")
                card = ctk.CTkFrame(
                    self.rule_summary_frame, corner_radius=8,
                    border_width=1, border_color=("#e8e8e8", "#3d3d3d"),
                )
                card.pack(fill="x", pady=3)

                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=8)
                ctk.CTkLabel(row, text=f"🌱 {pname}",
                             font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
                ctk.CTkLabel(row, text=f"Ẩm {rule.get('std_moisture', '?')}% ×{rule.get('moisture_ratio', '?')} "
                                       f"· Tạp {rule.get('std_impurity', '?')}% ×{rule.get('impurity_ratio', '?')}",
                             font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED).pack(side="right")

        except Exception as e:
            ctk.CTkLabel(
                self.rule_summary_frame,
                text=f"⚠️ Lỗi tải: {e}", font=ctk.CTkFont(size=11),
                text_color=T.DANGER,
            ).pack(pady=10)

    # ════════════════════════════════════════════
    # TAB 2 — Hồ sơ Đại lý
    # ════════════════════════════════════════════
    def _build_tab_ho_so(self):
        t = self.tab2
        form = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            form, text="👤 THÔNG TIN ĐẠI LÝ",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=24, pady=(20, 16), anchor="w")

        # Avatar / Logo
        avatar_frame = ctk.CTkFrame(form, fg_color="transparent")
        avatar_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.avatar_label = ctk.CTkLabel(avatar_frame, text="🖼️", font=ctk.CTkFont(size=48))
        self.avatar_label.pack(side="left", padx=(0, 16))

        avatar_btn_frame = ctk.CTkFrame(avatar_frame, fg_color="transparent")
        avatar_btn_frame.pack(side="left")
        ctk.CTkLabel(avatar_frame, text="Logo đại lý (xuất hiện trên báo cáo)",
                     font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED).pack(anchor="w")
        ctk.CTkButton(avatar_frame, text="Chọn ảnh...", command=self._choose_logo,
                      width=100, height=28, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(4, 0))

        # Form fields
        fields = [
            ("🏷️ Tên Đại lý / Tên Shop", "agency_name", "VD: Đại lý ViuGiaLai"),
            ("👤 Tên chủ hộ", "owner_name", "VD: Nguyễn Văn A"),
            ("📞 Số điện thoại", "phone", "VD: 0912 345 678"),
            ("📍 Địa chỉ", "address", "VD: 123 Nguyễn Huệ, Pleiku, Gia Lai"),
        ]

        self.profile_entries = {}
        for label, key, placeholder in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         width=180, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=35)
            entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
            self.profile_entries[key] = entry

        # User ID (read-only)
        uid_row = ctk.CTkFrame(form, fg_color="transparent")
        uid_row.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(uid_row, text="🆔 Mã định danh (User ID)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=180, anchor="w").pack(side="left")
        self.uid_label = ctk.CTkLabel(
            uid_row, text=self.user_id or "N/A",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        )
        self.uid_label.pack(side="left", padx=(10, 0))

        # Load saved profile
        self._load_profile()

        # Buttons
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(16, 20))
        ctk.CTkButton(btn_row, text="💾 Lưu thông tin",
                      command=self._save_profile,
                      height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T.PRIMARY).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="🔄 Đặt lại",
                      command=self._load_profile,
                      height=38, font=ctk.CTkFont(size=13),
                      fg_color=T.SECONDARY_LIGHT).pack(side="left")

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            title="Chọn logo đại lý",
            filetypes=[("Hình ảnh", "*.png *.jpg *.jpeg *.gif *.ico"), ("Tất cả", "*.*")]
        )
        if path:
            try:
                img = ctk.CTkImage(Image.open(path), size=(48, 48))
                self.avatar_label.configure(image=img)
                self.avatar_label.image = img
                self.prefs["logo_path"] = path
                self._save_prefs()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể load ảnh: {e}")

    def _load_profile(self):
        """Điền thông tin đại lý từ preferences."""
        for key, entry in self.profile_entries.items():
            entry.delete(0, "end")
            entry.insert(0, self.prefs.get(key, ""))

        # Load logo
        logo_path = self.prefs.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                img = ctk.CTkImage(Image.open(logo_path), size=(48, 48))
                self.avatar_label.configure(image=img)
                self.avatar_label.image = img
            except:
                pass

    def _save_profile(self):
        """Lưu thông tin đại lý vào preferences JSON."""
        for key, entry in self.profile_entries.items():
            self.prefs[key] = entry.get().strip()
        self._save_prefs()
        messagebox.showinfo("Thành công", "Đã lưu thông tin đại lý!")

    # ════════════════════════════════════════════
    # TAB 3 — AI & API
    # ════════════════════════════════════════════
    def _build_tab_ai(self):
        t = self.tab3
        form = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form, text="🤖 CẤU HÌNH AI & API",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).pack(padx=24, pady=(20, 16), anchor="w")

        # API Key
        api_row = ctk.CTkFrame(form, fg_color="transparent")
        api_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(api_row, text="🔑 Gemini API Key",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=160, anchor="w").pack(side="left")
        self.api_key_entry = ctk.CTkEntry(api_row, placeholder_text="Nhập API key...",
                                          height=35, show="•")
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Toggle hiện API key
        self.show_api_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(api_row, text="👁️", variable=self.show_api_var,
                        command=self._toggle_api_visible,
                        checkbox_width=20, width=30).pack(side="left", padx=(6, 0))

        # Nạp API key từ .env / prefs
        self._load_api_key()

        # Trạng thái kết nối
        self.api_status = ctk.CTkLabel(form, text="",
                                       font=ctk.CTkFont(size=11))
        self.api_status.pack(anchor="w", padx=24, pady=(0, 10))

        # Kiểm tra kết nối
        ctk.CTkButton(form, text="🔌 Kiểm tra kết nối Gemini",
                      command=self._test_gemini,
                      height=36, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=24, pady=(0, 16))

        # Agentic mode toggle
        agentic_row = ctk.CTkFrame(form, fg_color="transparent")
        agentic_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(agentic_row, text="🧠 Chế độ Agentic (tự gọi tool)",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.agentic_var = ctk.BooleanVar(value=self.prefs.get("agentic_mode", True))
        ctk.CTkSwitch(agentic_row, text="", variable=self.agentic_var,
                      command=self._save_agentic_pref,
                      progress_color=T.PRIMARY).pack(side="right")
        ctk.CTkLabel(agentic_row, text="Bật" if self.agentic_var.get() else "Tắt",
                     font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED).pack(side="right", padx=(0, 6))

        # System Prompt
        prompt_row = ctk.CTkFrame(form, fg_color="transparent")
        prompt_row.pack(fill="x", padx=24, pady=(12, 6))
        ctk.CTkLabel(prompt_row, text="📝 System Prompt (lời dẫn AI)",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.system_prompt_text = ctk.CTkTextbox(form, height=120, wrap="word",
                                                  corner_radius=8, border_width=1)
        self.system_prompt_text.pack(fill="x", padx=24, pady=(4, 10))
        self.system_prompt_text.insert("0.0", self.prefs.get("system_prompt", ""))

        ctk.CTkLabel(form, text="Prompt mặc định được dùng khi không có custom prompt",
                     font=ctk.CTkFont(size=10), text_color=T.TEXT_MUTED,
                     ).pack(anchor="w", padx=24, pady=(0, 10))

        ctk.CTkButton(form, text="💾 Lưu cấu hình AI",
                      command=self._save_ai_config,
                      height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T.PRIMARY).pack(anchor="w", padx=24, pady=(0, 20))

    def _load_api_key(self):
        """Đọc API key từ .env hoặc prefs."""
        key = self.prefs.get("gemini_api_key", "")
        if not key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                key = os.environ.get("GEMINI_API_KEY", "")
            except:
                pass
        if key:
            self.api_key_entry.insert(0, key)

    def _toggle_api_visible(self):
        if self.show_api_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="•")

    def _test_gemini(self):
        """Kiểm tra kết nối Gemini API."""
        key = self.api_key_entry.get().strip()
        if not key:
            self.api_status.configure(text="❌ Chưa nhập API Key", text_color=T.DANGER)
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            models = genai.list_models()
            self.api_status.configure(text="✅ Kết nối Gemini thành công!",
                                      text_color=T.SUCCESS)
        except Exception as e:
            self.api_status.configure(text=f"❌ Lỗi: {str(e)[:60]}", text_color=T.DANGER)

    def _save_agentic_pref(self):
        self.prefs["agentic_mode"] = self.agentic_var.get()
        self._save_prefs()

    def _save_ai_config(self):
        key = self.api_key_entry.get().strip()
        self.prefs["gemini_api_key"] = key
        self.prefs["system_prompt"] = self.system_prompt_text.get("0.0", "end").strip()
        self._save_prefs()
        # Đồng bộ ngay vào environment để GeminiAgent có thể dùng
        if key:
            os.environ["GEMINI_API_KEY"] = key
        messagebox.showinfo("Thành công", "Đã lưu cấu hình AI! API Key đã được kích hoạt ngay.")

    # ════════════════════════════════════════════
    # TAB 4 — Giao diện & Hệ thống
    # ════════════════════════════════════════════
    def _build_tab_giao_dien(self):
        t = self.tab4
        form = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form, text="🎨 GIAO DIỆN & HỆ THỐNG",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).pack(padx=24, pady=(20, 16), anchor="w")

        # Theme
        theme_row = ctk.CTkFrame(form, fg_color="transparent")
        theme_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(theme_row, text="🌗 Chế độ Sáng/Tối",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_combo = ctk.CTkComboBox(theme_row, values=["Light", "Dark"],
                                      variable=self.theme_var,
                                      command=self._change_theme, width=120)
        theme_combo.pack(side="right")

        # Ngôn ngữ
        lang_row = ctk.CTkFrame(form, fg_color="transparent")
        lang_row.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(lang_row, text="🌐 Ngôn ngữ (dự trù i18n)",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.lang_var = ctk.StringVar(value=self.prefs.get("language", "Tiếng Việt"))
        lang_combo = ctk.CTkComboBox(lang_row, values=["Tiếng Việt", "English"],
                                      variable=self.lang_var, width=120,
                                      state="readonly")
        lang_combo.pack(side="right")

        # Đường dẫn lưu báo cáo
        path_row = ctk.CTkFrame(form, fg_color="transparent")
        path_row.pack(fill="x", padx=24, pady=(16, 6))
        ctk.CTkLabel(path_row, text="📁 Đường dẫn lưu báo cáo",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        path_sel = ctk.CTkFrame(form, fg_color="transparent")
        path_sel.pack(fill="x", padx=24, pady=(4, 10))
        self.report_path_entry = ctk.CTkEntry(
            path_sel, placeholder_text="VD: D:\\Bao_cao",
            height=35)
        self.report_path_entry.pack(side="left", fill="x", expand=True)
        self.report_path_entry.insert(0, self.prefs.get("report_path", ""))
        ctk.CTkButton(path_sel, text="📂 Chọn...",
                      command=self._choose_report_path,
                      width=80, height=35, font=ctk.CTkFont(size=11)).pack(side="right", padx=(8, 0))

        # Lưu preferences giao diện
        ctk.CTkButton(form, text="💾 Lưu cài đặt giao diện",
                      command=self._save_display_prefs,
                      height=38, font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=T.PRIMARY).pack(anchor="w", padx=24, pady=(16, 20))

    def _change_theme(self, choice):
        ctk.set_appearance_mode(choice)
        self.prefs["theme"] = choice
        self._save_prefs()
        # Đồng bộ với switch trên topbar nếu có
        if self.main_app and hasattr(self.main_app, "theme_switch"):
            if choice == "dark":
                self.main_app.theme_switch.select()
            else:
                self.main_app.theme_switch.deselect()

    def _choose_report_path(self):
        path = filedialog.askdirectory(title="Chọn thư mục lưu báo cáo")
        if path:
            self.report_path_entry.delete(0, "end")
            self.report_path_entry.insert(0, path)

    def _save_display_prefs(self):
        self.prefs["report_path"] = self.report_path_entry.get().strip()
        self.prefs["language"] = self.lang_var.get()
        self._save_prefs()
        messagebox.showinfo("Thành công", "Đã lưu cài đặt giao diện!")

    # ════════════════════════════════════════════
    # TAB 5 — Kết nối & Bảo mật
    # ════════════════════════════════════════════
    def _build_tab_bao_mat(self):
        t = self.tab5
        form = ctk.CTkFrame(t, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form, text="🔒 KẾT NỐI & BẢO MẬT",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).pack(padx=24, pady=(20, 16), anchor="w")

        # Supabase status
        supabase_card = ctk.CTkFrame(form, corner_radius=10,
                                      border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        supabase_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(supabase_card, text="🗄️ TRẠNG THÁI SUPABASE",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     ).pack(padx=16, pady=(10, 4), anchor="w")
        self.supabase_status = ctk.CTkLabel(
            supabase_card, text="⏳ Đang kiểm tra...",
            font=ctk.CTkFont(size=12))
        self.supabase_status.pack(padx=16, pady=(0, 10), anchor="w")
        ctk.CTkButton(supabase_card, text="🔄 Kiểm tra lại",
                      command=self._check_supabase,
                      height=30, font=ctk.CTkFont(size=11)).pack(padx=16, pady=(0, 12), anchor="w")

        self._check_supabase()

        # Thông tin user
        user_card = ctk.CTkFrame(form, corner_radius=10,
                                   border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        user_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(user_card, text="👤 THÔNG TIN NGƯỜI DÙNG",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     ).pack(padx=16, pady=(10, 4), anchor="w")
        ctk.CTkLabel(user_card, text=f"Email: {self.main_app.current_user.get('email', 'N/A') if self.main_app else 'N/A'}",
                     font=ctk.CTkFont(size=12)).pack(padx=16, pady=2, anchor="w")
        ctk.CTkLabel(user_card, text=f"User ID: {self.user_id or 'N/A'}",
                     font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
                     ).pack(padx=16, pady=(2, 10), anchor="w")

        # Dropdown for saved accounts management
        accounts_card = ctk.CTkFrame(form, corner_radius=10,
                                      border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        accounts_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(accounts_card, text="👤 QUẢN LÝ TÀI KHOẢN",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     ).pack(padx=16, pady=(10, 8), anchor="w")

        ctk.CTkButton(accounts_card, text="🔑 Đổi mật khẩu",
                      command=self._change_password,
                      height=34, font=ctk.CTkFont(size=12),
                      fg_color=T.INFO).pack(padx=16, pady=4, fill="x")
        ctk.CTkButton(accounts_card, text="🗑️ Xóa tài khoản đã lưu",
                      command=self._clear_saved_accounts,
                      height=34, font=ctk.CTkFont(size=12),
                      fg_color=T.WARNING).pack(padx=16, pady=4, fill="x")
        ctk.CTkButton(accounts_card, text="📋 Đăng xuất",
                      command=self._logout,
                      height=34, font=ctk.CTkFont(size=12),
                      fg_color=T.DANGER).pack(padx=16, pady=(4, 12), fill="x")

        # Cache
        cache_card = ctk.CTkFrame(form, corner_radius=10,
                                    border_width=1, border_color=("#e8e8e8", "#3d3d3d"))
        cache_card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(cache_card, text="🧹 DỌN DẸP",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     ).pack(padx=16, pady=(10, 8), anchor="w")
        ctk.CTkButton(cache_card, text="🗑️ Xóa bộ nhớ đệm (Cache)",
                      command=self._clear_cache,
                      height=34, font=ctk.CTkFont(size=12),
                      fg_color=T.SECONDARY_LIGHT).pack(padx=16, pady=(4, 12), anchor="w")

    def _check_supabase(self):
        try:
            from database.client import get_supabase
            supabase = get_supabase()
            # Thử một query nhỏ
            supabase.table("products").select("id", count="exact").limit(1).execute()
            self.supabase_status.configure(
                text="✅ Kết nối Supabase thành công — realtime đang hoạt động",
                text_color=T.SUCCESS)
        except Exception as e:
            self.supabase_status.configure(
                text=f"❌ Mất kết nối Supabase: {str(e)[:60]}",
                text_color=T.DANGER)

    def _change_password(self):
        """Gọi Supabase Auth đổi mật khẩu (xác thực + xác nhận)."""
        new_pw = ctk.CTkInputDialog(text="Nhập mật khẩu MỚI (tối thiểu 6 ký tự):",
                                    title="Đổi mật khẩu").get_input()
        if not new_pw or len(new_pw) < 6:
            messagebox.showerror("Lỗi", "Mật khẩu mới phải có ít nhất 6 ký tự!")
            return

        confirm_pw = ctk.CTkInputDialog(text="Nhập LẠI mật khẩu mới:",
                                       title="Xác nhận").get_input()
        if new_pw != confirm_pw:
            messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp!")
            return

        try:
            from database.client import get_supabase
            supabase = get_supabase()
            # Thử update_user trực tiếp (session còn hiệu lực)
            supabase.auth.update_user({"password": new_pw})
            messagebox.showinfo("Thành công", "Đã đổi mật khẩu thành công!")
        except Exception as e:
            error_msg = str(e)
            if "session" in error_msg.lower() or "auth" in error_msg.lower():
                # Session hết hạn — yêu cầu đăng nhập lại
                old_pw = ctk.CTkInputDialog(
                    text="Phiên đăng nhập hết hạn. Nhập mật khẩu HIỆN TẠI để xác thực lại:",
                    title="Xác thực lại").get_input()
                if old_pw:
                    try:
                        user_email = self.main_app.current_user.get('email') if self.main_app else None
                        if user_email:
                            supabase.auth.sign_in_with_password({"email": user_email, "password": old_pw})
                            supabase.auth.update_user({"password": new_pw})
                            messagebox.showinfo("Thành công", "Đã đổi mật khẩu thành công!")
                        else:
                            messagebox.showerror("Lỗi", "Không xác định được email người dùng!")
                    except Exception as e2:
                        if "Invalid login credentials" in str(e2):
                            messagebox.showerror("Lỗi", "Mật khẩu hiện tại không đúng!")
                        else:
                            messagebox.showerror("Lỗi", f"Lỗi: {str(e2)[:80]}")
            else:
                messagebox.showerror("Lỗi", f"Không thể đổi mật khẩu: {error_msg[:80]}")

    def _clear_saved_accounts(self):
        """Xóa file tài khoản đã lưu (có xác nhận)."""
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa tất cả tài khoản đã lưu?"):
            return
        try:
            for f in [".saved_accounts.json", "saved_credentials.json", ".session"]:
                if os.path.exists(f):
                    os.remove(f)
            messagebox.showinfo("Thành công", "Đã xóa tất cả tài khoản đã lưu!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xóa: {e}")

    def _clear_cache(self):
        """Xóa Redis cache + cache file (có xác nhận)."""
        if not messagebox.askyesno("Xác nhận", "Xóa toàn bộ cache (Redis + file tạm)?\nDữ liệu gốc không bị ảnh hưởng."):
            return
        try:
            # Xóa Redis cache (nếu đang chạy)
            redis_cleared = 0
            try:
                from core.cache_manager import get_cache
                cache = get_cache()
                redis_cleared = cache.flush()
            except Exception:
                pass

            # Xóa cache file
            cache_files = [".session", "user_preferences.json"]
            for f in cache_files:
                if os.path.exists(f):
                    os.remove(f)

            self.prefs = {}
            self._save_prefs()

            msg = "✅ Đã xóa cache"
            if redis_cleared > 0:
                msg += f" (gồm {redis_cleared} keys Redis)"
            else:
                msg += " (Redis không khả dụng, chỉ xóa file tạm)"
            messagebox.showinfo("Thành công", msg)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xóa cache: {e}")

    def _logout(self):
        """Đăng xuất qua main_app."""
        if self.main_app and hasattr(self.main_app, "logout"):
            self.main_app.logout()
        else:
            messagebox.showinfo("Thông tin", "Vui lòng dùng nút Đăng xuất ở góc trên bên phải.")

    # ════════════════════════════════════════════
    # PREFERENCES HELPERS
    # ════════════════════════════════════════════
    PREFS_FILE = "user_preferences.json"

    def _load_prefs(self) -> Dict[str, Any]:
        """Đọc preferences, ưu tiên dùng chung với MainApp."""
        try:
            if os.path.exists(self.PREFS_FILE):
                with open(self.PREFS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Nếu có MainApp, merge với prefs của nó
                    if self.main_app and hasattr(self.main_app, '_load_prefs'):
                        pass  # MainApp không có _load_prefs, dùng file chung là đủ
                    return data
        except Exception as e:
            logger.warning(f"Không đọc được preferences: {e}")
        return {}

    def _save_prefs(self):
        """Lưu preferences, đồng bộ với MainApp nếu có thể."""
        self._save_to_mainapp()

    def _save_to_mainapp(self):
        """Ghi preferences một lần duy nhất để tránh nhiều file I/O."""
        try:
            # Merge với file hiện tại để không mất dữ liệu của MainApp
            current = {}
            if os.path.exists(self.PREFS_FILE):
                with open(self.PREFS_FILE, "r", encoding="utf-8") as f:
                    current = json.load(f)
            current.update(self.prefs)
            with open(self.PREFS_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Không lưu được preferences: {e}")
