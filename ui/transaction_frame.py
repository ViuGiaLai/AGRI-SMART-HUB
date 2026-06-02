# -*- coding: utf-8 -*-
"""Giao dịch thu mua — form 2 cột + kết quả tạm tính."""
import customtkinter as ctk
from tkinter import messagebox, ttk
from database.db_manager import DatabaseManager
from core.business import BusinessLogic, FarmerDebtManager
from ui import theme as T


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
        self.setup_ui()
        self.after(100, self.load_data)

    def setup_ui(self):
        # Header
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

        # Tab: Nhập mới | Danh sách
        self.tabview = ctk.CTkTabview(
            self, corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD, segmented_button_fg_color=T.SECONDARY,
            segmented_button_selected_color=T.PRIMARY,
        )
        self.tabview.pack(fill="both", expand=True, padx=24, pady=(8, 24))
        self.tab_new = self.tabview.add("  ➕ Nhập giao dịch  ")
        self.tab_list = self.tabview.add("  📋 Danh sách  ")

        self._build_new_transaction_tab()
        self._build_list_tab()

    def _build_new_transaction_tab(self):
        form_wrap = ctk.CTkFrame(self.tab_new, fg_color="transparent")
        form_wrap.pack(fill="both", expand=True, padx=8, pady=8)
        form_wrap.grid_columnconfigure(0, weight=1)
        form_wrap.grid_columnconfigure(1, weight=1)
        form_wrap.grid_rowconfigure(0, weight=1)

        # —— Cột trái: nông dân & cân ——
        left = ctk.CTkFrame(
            form_wrap, corner_radius=T.CORNER_RADIUS, fg_color=("#fafbfc", "#2a2a2a")
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)
        self._section_title(left, "👨‍🌾 Thông tin nông dân & cân")

        self.farmer_combo = self._labeled_combo(
            left, "Nông dân", ["Chọn nông dân..."], command=None
        )
        self.product_combo = self._labeled_combo(
            left, "Sản phẩm", ["Chọn sản phẩm..."], command=self.on_product_change
        )
        self.gross_entry = self._labeled_entry(left, "⚖️ Tổng cân (kg)")
        self.package_entry = self._labeled_entry(left, "📦 Bao bì (kg)")
        self.price_entry = self._labeled_entry(left, "💰 Đơn giá (VNĐ/kg)")

        pay_frame = ctk.CTkFrame(left, fg_color="transparent")
        pay_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(
            pay_frame, text="Hình thức thanh toán",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(anchor="w")
        self.payment_var = ctk.StringVar(value="paid")
        ctk.CTkRadioButton(
            pay_frame, text="Thanh toán ngay", variable=self.payment_var, value="paid",
            command=self.calculate_total, fg_color=T.PRIMARY,
        ).pack(anchor="w", pady=4)
        ctk.CTkRadioButton(
            pay_frame, text="Ghi nợ", variable=self.payment_var, value="debt",
            command=self.calculate_total, fg_color=T.PRIMARY,
        ).pack(anchor="w")

        # —— Cột phải: chất lượng & quy tắc ——
        right = ctk.CTkFrame(
            form_wrap, corner_radius=T.CORNER_RADIUS, fg_color=("#fafbfc", "#2a2a2a")
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        self._section_title(right, "🔬 Chỉ số chất lượng & trừ lùi")

        self.moisture_entry = self._labeled_entry(right, "💧 Độ ẩm (%)")
        self.impurity_entry = self._labeled_entry(right, "🧹 Tạp chất (%)")

        rule_frame = ctk.CTkFrame(right, fg_color="transparent")
        rule_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(
            rule_frame, text="Quy tắc trừ lùi",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(anchor="w")
        self.rule_combo = ctk.CTkComboBox(
            rule_frame, values=["Mặc định (theo sản phẩm)"],
            height=42, corner_radius=T.CORNER_RADIUS_SM,
            font=ctk.CTkFont(size=13), command=lambda _: self.calculate_net_weight(),
        )
        self.rule_combo.pack(fill="x", pady=(6, 0))

        for entry in (
            self.gross_entry, self.package_entry,
            self.moisture_entry, self.impurity_entry, self.price_entry,
        ):
            entry.bind("<KeyRelease>", self._on_input_change)

        # —— Kết quả tạm tính ——
        result = ctk.CTkFrame(
            form_wrap, corner_radius=T.CORNER_RADIUS,
            fg_color=(T.PRIMARY_LIGHT, "#1e3d2a"),
            border_width=2, border_color=T.PRIMARY,
        )
        result.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        inner = ctk.CTkFrame(result, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        inner.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_subtracted = ctk.CTkLabel(
            inner, text="0", font=ctk.CTkFont(size=36, weight="bold"), text_color=T.DANGER,
        )
        self.lbl_subtracted.grid(row=0, column=0)
        ctk.CTkLabel(
            inner, text="kg bị trừ", font=ctk.CTkFont(size=13), text_color=T.TEXT_MUTED,
        ).grid(row=1, column=0)

        self.lbl_net = ctk.CTkLabel(
            inner, text="0", font=ctk.CTkFont(size=36, weight="bold"), text_color=T.SECONDARY,
        )
        self.lbl_net.grid(row=0, column=1)
        ctk.CTkLabel(
            inner, text="kg cân tịnh", font=ctk.CTkFont(size=13), text_color=T.TEXT_MUTED,
        ).grid(row=1, column=1)

        self.lbl_total = ctk.CTkLabel(
            inner, text="0", font=ctk.CTkFont(size=36, weight="bold"), text_color=T.PRIMARY,
        )
        self.lbl_total.grid(row=0, column=2)
        ctk.CTkLabel(
            inner, text="VNĐ khách nhận", font=ctk.CTkFont(size=13), text_color=T.TEXT_MUTED,
        ).grid(row=1, column=2)

        # Nút xác nhận
        btn_row = ctk.CTkFrame(form_wrap, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        self.save_button = ctk.CTkButton(
            btn_row,
            text="✓  XÁC NHẬN GIAO DỊCH",
            command=self.save_transaction,
            height=56,
            corner_radius=T.CORNER_RADIUS,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color=T.PRIMARY,
            hover_color=T.PRIMARY_DARK,
        )
        self.save_button.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Xóa form", command=self.clear_form,
            height=56, corner_radius=T.CORNER_RADIUS,
            fg_color=T.SECONDARY_LIGHT, hover_color=T.SECONDARY,
            font=ctk.CTkFont(size=14),
        ).pack(side="right", padx=(8, 0))

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

        tree_frame = ctk.CTkFrame(self.tab_list, corner_radius=T.CORNER_RADIUS_SM)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        columns = ("Ngày", "Nông dân", "Sản phẩm", "Cân tịnh", "Thành tiền", "TT")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            height=18, yscrollcommand=scrollbar.set,
        )
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        scrollbar.config(command=self.tree.yview)

        ctk.CTkButton(
            self.tab_list, text="🔄 Làm mới", command=self.load_transactions,
            height=42, fg_color=T.SECONDARY_LIGHT,
        ).pack(fill="x", padx=8, pady=8)

    def _section_title(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=15, weight="bold"), text_color=T.SECONDARY,
        ).pack(anchor="w", padx=20, pady=(16, 12))

    def _labeled_entry(self, parent, label):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(
            f, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(anchor="w")
        entry = ctk.CTkEntry(
            f, height=42, corner_radius=T.CORNER_RADIUS_SM, font=ctk.CTkFont(size=13),
        )
        entry.pack(fill="x", pady=(4, 0))
        return entry

    def _labeled_combo(self, parent, label, values, command):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(
            f, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(anchor="w")
        combo = ctk.CTkComboBox(
            f, values=values, height=42, corner_radius=T.CORNER_RADIUS_SM,
            font=ctk.CTkFont(size=13), command=command,
        )
        combo.pack(fill="x", pady=(4, 0))
        return combo

    def _on_input_change(self, event=None):
        self.calculate_net_weight()

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
        rules = self.db.get_grading_rules(self.user_id, product_id)
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
        for trans in self.db.get_transactions(self.user_id):
            farmer_name = trans.get("farmers", {}).get("name", "N/A")
            product_name = trans.get("products", {}).get("name", "N/A")
            status = "✅" if trans["payment_status"] == "paid" else "📝"
            self.tree.insert("", "end", values=(
                str(trans.get("created_at", ""))[:10],
                farmer_name, product_name,
                f"{trans.get('net_weight', 0):,.1f}",
                f"{trans.get('total_amount', 0):,.0f}",
                status,
            ), tags=(trans["id"],))

    def search_transactions(self):
        q = self.search_entry.get().lower()
        for item in self.tree.get_children():
            vals = str(self.tree.item(item)["values"]).lower()
            if q in vals:
                self.tree.reattach(item, "", "end")
                self.tree.see(item)
            else:
                self.tree.detach(item)

    def calculate_net_weight(self, event=None):
        try:
            gross = float(self.gross_entry.get() or 0)
            package = float(self.package_entry.get() or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            raw_net = max(0, gross - package)

            product_name = self.product_combo.get()
            rule = None
            if hasattr(self, "rules_map"):
                rule = self.rules_map.get(self.rule_combo.get())
            if rule is None and product_name in getattr(self, "products_data", {}):
                rules = self.db.get_grading_rules(
                    self.user_id, self.products_data[product_name]
                )
                rule = rules[0] if rules else None

            if rule:
                result = self.business_logic.calculate_net_weight(
                    gross, package, moisture, impurity, rule
                )
                net = result["net_weight"]
                self._subtracted_kg = max(0, raw_net - net)
            else:
                net = raw_net
                self._subtracted_kg = 0

            self._net_weight = net
            self._update_result_display()
        except ValueError:
            self._net_weight = 0
            self._subtracted_kg = 0
            self._update_result_display()

    def calculate_total(self, event=None):
        self._update_result_display()

    def _update_result_display(self):
        unit_price = 0
        try:
            unit_price = float(self.price_entry.get() or 0)
        except ValueError:
            pass
        total = self._net_weight * unit_price
        self.lbl_subtracted.configure(text=f"{self._subtracted_kg:,.1f}")
        self.lbl_net.configure(text=f"{self._net_weight:,.1f}")
        self.lbl_total.configure(text=f"{total:,.0f}")

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

            gross_weight = float(self.gross_entry.get() or 0)
            package_weight = float(self.package_entry.get() or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            unit_price = float(self.price_entry.get() or 0)
            net_weight = self._net_weight
            total_amount = net_weight * unit_price

            is_valid, error = self.business_logic.validate_transaction({
                "gross_weight": gross_weight,
                "package_weight": package_weight,
                "unit_price": unit_price,
                "measured_moisture": moisture,
                "measured_impurity": impurity,
            })
            if not is_valid:
                messagebox.showwarning("Cảnh báo", error)
                return

            from database.models import Transaction
            transaction = Transaction(
                id=None,
                user_id=self.user_id,
                farmer_id=self.farmers_data[farmer_name],
                product_id=self.products_data[product_name],
                gross_weight=gross_weight,
                package_weight=package_weight,
                measured_moisture=moisture,
                measured_impurity=impurity,
                net_weight=net_weight,
                unit_price=unit_price,
                total_amount=total_amount,
                payment_status=self.payment_var.get(),
            )
            if self.db.create_transaction(transaction):
                messagebox.showinfo("Thành công", "Đã lưu giao dịch!")
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
        for e in (
            self.gross_entry, self.package_entry,
            self.moisture_entry, self.impurity_entry, self.price_entry,
        ):
            e.delete(0, "end")
        self.payment_var.set("paid")
        self._net_weight = 0
        self._subtracted_kg = 0
        self._update_result_display()
