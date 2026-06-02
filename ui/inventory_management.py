# -*- coding: utf-8 -*-
"""Quản lý kho — điều chỉnh tồn, kiểm kê, cảnh báo."""
import json
import os
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, ttk

from database.db_manager import DatabaseManager
from core.notification_system import NotificationSystem
from ui import theme as T


class InventoryManagementFrame(ctk.CTkFrame):
    """Quản lý tồn kho và kiểm kê."""

    DEFAULT_PRICE_ESTIMATE = 45_000

    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, fg_color=T.BG_MAIN, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.current_product = None
        self.products_data = {}
        self._stock_by_product: dict = {}
        self.notifier = NotificationSystem(
            db_manager, user_id, root_window=self.winfo_toplevel(),
        )

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(
            hdr, text="Quản lý kho",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="Điều chỉnh tồn · kiểm kê · theo dõi cảnh báo",
            font=ctk.CTkFont(size=13), text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(8, 24))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.right_panel = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._build_adjustment_form()
        self._build_inventory_table()
        self._build_alerts_panel()

    def _build_adjustment_form(self):
        ctk.CTkLabel(
            self.left_panel, text="Điều chỉnh tồn kho",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=T.SECONDARY,
        ).pack(anchor="w", padx=20, pady=(16, 12))

        self.product_combo = self._field_combo(
            self.left_panel, "Sản phẩm *",
            ["-- Chọn sản phẩm --"], self.on_product_select,
        )

        info = ctk.CTkFrame(
            self.left_panel, corner_radius=T.CORNER_RADIUS_SM,
            fg_color=(T.PRIMARY_LIGHT, "#1e3d28"),
        )
        info.pack(fill="x", padx=20, pady=8)
        self.current_stock_label = ctk.CTkLabel(
            info, text="Tồn kho hiện tại: — kg",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=T.PRIMARY,
        )
        self.current_stock_label.pack(pady=12)

        ctk.CTkLabel(
            self.left_panel, text="Loại điều chỉnh",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(anchor="w", padx=20, pady=(8, 4))
        self.adjustment_type = ctk.StringVar(value="loss")
        rf = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        rf.pack(fill="x", padx=20)
        ctk.CTkRadioButton(
            rf, text="Hao hụt (giảm)", variable=self.adjustment_type, value="loss",
            fg_color=T.DANGER,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            rf, text="Bổ sung (tăng)", variable=self.adjustment_type, value="gain",
            fg_color=T.PRIMARY,
        ).pack(side="left")

        self.quantity_entry = self._field_entry(self.left_panel, "Số lượng (kg) *")
        self.reason_combo = self._field_combo(
            self.left_panel, "Lý do",
            [
                "-- Chọn lý do --",
                "Bay hơi ẩm tự nhiên",
                "Hao hụt vận chuyển",
                "Chế biến, sàng lọc",
                "Hư hỏng, mốc",
                "Kiểm kê chênh lệch",
                "Lấy mẫu QC",
                "Xuất bán / nhập bổ sung",
                "Khác",
            ],
            None,
        )
        self.reason_combo.set("-- Chọn lý do --")

        nf = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        nf.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(nf, text="Ghi chú", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.note_entry = ctk.CTkTextbox(nf, height=56, corner_radius=T.CORNER_RADIUS_SM)
        self.note_entry.pack(fill="x", pady=(4, 0))

        bf = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        bf.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(
            bf, text="✓ XÁC NHẬN ĐIỀU CHỈNH",
            command=self.confirm_adjustment, height=50,
            corner_radius=T.CORNER_RADIUS, fg_color=T.ACCENT, hover_color=T.ACCENT_DARK,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            bf, text="Nhập lại", command=self.clear_form, height=40,
            fg_color=T.SECONDARY_LIGHT,
        ).pack(fill="x")

    def _build_inventory_table(self):
        top = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            top, text="Danh sách tồn kho",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=T.SECONDARY,
        ).pack(side="left")
        ctk.CTkButton(
            top, text="🔄", width=40, height=36,
            command=self.load_inventory, fg_color=T.PRIMARY,
        ).pack(side="right")

        sf = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        sf.pack(fill="x", padx=16, pady=(0, 8))
        self.search_entry = ctk.CTkEntry(
            sf, placeholder_text="🔍 Tìm sản phẩm...", height=40,
            corner_radius=T.CORNER_RADIUS_SM,
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_inventory())

        tf = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        tf.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        vsb = ttk.Scrollbar(tf)
        vsb.pack(side="right", fill="y")
        cols = ("id", "Sản phẩm", "Tồn kho", "Đơn vị", "Giá trị ước tính", "Cập nhật")
        self.tree = ttk.Treeview(
            tf, columns=cols, show="headings", height=14, yscrollcommand=vsb.set,
        )
        vsb.config(command=self.tree.yview)
        widths = {"id": 0, "Sản phẩm": 180, "Tồn kho": 100, "Đơn vị": 60,
                  "Giá trị ước tính": 130, "Cập nhật": 110}
        for c in cols:
            self.tree.heading(c, text=c if c != "id" else "")
            self.tree.column(c, width=widths.get(c, 100), anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_inventory_select)

    def _build_alerts_panel(self):
        panel = ctk.CTkFrame(
            self.right_panel, corner_radius=T.CORNER_RADIUS_SM,
            fg_color=("#fff8e6", "#3d3010"), border_width=1, border_color=T.ACCENT,
        )
        panel.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(
            panel, text="⚠️ Cảnh báo tồn kho",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=T.ACCENT,
        ).pack(anchor="w", padx=12, pady=(10, 4))
        self.alert_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", height=72)
        self.alert_scroll.pack(fill="x", padx=8, pady=(0, 10))

    def _field_entry(self, parent, label):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        e = ctk.CTkEntry(f, height=42, corner_radius=T.CORNER_RADIUS_SM)
        e.pack(fill="x", pady=(4, 0))
        return e

    def _field_combo(self, parent, label, values, command):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        c = ctk.CTkComboBox(
            f, values=values, height=42, corner_radius=T.CORNER_RADIUS_SM,
            command=command,
        )
        c.pack(fill="x", pady=(4, 0))
        return c

    def load_data(self):
        self.load_products()
        self.load_inventory()

    def load_products(self):
        try:
            products = self.db.get_products(self.user_id)
            if products:
                names = [p["name"] for p in products]
                self.product_combo.configure(values=names)
                self.products_data = {p["name"]: p["id"] for p in products}
            else:
                self.product_combo.configure(values=["-- Chưa có sản phẩm --"])
                self.products_data = {}
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tải sản phẩm: {e}")

    def load_inventory(self):
        try:
            inventory = self.db.get_inventory(self.user_id)
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._stock_by_product.clear()

            for inv in inventory or []:
                name = inv.get("products", {}).get("name", "N/A")
                stock = inv.get("current_stock", 0) or 0
                self._stock_by_product[name] = stock
                value = stock * self.DEFAULT_PRICE_ESTIMATE
                self.tree.insert("", "end", values=(
                    inv.get("id", ""),
                    name,
                    f"{stock:,.1f}",
                    "kg",
                    f"{value:,.0f}",
                    self._fmt_dt(inv.get("last_updated")),
                ))
            self.check_alerts()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Tải tồn kho: {e}")

    def search_inventory(self):
        q = self.search_entry.get().lower()
        for item in self.tree.get_children():
            vals = self.tree.item(item)["values"]
            name = str(vals[1]).lower() if len(vals) > 1 else ""
            if not q or q in name:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def on_product_select(self, choice=None):
        name = self.product_combo.get()
        stock = self._stock_by_product.get(name)
        if stock is not None:
            self.current_stock_label.configure(text=f"Tồn kho hiện tại: {stock:,.1f} kg")
            self.current_product = {"name": name, "stock": stock}
        else:
            self.current_stock_label.configure(text="Tồn kho hiện tại: — kg")
            self.current_product = None

    def on_inventory_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        if len(vals) > 1:
            self.product_combo.set(vals[1])
            self.on_product_select()

    def confirm_adjustment(self):
        if not self.current_product:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm!")
            return
        try:
            qty = float(self.quantity_entry.get() or 0)
            if qty <= 0:
                messagebox.showwarning("Cảnh báo", "Số lượng phải > 0!")
                return
            reason = self.reason_combo.get()
            if reason == "-- Chọn lý do --":
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn lý do!")
                return

            adj = self.adjustment_type.get()
            cur = self.current_product["stock"]
            note = self.note_entry.get("1.0", "end-1c").strip()

            if adj == "loss":
                if qty > cur and not messagebox.askyesno(
                    "Xác nhận", f"Hao hụt {qty} kg > tồn {cur:.1f} kg. Tiếp tục?"
                ):
                    return
                new_stock = max(0, cur - qty)
                delta_txt = f"GIẢM {qty:,.1f} kg"
            else:
                new_stock = cur + qty
                delta_txt = f"TĂNG {qty:,.1f} kg"

            msg = (
                f"Sản phẩm: {self.current_product['name']}\n"
                f"Tồn hiện tại: {cur:,.1f} kg → {new_stock:,.1f} kg\n"
                f"Điều chỉnh: {delta_txt}\nLý do: {reason}"
            )
            if not messagebox.askyesno("Xác nhận điều chỉnh", msg):
                return

            pid = self.products_data[self.current_product["name"]]
            ok = self.db.update_inventory(self.user_id, pid, qty, is_add=(adj == "gain"))
            if ok:
                self._log_adjustment(self.current_product["name"], qty, adj, reason, note)
                messagebox.showinfo("Thành công", "Đã cập nhật tồn kho!")
                self.clear_form()
                self.load_inventory()
                self.on_product_select()
            else:
                messagebox.showerror("Lỗi", "Không thể cập nhật tồn kho!")
        except ValueError:
            messagebox.showwarning("Cảnh báo", "Số lượng không hợp lệ!")

    def check_alerts(self):
        for w in self.alert_scroll.winfo_children():
            w.destroy()

        alerts = self.notifier.collect_dashboard_alerts()
        stock_alerts = [a for a in alerts if "tồn" in a[1].lower() or "hết" in a[1].lower()]

        if not stock_alerts:
            ctk.CTkLabel(
                self.alert_scroll, text="✅ Tồn kho ổn định",
                font=ctk.CTkFont(size=12), text_color=T.PRIMARY,
            ).pack(anchor="w", padx=4)
            return

        for level, msg, _ in stock_alerts:
            ctk.CTkLabel(
                self.alert_scroll, text=f"{level}  {msg}",
                font=ctk.CTkFont(size=11), anchor="w", wraplength=400,
            ).pack(anchor="w", pady=2)

    def _log_adjustment(self, product, qty, adj_type, reason, note):
        log_file = f"stock_adjustment_log_{self.user_id}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "product": product, "quantity": qty, "type": adj_type,
            "reason": reason, "note": note,
        }
        try:
            logs = []
            if os.path.exists(log_file):
                with open(log_file, encoding="utf-8") as f:
                    logs = json.load(f)
            logs.append(entry)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger_msg = f"log adjustment failed: {e}"
            print(logger_msg)

    def _fmt_dt(self, dt_value):
        if not dt_value:
            return datetime.now().strftime("%d/%m/%Y")
        try:
            if isinstance(dt_value, str) and "T" in dt_value:
                return datetime.fromisoformat(dt_value.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        return str(dt_value)[:16]

    def clear_form(self):
        self.product_combo.set("")
        self.quantity_entry.delete(0, "end")
        self.reason_combo.set("-- Chọn lý do --")
        self.note_entry.delete("1.0", "end")
        self.adjustment_type.set("loss")
        self.current_product = None
        self.current_stock_label.configure(text="Tồn kho hiện tại: — kg")
