# -*- coding: utf-8 -*-
"""Giao dịch thu mua — layout 2 cột grid + AI Vision + kết quả tạm tính."""
import base64
import threading
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
from database.db_manager import DatabaseManager
from core.business import BusinessLogic, FarmerDebtManager
from ui import theme as T

try:
    import google.generativeai as genai
    from core.ai_engine import GeminiConfig
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False


class TransactionFrame(ctk.CTkFrame):
    """Frame quản lý giao dịch thu mua."""

    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, fg_color=T.BG_MAIN, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.business_logic = BusinessLogic()
        self.debt_manager = FarmerDebtManager(db_manager)
        self._subtracted_kg = 0.0
        self._net_weight = 0.0
        self._image_path = None
        self._ai_parsed = {}
        self.setup_ui()
        self.after(100, self.load_data)

    # ══════════════════════════════════════════════
    # SETUP UI
    # ══════════════════════════════════════════════
    def setup_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(
            hdr, text="Giao dịch thu mua",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="≤ 3 thao tác để hoàn tất một giao dịch",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0))

        self.tabview = ctk.CTkTabview(
            self, corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD,
            segmented_button_fg_color=T.SECONDARY,
            segmented_button_selected_color=T.PRIMARY,
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(8, 24))
        self.tab_new  = self.tabview.add("  ➕ Nhập giao dịch  ")
        self.tab_list = self.tabview.add("  📋 Danh sách  ")

        self._build_new_tab()
        self._build_list_tab()

    # ══════════════════════════════════════════════
    # TAB NHẬP GIAO DỊCH
    # ══════════════════════════════════════════════
    def _build_new_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_new, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Grid 2 cột
        outer = ctk.CTkFrame(scroll, fg_color="transparent")
        outer.pack(fill="x", padx=12, pady=(8, 0))
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=1)

        # ── Cột trái: Nông dân & Cân ──────────────
        col_left = ctk.CTkFrame(outer, corner_radius=T.CORNER_RADIUS,
                                fg_color=("#fafbfc", "#242424"))
        col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)

        self._card_title(col_left, "👨‍🌾 Nông dân & Cân")
        self.farmer_combo  = self._field_combo(col_left, "Nông dân",  ["Chọn nông dân..."],  None)
        self.product_combo = self._field_combo(col_left, "Sản phẩm", ["Chọn sản phẩm..."], self.on_product_change)
        self.gross_entry   = self._field_entry(col_left, "⚖️ Tổng cân (kg)")
        self.package_entry = self._field_entry(col_left, "📦 Bao bì (kg)")
        self.price_entry   = self._field_entry(col_left, "💰 Đơn giá (VNĐ/kg)")

        pf = ctk.CTkFrame(col_left, fg_color="transparent")
        pf.pack(fill="x", padx=20, pady=(8, 20))
        ctk.CTkLabel(pf, text="Hình thức thanh toán",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=T.TEXT_DARK).pack(anchor="w")
        self.payment_var = ctk.StringVar(value="paid")
        ctk.CTkRadioButton(pf, text="Thanh toán ngay", variable=self.payment_var,
                           value="paid", command=self.calculate_total,
                           fg_color=T.PRIMARY).pack(anchor="w", pady=(6, 2))
        ctk.CTkRadioButton(pf, text="Ghi nợ", variable=self.payment_var,
                           value="debt", command=self.calculate_total,
                           fg_color=T.PRIMARY).pack(anchor="w")

        # ── Cột phải: Chất lượng & AI Vision ──────
        col_right = ctk.CTkFrame(outer, corner_radius=T.CORNER_RADIUS,
                                 fg_color=("#fafbfc", "#242424"))
        col_right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)

        self._card_title(col_right, "🔬 Chất lượng & AI Vision")
        self.moisture_entry = self._field_entry(col_right, "💧 Độ ẩm (%)")
        self.impurity_entry = self._field_entry(col_right, "🧹 Tạp chất (%)")

        rf = ctk.CTkFrame(col_right, fg_color="transparent")
        rf.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(rf, text="Quy tắc trừ lùi",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=T.TEXT_DARK).pack(anchor="w")
        self.rule_combo = ctk.CTkComboBox(
            rf, values=["Mặc định (theo sản phẩm)"],
            height=42, corner_radius=T.CORNER_RADIUS_SM,
            font=ctk.CTkFont(size=13),
            command=lambda _: self.calculate_net_weight(),
        )
        self.rule_combo.pack(fill="x", pady=(4, 0))

        ctk.CTkFrame(col_right, fg_color=T.PRIMARY_LIGHT, height=2).pack(
            fill="x", padx=20, pady=(14, 0))
        self._build_ai_vision(col_right)

        # Bind
        for entry in (self.gross_entry, self.package_entry,
                      self.moisture_entry, self.impurity_entry, self.price_entry):
            entry.bind("<KeyRelease>", lambda e: self.calculate_net_weight())

        # ── Kết quả tạm tính ──────────────────────
        result_bar = ctk.CTkFrame(
            scroll, corner_radius=T.CORNER_RADIUS,
            fg_color=(T.PRIMARY_LIGHT, "#1b3529"),
            border_width=2, border_color=T.PRIMARY,
        )
        result_bar.pack(fill="x", padx=12, pady=(10, 0))

        rb_inner = ctk.CTkFrame(result_bar, fg_color="transparent")
        rb_inner.pack(fill="x", padx=28, pady=18)
        rb_inner.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_subtracted = ctk.CTkLabel(
            rb_inner, text="0",
            font=ctk.CTkFont(size=34, weight="bold"), text_color=T.DANGER)
        self.lbl_subtracted.grid(row=0, column=0)
        ctk.CTkLabel(rb_inner, text="kg bị trừ",
                     font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED).grid(row=1, column=0)

        self.lbl_net = ctk.CTkLabel(
            rb_inner, text="0",
            font=ctk.CTkFont(size=34, weight="bold"), text_color=T.SECONDARY)
        self.lbl_net.grid(row=0, column=1)
        ctk.CTkLabel(rb_inner, text="kg cân tịnh",
                     font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED).grid(row=1, column=1)

        self.lbl_total = ctk.CTkLabel(
            rb_inner, text="0 ₫",
            font=ctk.CTkFont(size=34, weight="bold"), text_color=T.PRIMARY)
        self.lbl_total.grid(row=0, column=2)
        ctk.CTkLabel(rb_inner, text="VNĐ khách nhận",
                     font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED).grid(row=1, column=2)

        # ── Nút hành động ─────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(10, 16))

        self.save_button = ctk.CTkButton(
            btn_row, text="✓  XÁC NHẬN GIAO DỊCH",
            command=self.save_transaction, height=54,
            corner_radius=T.CORNER_RADIUS,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
        )
        self.save_button.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="🗑  Xóa form", command=self.clear_form,
            height=54, corner_radius=T.CORNER_RADIUS,
            fg_color=T.SECONDARY_LIGHT, hover_color=T.SECONDARY,
            font=ctk.CTkFont(size=14), width=140,
        ).pack(side="right")

    # ══════════════════════════════════════════════
    # AI VISION BLOCK
    # ══════════════════════════════════════════════
    def _build_ai_vision(self, parent):
        badge_color = T.PRIMARY if _GEMINI_OK else T.DANGER
        badge_text  = "● Sẵn sàng" if _GEMINI_OK else "● Chưa cấu hình"

        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(10, 6))
        ctk.CTkLabel(hdr, text="🤖 Nhận diện chất lượng hạt",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=T.PRIMARY).pack(side="left")
        ctk.CTkLabel(hdr, text=badge_text,
                     font=ctk.CTkFont(size=11), text_color=badge_color).pack(side="right")

        self.img_drop_zone = ctk.CTkFrame(
            parent, corner_radius=T.CORNER_RADIUS_SM,
            fg_color=("#eef8f2", "#1a2e22"),
            border_width=2, border_color=T.PRIMARY, height=72,
        )
        self.img_drop_zone.pack(fill="x", padx=20, pady=(0, 8))
        self.img_drop_zone.pack_propagate(False)

        self.lbl_img_status = ctk.CTkLabel(
            self.img_drop_zone,
            text="📷  Chưa có ảnh — nhấn để tải lên",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        )
        self.lbl_img_status.place(relx=0.5, rely=0.5, anchor="center")

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(
            btn_row, text="📁 Chọn ảnh",
            command=self.upload_image, height=38,
            corner_radius=T.CORNER_RADIUS_SM,
            fg_color=T.SECONDARY_LIGHT, hover_color=T.SECONDARY,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_analyze = ctk.CTkButton(
            btn_row, text="🔍 Phân tích AI",
            command=self.analyze_image_with_ai, height=38,
            corner_radius=T.CORNER_RADIUS_SM,
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
            font=ctk.CTkFont(size=13), state="disabled",
        )
        self.btn_analyze.pack(side="right", fill="x", expand=True, padx=(6, 0))

        result_box = ctk.CTkFrame(parent, corner_radius=T.CORNER_RADIUS_SM,
                                  fg_color=("#f0faf4", "#1c2e22"))
        result_box.pack(fill="x", padx=20, pady=(0, 6))

        self.lbl_ai_result = ctk.CTkLabel(
            result_box,
            text="Kết quả phân tích sẽ hiển thị ở đây",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
            wraplength=260, justify="left",
        )
        self.lbl_ai_result.pack(anchor="w", padx=12, pady=10)

        self.btn_apply_result = ctk.CTkButton(
            parent, text="✅ Áp dụng kết quả vào form",
            command=self._apply_ai_result, height=36,
            corner_radius=T.CORNER_RADIUS_SM,
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
            font=ctk.CTkFont(size=12),
        )
        # KHÔNG pack ở đây — chỉ pack sau khi có kết quả AI

        ctk.CTkFrame(parent, fg_color="transparent", height=12).pack()

    # ══════════════════════════════════════════════
    # TAB DANH SÁCH
    # ══════════════════════════════════════════════
    def _build_list_tab(self):
        search_frame = ctk.CTkFrame(self.tab_list, fg_color="transparent")
        search_frame.pack(fill="x", padx=8, pady=8)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍 Tìm kiếm...",
            height=42, corner_radius=T.CORNER_RADIUS_SM,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            search_frame, text="Tìm", width=90, height=42,
            fg_color=T.PRIMARY, command=self.search_transactions,
        ).pack(side="left")

        tree_wrap = ctk.CTkFrame(self.tab_list, corner_radius=T.CORNER_RADIUS_SM)
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=4)

        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("", 11))
        style.configure("Treeview.Heading", font=("", 11, "bold"))

        scrollbar = ttk.Scrollbar(tree_wrap, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        columns = ("Ngày", "Nông dân", "Sản phẩm", "Cân tịnh (kg)", "Thành tiền (VNĐ)", "TT")
        self.tree = ttk.Treeview(
            tree_wrap, columns=columns, show="headings",
            yscrollcommand=scrollbar.set,
        )
        col_widths = [90, 150, 120, 100, 130, 50]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.tree.yview)

        ctk.CTkButton(
            self.tab_list, text="🔄 Làm mới",
            command=self.load_transactions,
            height=40, fg_color=T.SECONDARY_LIGHT,
            corner_radius=T.CORNER_RADIUS_SM,
        ).pack(fill="x", padx=8, pady=(4, 8))

    # ══════════════════════════════════════════════
    # HELPER WIDGETS
    # ══════════════════════════════════════════════
    def _card_title(self, parent, text: str):
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T.SECONDARY).pack(anchor="w", padx=20, pady=(16, 10))

    def _field_entry(self, parent, label: str):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T.TEXT_DARK).pack(anchor="w")
        entry = ctk.CTkEntry(f, height=40, corner_radius=T.CORNER_RADIUS_SM,
                             font=ctk.CTkFont(size=13))
        entry.pack(fill="x", pady=(3, 0))
        return entry

    def _field_combo(self, parent, label: str, values: list, command):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=T.TEXT_DARK).pack(anchor="w")
        combo = ctk.CTkComboBox(f, values=values, height=40,
                                corner_radius=T.CORNER_RADIUS_SM,
                                font=ctk.CTkFont(size=13), command=command)
        combo.pack(fill="x", pady=(3, 0))
        return combo

    # ══════════════════════════════════════════════
    # UPLOAD & AI VISION
    # ══════════════════════════════════════════════
    def upload_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh nắm hạt",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Tất cả", "*.*")],
        )
        if not path:
            return
        self._image_path = path
        short = path.replace("\\", "/").split("/")[-1]
        self.lbl_img_status.configure(text=f"✅  {short}", text_color=T.PRIMARY)
        self.btn_analyze.configure(state="normal")
        self.btn_apply_result.pack_forget()
        self.lbl_ai_result.configure(
            text="Nhấn 'Phân tích AI' để nhận diện chất lượng hạt",
            text_color=T.TEXT_MUTED)
        self._ai_parsed = {}

    def analyze_image_with_ai(self):
        if not self._image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ảnh trước")
            return
        if not _GEMINI_OK:
            messagebox.showerror("Lỗi", "Thư viện google-generativeai chưa được cài đặt")
            return
        config = GeminiConfig()
        if not config.configured:
            messagebox.showerror("Lỗi API",
                                 "Chưa cấu hình GEMINI_API_KEY.\n"
                                 "Vui lòng thêm key trong mục Cài đặt.")
            return

        self.btn_analyze.configure(state="disabled", text="⏳ Đang phân tích...")
        self.lbl_ai_result.configure(text="🔄  AI đang phân tích ảnh...",
                                     text_color=T.TEXT_MUTED)
        self.btn_apply_result.pack_forget()
        threading.Thread(target=self._run_vision_api, daemon=True).start()

    def _run_vision_api(self):
        try:
            with open(self._image_path, "rb") as f:
                img_bytes = f.read()
            ext  = self._image_path.rsplit(".", 1)[-1].lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "webp": "image/webp",
                    "bmp": "image/bmp"}.get(ext, "image/jpeg")

            config = GeminiConfig()
            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = (
                "Bạn là chuyên gia kiểm tra chất lượng nông sản tại Việt Nam. "
                "Phân tích ảnh hạt cà phê hoặc hạt tiêu và trả lời đúng định dạng:\n\n"
                "TẠP_CHẤT: <số 0-100>\n"
                "ĐỘ_ẨM_ƯỚC_TÍNH: <số 0-100>\n"
                "NHẬN_XÉT: <1-2 câu>\n\n"
                "TẠP_CHẤT = % hạt lỗi (nhân đen, vỡ, lép, tạp vật). "
                "Chỉ trả về 3 dòng trên, không thêm gì khác."
            )
            response = model.generate_content([
                prompt,
                {"mime_type": mime, "data": base64.b64encode(img_bytes).decode()}
            ])
            parsed = self._parse_vision_response(response.text.strip())
            self.after(0, lambda: self._on_vision_success(parsed))
        except FileNotFoundError:
            self.after(0, lambda: self._on_vision_error("Không tìm thấy file ảnh"))
        except Exception as e:
            err = str(e)
            if "api key" in err.lower():
                err = "API Key không hợp lệ"
            elif "quota" in err.lower():
                err = "Đã vượt quota API hôm nay"
            self.after(0, lambda msg=err: self._on_vision_error(msg))

    def _parse_vision_response(self, text: str) -> dict:
        result = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("TẠP_CHẤT:"):
                try:
                    result["impurity"] = min(100.0, max(0.0,
                        float(line.split(":", 1)[1].strip().replace(",", "."))))
                except ValueError:
                    pass
            elif line.startswith("ĐỘ_ẨM_ƯỚC_TÍNH:"):
                try:
                    result["moisture"] = min(100.0, max(0.0,
                        float(line.split(":", 1)[1].strip().replace(",", "."))))
                except ValueError:
                    pass
            elif line.startswith("NHẬN_XÉT:"):
                result["note"] = line.split(":", 1)[1].strip()
        return result

    def _on_vision_success(self, parsed: dict):
        self._ai_parsed = parsed
        self.btn_analyze.configure(state="normal", text="🔍 Phân tích AI")
        impurity = parsed.get("impurity", "?")
        moisture = parsed.get("moisture", "?")
        note     = parsed.get("note", "")
        self.lbl_ai_result.configure(
            text=f"🧹 Tạp chất: {impurity}%\n💧 Độ ẩm: {moisture}%\n📝 {note}",
            text_color=T.TEXT_DARK)
        if "impurity" in parsed or "moisture" in parsed:
            self.btn_apply_result.pack(fill="x", padx=20, pady=(0, 8))

    def _on_vision_error(self, error_msg: str):
        self.btn_analyze.configure(state="normal", text="🔍 Phân tích AI")
        self.lbl_ai_result.configure(text=f"❌ Lỗi: {error_msg}", text_color=T.DANGER)

    def _apply_ai_result(self):
        if not self._ai_parsed:
            return
        if "impurity" in self._ai_parsed:
            self.impurity_entry.delete(0, "end")
            self.impurity_entry.insert(0, str(self._ai_parsed["impurity"]))
        if "moisture" in self._ai_parsed:
            self.moisture_entry.delete(0, "end")
            self.moisture_entry.insert(0, str(self._ai_parsed["moisture"]))
        self.calculate_net_weight()
        messagebox.showinfo(
            "Đã áp dụng",
            f"✅ Đã điền kết quả AI vào form:\n"
            f"  • Tạp chất: {self._ai_parsed.get('impurity', '?')}%\n"
            f"  • Độ ẩm:    {self._ai_parsed.get('moisture', '?')}%\n\n"
            "Vui lòng kiểm tra lại trước khi xác nhận giao dịch.")

    # ══════════════════════════════════════════════
    # DATA LOADING
    # ══════════════════════════════════════════════
    def load_data(self):
        self.load_farmers()
        self.load_products()
        self.load_transactions()

    def load_farmers(self):
        farmers = self.db.get_farmers(self.user_id)
        names = [f"{f['name']} - {f.get('phone', '')}" for f in farmers]
        self.farmer_combo.configure(values=names or ["Chưa có nông dân"])
        self.farmers_data = {
            f"{f['name']} - {f.get('phone', '')}": f["id"] for f in farmers
        }

    def load_products(self):
        products = self.db.get_products(self.user_id)
        names = [p["name"] for p in products]
        self.product_combo.configure(values=names or ["Chưa có sản phẩm"])
        self.products_data = {p["name"]: p["id"] for p in products}
        self.rules_map = {"Mặc định (theo sản phẩm)": None}

    def load_rules_for_product(self):
        product_name = self.product_combo.get()
        if product_name not in getattr(self, "products_data", {}):
            self.rule_combo.configure(values=["Mặc định (theo sản phẩm)"])
            return
        product_id = self.products_data[product_name]
        rules  = self.db.get_grading_rules(self.user_id, product_id)
        labels = ["Mặc định (theo sản phẩm)"]
        self.rules_map = {"Mặc định (theo sản phẩm)": None}
        for r in rules:
            label = r.get("rule_name") or f"Quy tắc #{r.get('id', '')[:8]}"
            labels.append(label)
            self.rules_map[label] = r
        self.rule_combo.configure(values=labels)
        self.rule_combo.set(labels[0])

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Cấu hình tag màu
        self.tree.tag_configure("paid", foreground="#27ae60")
        self.tree.tag_configure("debt", foreground="#e74c3c", font=("Arial", 10, "bold"))
        self.tree.tag_configure("amount_high", foreground="#e67e22", font=("Arial", 10, "bold"))
        self.tree.tag_configure("amount_low", foreground="#7f8c8d")

        for trans in self.db.get_transactions(self.user_id):
            farmer_name  = trans.get("farmers", {}).get("name", "N/A")
            product_name = trans.get("products", {}).get("name", "N/A")
            status_text = "✅" if trans["payment_status"] == "paid" else "📝"
            amount = trans.get('total_amount', 0) or 0

            # Chọn tag dựa trên trạng thái và số tiền
            if trans["payment_status"] == "paid":
                row_tag = "paid"
            else:
                row_tag = "debt"

            self.tree.insert("", "end", tags=(row_tag, trans["id"]), values=(
                str(trans.get("created_at", ""))[:10],
                farmer_name, product_name,
                f"{trans.get('net_weight', 0):,.1f}",
                f"{amount:,.0f}",
                status_text,
            ))

    def search_transactions(self):
        q = self.search_entry.get().lower()
        for item in self.tree.get_children():
            vals = str(self.tree.item(item)["values"]).lower()
            if q in vals:
                self.tree.reattach(item, "", "end")
                self.tree.see(item)
            else:
                self.tree.detach(item)

    # ══════════════════════════════════════════════
    # BUSINESS LOGIC
    # ══════════════════════════════════════════════
    def calculate_net_weight(self, event=None):
        try:
            gross    = float(self.gross_entry.get()    or 0)
            package  = float(self.package_entry.get()  or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            raw_net  = max(0, gross - package)

            product_name = self.product_combo.get()
            rule = None
            if hasattr(self, "rules_map"):
                rule = self.rules_map.get(self.rule_combo.get())
            if rule is None and product_name in getattr(self, "products_data", {}):
                rules = self.db.get_grading_rules(
                    self.user_id, self.products_data[product_name])
                rule = rules[0] if rules else None

            if rule:
                res = self.business_logic.calculate_net_weight(
                    gross, package, moisture, impurity, rule)
                net = res["net_weight"]
                self._subtracted_kg = max(0, raw_net - net)
            else:
                net = raw_net
                self._subtracted_kg = 0

            self._net_weight = net
        except ValueError:
            self._net_weight    = 0
            self._subtracted_kg = 0
        self._update_display()

    def calculate_total(self, event=None):
        self._update_display()

    def _update_display(self):
        try:
            unit_price = float(self.price_entry.get() or 0)
        except ValueError:
            unit_price = 0
        total = self._net_weight * unit_price
        self.lbl_subtracted.configure(text=f"{self._subtracted_kg:,.1f}")
        self.lbl_net.configure(text=f"{self._net_weight:,.1f}")
        self.lbl_total.configure(text=f"{total:,.0f} ₫")

    def on_product_change(self, choice):
        self.load_rules_for_product()
        self.calculate_net_weight()

    def save_transaction(self):
        try:
            farmer_name = self.farmer_combo.get()
            if farmer_name not in getattr(self, "farmers_data", {}):
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn nông dân")
                return
            product_name = self.product_combo.get()
            if product_name not in getattr(self, "products_data", {}):
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm")
                return

            gross_weight   = float(self.gross_entry.get()    or 0)
            package_weight = float(self.package_entry.get()  or 0)
            moisture       = float(self.moisture_entry.get() or 0)
            impurity       = float(self.impurity_entry.get() or 0)
            unit_price     = float(self.price_entry.get()    or 0)
            net_weight     = self._net_weight
            total_amount   = net_weight * unit_price

            is_valid, error = self.business_logic.validate_transaction({
                "gross_weight":      gross_weight,
                "package_weight":    package_weight,
                "unit_price":        unit_price,
                "measured_moisture": moisture,
                "measured_impurity": impurity,
            })
            if not is_valid:
                messagebox.showwarning("Cảnh báo", error)
                return

            from database.models import Transaction
            transaction = Transaction(
                id=None, user_id=self.user_id,
                farmer_id=self.farmers_data[farmer_name],
                product_id=self.products_data[product_name],
                gross_weight=gross_weight, package_weight=package_weight,
                measured_moisture=moisture, measured_impurity=impurity,
                net_weight=net_weight, unit_price=unit_price,
                total_amount=total_amount,
                payment_status=self.payment_var.get(),
            )
            if self.db.create_transaction(transaction):
                messagebox.showinfo("Thành công", "✅ Đã lưu giao dịch!")
                self.clear_form()
                self.load_transactions()
                self.tabview.set("  📋 Danh sách  ")
            else:
                messagebox.showerror("Lỗi", "Không thể lưu giao dịch")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def clear_form(self):
        self.farmer_combo.set("")
        self.product_combo.set("")
        for e in (self.gross_entry, self.package_entry,
                  self.moisture_entry, self.impurity_entry, self.price_entry):
            e.delete(0, "end")
        self.payment_var.set("paid")
        self._net_weight    = 0
        self._subtracted_kg = 0
        self._update_display()

        self._image_path = None
        self._ai_parsed  = {}
        self.lbl_img_status.configure(
            text="📷  Chưa có ảnh — nhấn để tải lên",
            text_color=T.TEXT_MUTED)
        self.btn_analyze.configure(state="disabled", text="🔍 Phân tích AI")
        self.lbl_ai_result.configure(
            text="Kết quả phân tích sẽ hiển thị ở đây",
            text_color=T.TEXT_MUTED)
        self.btn_apply_result.pack_forget()