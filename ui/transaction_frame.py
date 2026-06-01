# -*- coding: utf-8 -*-
# ui/transaction_frame.py
import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from database.db_manager import DatabaseManager
from core.business import BusinessLogic, FarmerDebtManager
from core.calculator import calculate_coffee_subtraction, calculate_pepper_subtraction

class TransactionFrame(ctk.CTkFrame):
    """Frame quản lý giao dịch thu mua"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.business_logic = BusinessLogic()
        self.debt_manager = FarmerDebtManager(db_manager)
        
        self.setup_ui()
        # Defer loading data slightly so the UI can render first and remain responsive
        self.after(100, self.load_data)
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="📋 QUẢN LÝ GIAO DỊCH THU MUA",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=20)
        
        # Main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel - Form nhập liệu
        self.left_panel = ctk.CTkFrame(self.main_container, width=400)
        self.left_panel.pack(side="left", fill="both", padx=(0, 10), pady=10)
        self.left_panel.pack_propagate(False)
        
        # Right panel - Danh sách giao dịch
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)
        
        self.create_input_form()
        self.create_transaction_list()
    
    def create_input_form(self):
        """Tạo form nhập liệu"""
        # Form title
        form_title = ctk.CTkLabel(
            self.left_panel,
            text="THÔNG TIN GIAO DỊCH",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        form_title.pack(pady=(10, 15))
        
        # Farmer selection
        self.farmer_label = ctk.CTkLabel(self.left_panel, text="👨‍🌾 Nông dân:", font=ctk.CTkFont(size=14, weight="bold"))
        self.farmer_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.farmer_combo = ctk.CTkComboBox(
            self.left_panel,
            values=["Chọn nông dân..."],
            width=320,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.farmer_combo.pack(pady=(8, 15), padx=20)
        
        # Product selection
        self.product_label = ctk.CTkLabel(self.left_panel, text="🌱 Sản phẩm:", font=ctk.CTkFont(size=14, weight="bold"))
        self.product_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.product_combo = ctk.CTkComboBox(
            self.left_panel,
            values=["Chọn sản phẩm..."],
            width=320,
            height=40,
            font=ctk.CTkFont(size=13),
            command=self.on_product_change
        )
        self.product_combo.pack(pady=(8, 15), padx=20)
        
        # Weight inputs
        self.create_weight_inputs()
        
        # Quality inputs
        self.create_quality_inputs()
        
        # Price and payment
        self.create_price_payment_inputs()
        
        # Action buttons
        self.create_action_buttons()
    
    def create_weight_inputs(self):
        """Tạo các input về cân nặng"""
        weight_frame = ctk.CTkFrame(self.left_panel)
        weight_frame.pack(fill="x", padx=20, pady=5)
        
        self.gross_label = ctk.CTkLabel(weight_frame, text="⚖️ Tổng cân (kg):", font=ctk.CTkFont(size=14, weight="bold"))
        self.gross_label.grid(row=0, column=0, sticky="w", pady=8)
        
        self.gross_entry = ctk.CTkEntry(weight_frame, width=250, height=40, font=ctk.CTkFont(size=13))
        self.gross_entry.grid(row=0, column=1, padx=10, pady=8)
        self.gross_entry.bind('<KeyRelease>', self.calculate_net_weight)
        
        self.package_label = ctk.CTkLabel(weight_frame, text="📦 Bao bì (kg):", font=ctk.CTkFont(size=14, weight="bold"))
        self.package_label.grid(row=1, column=0, sticky="w", pady=8)
        
        self.package_entry = ctk.CTkEntry(weight_frame, width=250, height=40, font=ctk.CTkFont(size=13))
        self.package_entry.grid(row=1, column=1, padx=10, pady=8)
        self.package_entry.bind('<KeyRelease>', self.calculate_net_weight)
    
    def create_quality_inputs(self):
        """Tạo các input về chất lượng"""
        quality_frame = ctk.CTkFrame(self.left_panel)
        quality_frame.pack(fill="x", padx=20, pady=5)
        
        self.moisture_label = ctk.CTkLabel(quality_frame, text="💧 Độ ẩm (%):", font=ctk.CTkFont(size=14, weight="bold"))
        self.moisture_label.grid(row=0, column=0, sticky="w", pady=8)
        
        self.moisture_entry = ctk.CTkEntry(quality_frame, width=250, height=40, font=ctk.CTkFont(size=13))
        self.moisture_entry.grid(row=0, column=1, padx=10, pady=8)
        self.moisture_entry.bind('<KeyRelease>', self.calculate_net_weight)
        
        self.impurity_label = ctk.CTkLabel(quality_frame, text="🧹 Tạp chất (%):", font=ctk.CTkFont(size=14, weight="bold"))
        self.impurity_label.grid(row=1, column=0, sticky="w", pady=8)
        
        self.impurity_entry = ctk.CTkEntry(quality_frame, width=250, height=40, font=ctk.CTkFont(size=13))
        self.impurity_entry.grid(row=1, column=1, padx=10, pady=8)
        self.impurity_entry.bind('<KeyRelease>', self.calculate_net_weight)
        
        # Kết quả tính toán
        self.net_weight_label = ctk.CTkLabel(
            quality_frame,
            text="🏆 Cân tịnh: 0 kg",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#27ae60"
        )
        self.net_weight_label.grid(row=2, column=0, columnspan=2, pady=10)
    
    def create_price_payment_inputs(self):
        """Tạo input về giá và thanh toán"""
        price_frame = ctk.CTkFrame(self.left_panel)
        price_frame.pack(fill="x", padx=20, pady=5)
        
        self.price_label = ctk.CTkLabel(price_frame, text="💰 Đơn giá (VNĐ/kg):", font=ctk.CTkFont(size=14, weight="bold"))
        self.price_label.grid(row=0, column=0, sticky="w", pady=8)
        
        self.price_entry = ctk.CTkEntry(price_frame, width=250, height=40, font=ctk.CTkFont(size=13))
        self.price_entry.grid(row=0, column=1, padx=10, pady=8)
        self.price_entry.bind('<KeyRelease>', self.calculate_total)
        
        self.payment_label = ctk.CTkLabel(price_frame, text="💵 Hình thức thanh toán:", font=ctk.CTkFont(size=14, weight="bold"))
        self.payment_label.grid(row=1, column=0, sticky="w", pady=8)
        
        self.payment_var = ctk.StringVar(value="paid")
        self.payment_paid = ctk.CTkRadioButton(
            price_frame, text="Thanh toán ngay",
            variable=self.payment_var, value="paid",
            command=self.calculate_total
        )
        self.payment_paid.grid(row=1, column=1, sticky="w")
        
        self.payment_debt = ctk.CTkRadioButton(
            price_frame, text="Ghi nợ",
            variable=self.payment_var, value="debt",
            command=self.calculate_total
        )
        self.payment_debt.grid(row=2, column=1, sticky="w")
        
        # Total amount
        self.total_label = ctk.CTkLabel(
            price_frame,
            text="Tổng tiền: 0 VNĐ",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e74c3c"
        )
        self.total_label.grid(row=3, column=0, columnspan=2, pady=10)
    
    def create_action_buttons(self):
        """Tạo các nút hành động"""
        button_frame = ctk.CTkFrame(self.left_panel)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        self.save_button = ctk.CTkButton(
            button_frame,
            text="💾 LƯU GIAO DỊCH",
            command=self.save_transaction,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#27ae60"
        )
        self.save_button.pack(fill="x", pady=8)
        
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="🗑️ XÓA FORM",
            command=self.clear_form,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="#7f8c8d"
        )
        self.clear_button.pack(fill="x", pady=8)
    
    def create_transaction_list(self):
        """Tạo bảng danh sách giao dịch"""
        # Search frame
        search_frame = ctk.CTkFrame(self.right_panel)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Tìm kiếm giao dịch...",
            width=400,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.pack(side="left", padx=5)
        
        self.search_button = ctk.CTkButton(
            search_frame,
            text="Tìm",
            command=self.search_transactions,
            width=100,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.search_button.pack(side="left", padx=5)
        
        # Treeview for transactions
        self.create_treeview()
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            self.right_panel,
            text="🔄 Làm mới",
            command=self.load_transactions,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.refresh_button.pack(pady=10, padx=10, fill="x")
    
    def create_treeview(self):
        """Tạo Treeview hiển thị giao dịch"""
        # Frame for treeview
        tree_frame = ctk.CTkFrame(self.right_panel)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("Ngày", "Nông dân", "Sản phẩm", "Cân tịnh(kg)", "Đơn giá", "Thành tiền", "Thanh toán")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=20,
            yscrollcommand=scrollbar.set
        )
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.column("Ngày", width=120)
        self.tree.column("Nông dân", width=150)
        self.tree.column("Sản phẩm", width=120)
        self.tree.column("Thành tiền", width=150)
        
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind double click
        self.tree.bind("<Double-Button-1>", self.on_transaction_select)
    
    def load_data(self):
        """Tải dữ liệu ban đầu"""
        self.load_farmers()
        self.load_products()
        self.load_transactions()
    
    def load_farmers(self):
        """Tải danh sách nông dân"""
        farmers = self.db.get_farmers(self.user_id)
        farmer_names = [f"{f['name']} - {f.get('phone', '')}" for f in farmers]
        self.farmer_combo.configure(values=farmer_names if farmer_names else ["Chưa có nông dân"])
        self.farmers_data = {f"{f['name']} - {f.get('phone', '')}": f['id'] for f in farmers}
    
    def load_products(self):
        """Tải danh sách sản phẩm"""
        products = self.db.get_products(self.user_id)
        product_names = [p['name'] for p in products]
        self.product_combo.configure(values=product_names if product_names else ["Chưa có sản phẩm"])
        self.products_data = {p['name']: p['id'] for p in products}
    
    def load_transactions(self):
        """Tải danh sách giao dịch"""
        transactions = self.db.get_transactions(self.user_id)
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add transactions
        for trans in transactions:
            farmer_name = trans.get('farmers', {}).get('name', 'N/A')
            product_name = trans.get('products', {}).get('name', 'N/A')
            payment_status = "✅ Đã trả" if trans['payment_status'] == 'paid' else "📝 Ghi nợ"
            
            self.tree.insert("", "end", values=(
                trans['created_at'][:10],
                farmer_name,
                product_name,
                f"{trans['net_weight']:,.1f}",
                f"{trans['unit_price']:,.0f}",
                f"{trans['total_amount']:,.0f}",
                payment_status
            ), tags=(trans['id'],))
        
        # Update summary
        self.update_summary()
    
    def search_transactions(self):
        """Tìm kiếm giao dịch"""
        search_text = self.search_entry.get().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if search_text in str(values).lower():
                self.tree.see(item)
            else:
                self.tree.detach(item)
    
    def calculate_net_weight(self, event=None):
        """Tính cân tịnh tự động"""
        try:
            gross = float(self.gross_entry.get() or 0)
            package = float(self.package_entry.get() or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            
            # Lấy quy tắc trừ lùi cho sản phẩm
            product_name = self.product_combo.get()
            if product_name in self.products_data:
                product_id = self.products_data[product_name]
                rules = self.db.get_grading_rules(self.user_id, product_id)
                if rules:
                    rule = rules[0]
                    result = self.business_logic.calculate_net_weight(
                        gross, package, moisture, impurity, rule
                    )
                    self.net_weight_label.configure(text=f"🏆 Cân tịnh: {result['net_weight']:.2f} kg")
                    self.calculate_total()
                    return
            
            # Fallback to default calculation
            net = gross - package
            self.net_weight_label.configure(text=f"🏆 Cân tịnh: {net:.2f} kg")
            self.calculate_total()
            
        except ValueError:
            self.net_weight_label.configure(text="🏆 Cân tịnh: 0 kg")
    
    def calculate_total(self, event=None):
        """Tính tổng tiền"""
        try:
            net_text = self.net_weight_label.cget("text")
            net_weight = float(net_text.split(":")[1].strip().split(" ")[0])
            unit_price = float(self.price_entry.get() or 0)
            
            total = net_weight * unit_price
            self.total_label.configure(text=f"Tổng tiền: {total:,.0f} VNĐ")
            
        except (ValueError, IndexError):
            self.total_label.configure(text="Tổng tiền: 0 VNĐ")
    
    def on_product_change(self, choice):
        """Xử lý khi thay đổi sản phẩm"""
        self.calculate_net_weight()
    
    def save_transaction(self):
        """Lưu giao dịch"""
        try:
            # Get farmer ID
            farmer_name = self.farmer_combo.get()
            if farmer_name not in self.farmers_data:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn nông dân")
                return
            
            farmer_id = self.farmers_data[farmer_name]
            
            # Get product ID
            product_name = self.product_combo.get()
            if product_name not in self.products_data:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm")
                return
            
            product_id = self.products_data[product_name]
            
            # Get values
            gross_weight = float(self.gross_entry.get() or 0)
            package_weight = float(self.package_entry.get() or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            unit_price = float(self.price_entry.get() or 0)
            payment_status = self.payment_var.get()
            
            # Calculate net weight
            net_text = self.net_weight_label.cget("text")
            net_weight = float(net_text.split(":")[1].strip().split(" ")[0])
            total_amount = net_weight * unit_price
            
            # Validate
            is_valid, error = self.business_logic.validate_transaction({
                'gross_weight': gross_weight,
                'package_weight': package_weight,
                'unit_price': unit_price,
                'measured_moisture': moisture,
                'measured_impurity': impurity
            })
            
            if not is_valid:
                messagebox.showwarning("Cảnh báo", error)
                return
            
            # Save transaction
            from database.models import Transaction
            transaction = Transaction(
                id=None,
                user_id=self.user_id,
                farmer_id=farmer_id,
                product_id=product_id,
                gross_weight=gross_weight,
                package_weight=package_weight,
                measured_moisture=moisture,
                measured_impurity=impurity,
                net_weight=net_weight,
                unit_price=unit_price,
                total_amount=total_amount,
                payment_status=payment_status
            )
            
            result = self.db.create_transaction(transaction)
            
            if result:
                messagebox.showinfo("Thành công", "Đã lưu giao dịch thành công!")
                self.clear_form()
                self.load_transactions()
            else:
                messagebox.showerror("Lỗi", "Không thể lưu giao dịch")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
    
    def update_summary(self):
        """Cập nhật thống kê"""
        summary = self.db.get_transaction_summary(self.user_id)
        # Hiển thị thống kê ở đây (có thể thêm label mới)
    
    def clear_form(self):
        """Xóa form nhập liệu"""
        self.farmer_combo.set("")
        self.product_combo.set("")
        self.gross_entry.delete(0, 'end')
        self.package_entry.delete(0, 'end')
        self.moisture_entry.delete(0, 'end')
        self.impurity_entry.delete(0, 'end')
        self.price_entry.delete(0, 'end')
        self.payment_var.set("paid")
        self.net_weight_label.configure(text="🏆 Cân tịnh: 0 kg")
        self.total_label.configure(text="Tổng tiền: 0 VNĐ")
    
    def on_transaction_select(self, event):
        """Xử lý khi chọn giao dịch"""
        selection = self.tree.selection()
        if selection:
            # TODO: Hiển thị chi tiết giao dịch
            pass