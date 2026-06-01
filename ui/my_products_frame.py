# -*- coding: utf-8 -*-
# ui/my_products_frame.py
import customtkinter as ctk
from tkinter import messagebox, ttk, Menu
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Product
from typing import Optional, Dict, Any

class MyProductsFrame(ctk.CTkFrame):
    """Quản lý danh sách sản phẩm của người dùng"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db_manager = db_manager
        self.user_id = user_id
        self.current_product: Optional[Dict] = None
        self.products: list = []
        self.filtered_products: list = []
        
        self.setup_ui()
        self.load_products()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main scrollable frame
        self.main_scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_scroll.grid(row=0, column=0, sticky="nsew")
        
        # Header
        self.header_frame = ctk.CTkFrame(
            self.main_scroll, 
            corner_radius=15, 
            fg_color=("#2ecc71", "#1a5d1a")
        )
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Header content
        self.header_content = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_content.pack(fill="x", padx=20, pady=15)
        
        self.title_label = ctk.CTkLabel(
            self.header_content,
            text="📦 QUẢN LÝ SẢN PHẨM",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(side="left")
        
        # Stats label
        self.stats_label = ctk.CTkLabel(
            self.header_content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        self.stats_label.pack(side="right")
        
        # Main container
        self.main_container = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel - Form
        self.left_panel = ctk.CTkFrame(self.main_container, width=450, corner_radius=15)
        self.left_panel.pack(side="left", fill="both", padx=(0, 10), pady=10)
        self.left_panel.pack_propagate(False)
        
        # Right panel - List
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)
        
        self.create_form_panel()
        self.create_list_panel()
        self.create_status_bar()
    
    def create_form_panel(self):
        """Tạo panel nhập thông tin sản phẩm"""
        # Form title with icon
        self.form_header = ctk.CTkFrame(self.left_panel, fg_color=("#3498db", "#2980b9"), corner_radius=15)
        self.form_header.pack(fill="x", padx=1, pady=(1, 0))
        
        self.form_title = ctk.CTkLabel(
            self.form_header,
            text="📝 THÔNG TIN SẢN PHẨM",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        self.form_title.pack(pady=12)
        
        # Form frame
        self.form_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tên sản phẩm (required)
        self.name_label = ctk.CTkLabel(
            self.form_frame, 
            text="📦 Tên sản phẩm *", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.name_label.pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(
            self.form_frame, 
            height=42, 
            font=ctk.CTkFont(size=13), 
            placeholder_text="Nhập tên sản phẩm (vd: Cà phê nhân, Hồ tiêu đen...)"
        )
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Danh mục
        self.category_label = ctk.CTkLabel(
            self.form_frame, 
            text="🏷️ Danh mục", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.category_label.pack(anchor="w", pady=(0, 5))
        
        self.category_combo = ctk.CTkComboBox(
            self.form_frame,
            height=42,
            font=ctk.CTkFont(size=13),
            values=["Cà phê", "Hồ tiêu", "Điều", "Cacao", "Lúa gạo", "Ngô", "Sắn", "Khác"],
            state="readonly"
        )
        self.category_combo.set("Chọn danh mục")
        self.category_combo.pack(fill="x", pady=(0, 15))
        
        # Đơn vị đo
        self.unit_label = ctk.CTkLabel(
            self.form_frame, 
            text="📏 Đơn vị đo", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.unit_label.pack(anchor="w", pady=(0, 5))
        
        self.unit_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.unit_frame.pack(fill="x", pady=(0, 15))
        
        self.unit_var = ctk.StringVar(value="kg")
        units = ["kg", "tấn", "gram", "lít", "thùng", "bao"]
        
        for i, unit in enumerate(units):
            radio = ctk.CTkRadioButton(
                self.unit_frame,
                text=unit,
                variable=self.unit_var,
                value=unit,
                font=ctk.CTkFont(size=12)
            )
            radio.pack(side="left", padx=(0, 10))
        
        # Giá tham khảo
        self.price_label = ctk.CTkLabel(
            self.form_frame, 
            text="💰 Giá tham khảo (VNĐ/kg)", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.price_label.pack(anchor="w", pady=(0, 5))
        
        self.price_entry = ctk.CTkEntry(
            self.form_frame,
            height=40,
            font=ctk.CTkFont(size=13),
            placeholder_text="Nhập giá tham khảo (nếu có)"
        )
        self.price_entry.pack(fill="x", pady=(0, 15))
        
        # Ghi chú
        self.note_label = ctk.CTkLabel(
            self.form_frame, 
            text="📌 Ghi chú", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.note_label.pack(anchor="w", pady=(0, 5))
        
        self.note_entry = ctk.CTkTextbox(
            self.form_frame,
            height=80,
            font=ctk.CTkFont(size=12)
        )
        self.note_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Thêm button
        self.add_btn = ctk.CTkButton(
            self.buttons_frame,
            text="✅ THÊM SẢN PHẨM",
            command=self.add_product,
            height=45,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2ecc71", "#27ae60")
        )
        self.add_btn.pack(fill="x", pady=(0, 10))
        
        # Buttons row
        self.action_row = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
        self.action_row.pack(fill="x")
        
        self.clear_btn = ctk.CTkButton(
            self.action_row,
            text="🔄 NHẬP LẠI",
            command=self.clear_form,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=("#95a5a6", "#7f8c8d")
        )
        self.clear_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.import_btn = ctk.CTkButton(
            self.action_row,
            text="📥 NHẬP MẪU",
            command=self.import_sample_products,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=("#3498db", "#2980b9")
        )
        self.import_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    def create_list_panel(self):
        """Tạo panel hiển thị danh sách sản phẩm"""
        # List header
        self.list_header = ctk.CTkFrame(self.right_panel, fg_color=("#34495e", "#2c3e50"), corner_radius=15)
        self.list_header.pack(fill="x", padx=1, pady=(1, 0))
        
        self.list_title = ctk.CTkLabel(
            self.list_header,
            text="📋 DANH SÁCH SẢN PHẨM",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        self.list_title.pack(pady=12)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=15, pady=(15, 10))
        
        # Search frame
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=8)
        self.search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.search_icon = ctk.CTkLabel(self.search_frame, text="🔍", font=("Segoe UI Emoji", 14))
        self.search_icon.pack(side="left", padx=(10, 5), pady=8)
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            height=35,
            font=ctk.CTkFont(size=12),
            placeholder_text="Tìm kiếm sản phẩm...",
            fg_color="transparent",
            border_width=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_products())
        
        # Filter buttons
        self.filter_all_btn = ctk.CTkButton(
            self.toolbar,
            text="Tất cả",
            command=lambda: self.filter_by_category("all"),
            width=60,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.filter_all_btn.pack(side="left", padx=(0, 5))
        
        self.filter_coffee_btn = ctk.CTkButton(
            self.toolbar,
            text="Cà phê",
            command=lambda: self.filter_by_category("Cà phê"),
            width=70,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#8e44ad"
        )
        self.filter_coffee_btn.pack(side="left", padx=(0, 5))
        
        self.filter_pepper_btn = ctk.CTkButton(
            self.toolbar,
            text="Hồ tiêu",
            command=lambda: self.filter_by_category("Hồ tiêu"),
            width=70,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#e67e22"
        )
        self.filter_pepper_btn.pack(side="left")
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.toolbar,
            text="📊 Xuất Excel",
            command=self.export_to_excel,
            width=100,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#27ae60"
        )
        self.export_btn.pack(side="right")
        
        # Treeview frame
        self.tree_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Create treeview with modern style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Treeview", 
                       font=('Arial', 10),
                       rowheight=30,
                       background="#ffffff",
                       fieldbackground="#ffffff",
                       foreground="#2c3e50")
        style.configure("Custom.Treeview.Heading", 
                       font=('Arial', 11, 'bold'),
                       background="#34495e",
                       foreground="white")
        style.map('Custom.Treeview', 
                 background=[('selected', '#2ecc71')],
                 foreground=[('selected', 'white')])
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.h_scrollbar = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("STT", "Tên", "Danh mục", "Đơn vị", "Giá TK", "Ngày tạo"),
            height=15,
            show='headings',
            style="Custom.Treeview",
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )
        
        # Define columns
        self.tree.column("STT", width=50, anchor="center")
        self.tree.column("Tên", width=200)
        self.tree.column("Danh mục", width=120, anchor="center")
        self.tree.column("Đơn vị", width=80, anchor="center")
        self.tree.column("Giá TK", width=120, anchor="center")
        self.tree.column("Ngày tạo", width=100, anchor="center")
        
        # Create headings
        self.tree.heading("STT", text="STT")
        self.tree.heading("Tên", text="Tên sản phẩm")
        self.tree.heading("Danh mục", text="Danh mục")
        self.tree.heading("Đơn vị", text="Đơn vị")
        self.tree.heading("Giá TK", text="Giá tham khảo")
        self.tree.heading("Ngày tạo", text="Ngày tạo")
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind("<Double-1>", lambda e: self.edit_product())
        self.tree.bind("<Delete>", lambda e: self.delete_product())
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)
    
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = ctk.CTkFrame(self.main_scroll, height=30, corner_radius=0)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="✅ Sẵn sàng",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray50")
        )
        self.status_label.pack(side="left", padx=20, pady=5)
        
        self.status_time = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray50")
        )
        self.status_time.pack(side="right", padx=20, pady=5)
        
        # Update time
        self.update_status_time()
    
    def update_status_time(self):
        """Cập nhật thời gian trên status bar"""
        self.status_time.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_status_time)
    
    def update_status(self, message: str, is_error: bool = False):
        """Cập nhật status message"""
        prefix = "❌" if is_error else "✅"
        self.status_label.configure(text=f"{prefix} {message}")
        self.after(3000, lambda: self.status_label.configure(text="✅ Sẵn sàng"))
    
    def setup_shortcuts(self):
        """Thiết lập phím tắt"""
        self.bind("<Control-n>", lambda e: self.clear_form())
        self.bind("<Control-s>", lambda e: self.add_product())
        self.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.bind("<F5>", lambda e: self.load_products())
    
    def load_products(self):
        """Tải danh sách sản phẩm từ database"""
        try:
            if self.db_manager:
                result = self.db_manager.supabase.table('products')\
                    .select("*")\
                    .eq('user_id', self.user_id)\
                    .order('created_at', desc=True)\
                    .execute()
                self.products = result.data if result.data else []
            else:
                self.products = []
            
            self.filtered_products = self.products.copy()
            self.refresh_list()
            self.update_stats()
            self.update_status(f"Đã tải {len(self.products)} sản phẩm")
            
        except Exception as e:
            self.update_status(f"Lỗi tải sản phẩm: {e}", is_error=True)
            messagebox.showerror("Lỗi", f"Lỗi khi tải sản phẩm: {e}")
    
    def refresh_list(self):
        """Làm mới danh sách sản phẩm"""
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add items
        for idx, product in enumerate(self.filtered_products, 1):
            created_date = product.get('created_at', '')
            if created_date:
                try:
                    dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    created_date = dt.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Format price
            price = product.get('reference_price', 0)
            price_text = f"{price:,.0f}" if price else "---"
            
            self.tree.insert(
                "",
                "end",
                iid=product.get('id', ''),
                values=(
                    idx,
                    product.get('name', ''),
                    product.get('category', '---'),
                    product.get('base_unit', 'kg'),
                    price_text,
                    created_date
                )
            )
    
    def filter_products(self):
        """Lọc danh sách sản phẩm theo tên tìm kiếm"""
        search_text = self.search_entry.get().lower().strip()
        
        if not search_text:
            self.filtered_products = self.products.copy()
        else:
            self.filtered_products = [
                p for p in self.products 
                if search_text in p.get('name', '').lower() 
                or search_text in p.get('category', '').lower()
            ]
        
        self.refresh_list()
        self.update_status(f"Tìm thấy {len(self.filtered_products)}/{len(self.products)} sản phẩm")
    
    def filter_by_category(self, category: str):
        """Lọc sản phẩm theo danh mục"""
        if category == "all":
            self.filtered_products = self.products.copy()
        else:
            self.filtered_products = [p for p in self.products if p.get('category') == category]
        
        self.refresh_list()
        self.update_status(f"Đã lọc: {len(self.filtered_products)} sản phẩm")
    
    def update_stats(self):
        """Cập nhật thống kê"""
        total = len(self.products)
        categories = {}
        for p in self.products:
            cat = p.get('category', 'Khác')
            categories[cat] = categories.get(cat, 0) + 1
        
        stats_text = f"📊 {total} sản phẩm | {len(categories)} danh mục"
        self.stats_label.configure(text=stats_text)
    
    def validate_form(self) -> bool:
        """Kiểm tra dữ liệu form"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên sản phẩm!")
            self.name_entry.focus()
            return False
        
        if len(name) < 2:
            messagebox.showwarning("Cảnh báo", "Tên sản phẩm phải có ít nhất 2 ký tự!")
            return False
        
        category = self.category_combo.get()
        if not category or category == "Chọn danh mục":
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn danh mục sản phẩm!")
            return False
        
        return True
    
    def add_product(self):
        """Thêm sản phẩm mới"""
        if not self.validate_form():
            return
        
        name = self.name_entry.get().strip()
        category = self.category_combo.get()
        unit = self.unit_var.get()
        
        try:
            # Tạo sản phẩm mới - chỉ sử dụng các field có trong schema
            product = {
                "user_id": self.user_id,
                "name": name,
                "category": category if category != "Chọn danh mục" else None,
                "base_unit": unit,
                "created_at": datetime.now().isoformat()
            }
            
            # Lưu vào database
            if self.db_manager:
                result = self.db_manager.supabase.table('products').insert(product).execute()
                if result.data:
                    product['id'] = result.data[0].get('id')
                    self.products.insert(0, product)
                    self.filtered_products = self.products.copy()
                    self.refresh_list()
                    self.clear_form()
                    self.update_stats()
                    self.update_status(f"Đã thêm sản phẩm '{name}'")
                    messagebox.showinfo("Thành công", f"Đã thêm sản phẩm '{name}' thành công!")
            else:
                # Demo mode
                import uuid
                product['id'] = str(uuid.uuid4())
                self.products.insert(0, product)
                self.filtered_products = self.products.copy()
                self.refresh_list()
                self.clear_form()
                self.update_stats()
                self.update_status(f"Đã thêm sản phẩm '{name}' (demo mode)")
                messagebox.showinfo("Thành công", f"Đã thêm sản phẩm '{name}' thành công (demo mode)!")
        
        except Exception as e:
            self.update_status(f"Lỗi: {str(e)}", is_error=True)
            messagebox.showerror("Lỗi", f"Lỗi khi thêm sản phẩm: {e}")
    
    def edit_product(self):
        """Chỉnh sửa sản phẩm"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm để chỉnh sửa!")
            return
        
        product_id = selection[0]
        product = next((p for p in self.products if p.get('id') == product_id), None)
        
        if not product:
            return
        
        # Điền thông tin vào form
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, product.get('name', ''))
        
        self.category_combo.set(product.get('category', 'Khác'))
        self.unit_var.set(product.get('base_unit', 'kg'))
        
        # Set reference price
        self.price_entry.delete(0, 'end')
        if product.get('reference_price'):
            self.price_entry.insert(0, str(product.get('reference_price')))
        
        self.note_entry.delete("1.0", "end")
        if product.get('note'):
            self.note_entry.insert("1.0", product.get('note'))
        
        # Change button
        self.add_btn.configure(text="💾 CẬP NHẬT", command=lambda: self.update_product(product_id))
        self.current_product = product
    
    def update_product(self, product_id: str):
        """Cập nhật sản phẩm"""
        if not self.validate_form():
            return
        
        name = self.name_entry.get().strip()
        category = self.category_combo.get()
        unit = self.unit_var.get()
        note = self.note_entry.get("1.0", "end-1c").strip()
        
        price_text = self.price_entry.get().strip()
        reference_price = float(price_text) if price_text else None
        
        try:
            update_data = {
                "name": name,
                "category": category if category != "Chọn danh mục" else None,
                "base_unit": unit,
                "reference_price": reference_price,
                "note": note if note else None,
                "updated_at": datetime.now().isoformat()
            }
            
            if self.db_manager:
                self.db_manager.supabase.table('products')\
                    .update(update_data)\
                    .eq('id', product_id)\
                    .execute()
            
            # Cập nhật local
            for i, p in enumerate(self.products):
                if p.get('id') == product_id:
                    self.products[i].update(update_data)
                    break
            
            self.filtered_products = self.products.copy()
            self.refresh_list()
            self.clear_form()
            self.update_stats()
            self.update_status(f"Đã cập nhật sản phẩm '{name}'")
            messagebox.showinfo("Thành công", "Đã cập nhật sản phẩm thành công!")
        
        except Exception as e:
            self.update_status(f"Lỗi: {str(e)}", is_error=True)
            messagebox.showerror("Lỗi", f"Lỗi khi cập nhật sản phẩm: {e}")
    
    def delete_product(self):
        """Xóa sản phẩm"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm để xóa!")
            return
        
        product_id = selection[0]
        product = next((p for p in self.products if p.get('id') == product_id), None)
        
        if not product:
            return
        
        # Kiểm tra xem sản phẩm có đang được sử dụng không
        if self.db_manager:
            try:
                # Kiểm tra trong transactions
                trans_result = self.db_manager.supabase.table('transactions')\
                    .select('id')\
                    .eq('product_id', product_id)\
                    .limit(1)\
                    .execute()
                
                if trans_result.data:
                    messagebox.showwarning(
                        "Không thể xóa", 
                        f"Sản phẩm '{product.get('name')}' đã có giao dịch.\nVui lòng xóa các giao dịch liên quan trước!"
                    )
                    return
            except:
                pass
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa sản phẩm '{product.get('name')}'?"):
            try:
                if self.db_manager:
                    self.db_manager.supabase.table('products')\
                        .delete()\
                        .eq('id', product_id)\
                        .execute()
                
                self.products = [p for p in self.products if p.get('id') != product_id]
                self.filtered_products = self.products.copy()
                self.refresh_list()
                self.update_stats()
                self.update_status(f"Đã xóa sản phẩm '{product.get('name')}'")
                messagebox.showinfo("Thành công", "Đã xóa sản phẩm thành công!")
            
            except Exception as e:
                self.update_status(f"Lỗi: {str(e)}", is_error=True)
                messagebox.showerror("Lỗi", f"Lỗi khi xóa sản phẩm: {e}")
    
    def import_sample_products(self):
        """Nhập sản phẩm mẫu"""
        sample_products = [
            {"name": "Cà phê nhân Robusta", "category": "Cà phê", "base_unit": "kg", "reference_price": 45000},
            {"name": "Cà phê nhân Arabica", "category": "Cà phê", "base_unit": "kg", "reference_price": 85000},
            {"name": "Hồ tiêu đen", "category": "Hồ tiêu", "base_unit": "kg", "reference_price": 180000},
            {"name": "Hồ tiêu trắng", "category": "Hồ tiêu", "base_unit": "kg", "reference_price": 220000},
            {"name": "Điều nhân", "category": "Điều", "base_unit": "kg", "reference_price": 35000},
            {"name": "Cacao khô", "category": "Cacao", "base_unit": "kg", "reference_price": 28000},
        ]
        
        if messagebox.askyesno("Xác nhận", "Nhập 6 sản phẩm mẫu? (sẽ không trùng lặp nếu đã có)"):
            added = 0
            for sample in sample_products:
                # Kiểm tra trùng lặp
                exists = any(p.get('name') == sample['name'] for p in self.products)
                if not exists:
                    product = {
                        "user_id": self.user_id,
                        **sample,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    if self.db_manager:
                        result = self.db_manager.supabase.table('products').insert(product).execute()
                        if result.data:
                            product['id'] = result.data[0].get('id')
                            self.products.append(product)
                            added += 1
                    else:
                        import uuid
                        product['id'] = str(uuid.uuid4())
                        self.products.append(product)
                        added += 1
            
            self.filtered_products = self.products.copy()
            self.refresh_list()
            self.update_stats()
            self.update_status(f"Đã thêm {added} sản phẩm mẫu")
            messagebox.showinfo("Thành công", f"Đã thêm {added} sản phẩm mẫu!")
    
    def export_to_excel(self):
        """Xuất danh sách sản phẩm ra Excel"""
        if not self.products:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return
        
        try:
            import pandas as pd
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"san_pham_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                # Prepare data
                data = []
                for p in self.products:
                    data.append({
                        "Tên sản phẩm": p.get('name', ''),
                        "Danh mục": p.get('category', ''),
                        "Đơn vị": p.get('base_unit', 'kg'),
                        "Giá tham khảo": p.get('reference_price', 0),
                        "Ngày tạo": p.get('created_at', '')[:10] if p.get('created_at') else '',
                        "Ghi chú": p.get('note', '')
                    })
                
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False, sheet_name="Sản phẩm")
                
                self.update_status(f"Đã xuất {len(data)} sản phẩm ra Excel")
                messagebox.showinfo("Thành công", f"Đã xuất danh sách sản phẩm ra file:\n{filename}")
        
        except ImportError:
            messagebox.showerror("Lỗi", "Chưa cài đặt pandas! Vui lòng chạy: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xuất file: {e}")
    
    def on_product_select(self, event):
        """Xử lý khi chọn sản phẩm"""
        selection = self.tree.selection()
        if selection:
            # Hiển thị thông tin sản phẩm trong status bar
            values = self.tree.item(selection[0])['values']
            if values:
                self.update_status(f"Đã chọn: {values[1]}")
    
    def show_context_menu(self, event):
        """Hiển thị menu ngữ cảnh"""
        item = self.tree.identify_row(event.y)
        if not item:
            return        
        self.tree.selection_set(item)
        
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="✏️ Chỉnh sửa", command=self.edit_product)
        self.context_menu.add_command(label="🗑️ Xóa", command=self.delete_product)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Sao chép tên", command=self.copy_product_name)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Đóng")
        
        self.context_menu.post(event.x_root, event.y_root)
    
    def copy_product_name(self):
        """Sao chép tên sản phẩm"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0])['values']
            if values:
                self.clipboard_clear()
                self.clipboard_append(values[1])
                self.update_status(f"Đã sao chép: {values[1]}")
    
    def clear_form(self):
        """Xóa form"""
        self.name_entry.delete(0, 'end')
        self.category_combo.set("Chọn danh mục")
        self.unit_var.set("kg")
        self.price_entry.delete(0, 'end')
        self.note_entry.delete("1.0", "end")
        self.current_product = None
        self.add_btn.configure(text="✅ THÊM SẢN PHẨM", command=self.add_product)
        self.name_entry.focus()
        self.update_status("Đã xóa form, sẵn sàng nhập mới")