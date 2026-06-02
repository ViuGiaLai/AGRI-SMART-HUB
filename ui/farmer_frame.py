# -*- coding: utf-8 -*-
# ui/farmer_frame.py
import customtkinter as ctk
from tkinter import messagebox, ttk, Menu
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Farmer

class FarmerFrame(ctk.CTkFrame):
    """Quản lý danh sách nông dân và công nợ"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db_manager = db_manager
        self.user_id = user_id
        self.current_farmer = None
        
        self.setup_ui()
        self.load_farmers()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#2ecc71", "#1a5d1a"))
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="👨‍🌾 QUẢN LÝ NÔNG DÂN & CÔNG NỢ",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(pady=15)
        
        # Main container with grid
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        self.main_container.grid_columnconfigure(0, weight=0)  # Left fixed
        self.main_container.grid_columnconfigure(1, weight=1)  # Right expands
        
        # Left panel - Form (fixed width)
        self.left_panel = ctk.CTkFrame(self.main_container, width=350, corner_radius=15)
        self.left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=10)
        
        # Right panel - List (expands)
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        
        self.create_form_panel()
        self.create_list_panel()
        self.create_debt_panel()
    
    def create_form_panel(self):
        """Tạo panel nhập thông tin nông dân"""
        # Configure left_panel grid
        self.left_panel.grid_rowconfigure(1, weight=1)
        
        # Form title
        self.form_title = ctk.CTkLabel(
            self.left_panel,
            text="📝 THÔNG TIN NÔNG DÂN",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.form_title.pack(pady=(20, 15))
        
        # Form frame
        self.form_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=20)
        
        # Họ tên
        self.name_label = ctk.CTkLabel(self.form_frame, text="👤 Họ và tên:", font=ctk.CTkFont(size=14, weight="bold"))
        self.name_label.pack(anchor="w", pady=(0, 8))
        self.name_entry = ctk.CTkEntry(self.form_frame, height=40, font=ctk.CTkFont(size=13), placeholder_text="Nhập tên nông dân")
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Số điện thoại
        self.phone_label = ctk.CTkLabel(self.form_frame, text="📞 Số điện thoại:", font=ctk.CTkFont(size=14, weight="bold"))
        self.phone_label.pack(anchor="w", pady=(0, 8))
        self.phone_entry = ctk.CTkEntry(self.form_frame, height=40, font=ctk.CTkFont(size=13), placeholder_text="Nhập số điện thoại")
        self.phone_entry.pack(fill="x", pady=(0, 15))
        
        # Địa chỉ
        self.address_label = ctk.CTkLabel(self.form_frame, text="📕 Địa chỉ:", font=ctk.CTkFont(size=14, weight="bold"))
        self.address_label.pack(anchor="w", pady=(0, 8))
        self.address_entry = ctk.CTkEntry(self.form_frame, height=40, placeholder_text="Nhập địa chỉ (xã/huyện)")
        self.address_entry.pack(fill="x", pady=(0, 15))
        
        # Ghi chú
        self.note_label = ctk.CTkLabel(self.form_frame, text="📝 Ghi chú:", font=ctk.CTkFont(size=13, weight="bold"))
        self.note_label.pack(anchor="w", pady=(0, 5))
        self.note_entry = ctk.CTkTextbox(self.form_frame, height=60)
        self.note_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.button_frame.pack(fill="x")
        
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="💾 THÊM MỚI",
            command=self.save_farmer,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60"
        )
        self.save_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.update_button = ctk.CTkButton(
            self.button_frame,
            text="🔄 CẬP NHẬT",
            command=self.update_farmer,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3498db"
        )
        self.update_button.pack(side="left", expand=True, fill="x", padx=5)
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="❌ HỦY",
            command=self.cancel_edit,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#95a5a6"
        )
        self.cancel_button.pack(side="left", expand=True, fill="x", padx=(5, 0))
    
    def create_list_panel(self):
        """Tạo panel danh sách nông dân"""
        # Configure right_panel grid
        self.right_panel.grid_rowconfigure(2, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # Search frame
        self.search_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        self.search_label = ctk.CTkLabel(self.search_frame, text="🔍 Tìm kiếm:", font=ctk.CTkFont(size=12))
        self.search_label.pack(side="left", padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Nhập tên hoặc số điện thoại", width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.search_farmers)
        
        self.search_button = ctk.CTkButton(self.search_frame, text="Tìm", command=self.search_farmers, width=80)
        self.search_button.pack(side="left")
        
        self.refresh_button = ctk.CTkButton(
            self.search_frame, 
            text="🔄", 
            command=self.load_farmers, 
            width=40,
            fg_color="#3498db"
        )
        self.refresh_button.pack(side="right")
        
        # Treeview frame (expands)
        self.tree_frame = ctk.CTkFrame(self.right_panel)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("ID", "Tên nông dân", "Số điện thoại", "Địa chỉ", "Công nợ (VNĐ)", "Ngày tạo")
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show="headings",
            height=15,
            yscrollcommand=self.scrollbar.set
        )
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Adjust column widths
        self.tree.column("ID", width=0, stretch=False)  # Hide ID column
        self.tree.column("Tên nông dân", width=180)
        self.tree.column("Số điện thoại", width=120)
        self.tree.column("Địa chỉ", width=200)
        self.tree.column("Công nợ (VNĐ)", width=150)
        self.tree.column("Ngày tạo", width=120)
        
        self.tree.pack(fill="both", expand=True)
        self.scrollbar.config(command=self.tree.yview)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_farmer_select)
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        
        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Xóa nông dân", command=self.delete_farmer)
        self.context_menu.add_command(label="Xem lịch sử giao dịch", command=self.view_transaction_history)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def create_debt_panel(self):
        """Tạo panel hiển thị tổng kết công nợ"""
        self.debt_frame = ctk.CTkFrame(self.right_panel, corner_radius=10, fg_color=("#f8f9fa", "#1a1a1a"))
        self.debt_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        self.debt_title = ctk.CTkLabel(
            self.debt_frame,
            text="💰 TỔNG KẾT CÔNG NỢ",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.debt_title.pack(pady=(10, 5))
        
        self.debt_stats_frame = ctk.CTkFrame(self.debt_frame, fg_color="transparent")
        self.debt_stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Stats will be displayed here
        self.total_debt_label = ctk.CTkLabel(
            self.debt_stats_frame,
            text="Tổng nợ: 0 VNĐ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        )
        self.total_debt_label.pack(side="left", expand=True)
        
        self.farmers_in_debt_label = ctk.CTkLabel(
            self.debt_stats_frame,
            text="Số hộ nợ: 0",
            font=ctk.CTkFont(size=12)
        )
        self.farmers_in_debt_label.pack(side="right", expand=True)
    
    def load_farmers(self):
        """Tải danh sách nông dân từ database"""
        farmers = self.db_manager.get_farmers(self.user_id)
        self.update_treeview(farmers)
        self.update_debt_stats(farmers)
    
    def search_farmers(self, event=None):
        """Tìm kiếm nông dân"""
        search_text = self.search_entry.get()
        farmers = self.db_manager.get_farmers(self.user_id, search=search_text)
        self.update_treeview(farmers)
    
    def update_treeview(self, farmers):
        """Cập nhật treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add farmers
        for farmer in farmers:
            self.tree.insert("", "end", values=(
                farmer['id'],
                farmer['name'],
                farmer.get('phone', ''),
                farmer.get('address', ''),
                f"{farmer.get('total_debt', 0):,.0f}",
                farmer.get('created_at', '')[:10] if farmer.get('created_at') else ''
            ))
    
    def update_debt_stats(self, farmers):
        """Cập nhật thống kê công nợ"""
        total_debt = sum(f.get('total_debt', 0) for f in farmers)
        farmers_in_debt = len([f for f in farmers if f.get('total_debt', 0) > 0])
        
        self.total_debt_label.configure(text=f"💰 Tổng nợ: {total_debt:,.0f} VNĐ")
        self.farmers_in_debt_label.configure(text=f"👥 Số hộ nợ: {farmers_in_debt}")
        
        # Change color if debt is high
        if total_debt > 100000000:  # 100 triệu
            self.total_debt_label.configure(text_color="#e74c3c")
        else:
            self.total_debt_label.configure(text_color="#f39c12")
    
    def save_farmer(self):
        """Thêm nông dân mới"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên nông dân!")
            return
        
        farmer = Farmer(
            id=None,
            user_id=self.user_id,
            name=name,
            phone=self.phone_entry.get().strip(),
            address=self.address_entry.get().strip(),
            total_debt=0,
            note=self.note_entry.get("1.0", "end-1c").strip()
        )
        
        result = self.db_manager.create_farmer(farmer)
        if result:
            messagebox.showinfo("Thành công", f"Đã thêm nông dân {name}!")
            self.clear_form()
            self.load_farmers()
        else:
            messagebox.showerror("Lỗi", "Không thể thêm nông dân!")
    
    def update_farmer(self):
        """Cập nhật thông tin nông dân"""
        if not self.current_farmer:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nông dân để cập nhật!")
            return
        
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên nông dân!")
            return
        
        update_data = {
            'name': name,
            'phone': self.phone_entry.get().strip(),
            'address': self.address_entry.get().strip(),
            'note': self.note_entry.get("1.0", "end-1c").strip()
        }
        
        if self.db_manager.update_farmer(self.current_farmer['id'], update_data):
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin!")
            self.cancel_edit()
            self.load_farmers()
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật!")
    
    def delete_farmer(self):
        """Xóa nông dân"""
        if not self.current_farmer:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nông dân để xóa!")
            return
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa nông dân {self.current_farmer['name']}?"):
            if self.db_manager.delete_farmer(self.current_farmer['id']):
                messagebox.showinfo("Thành công", "Đã xóa nông dân!")
                self.cancel_edit()
                self.load_farmers()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa nông dân!")
    
    def on_farmer_select(self, event):
        """Xử lý khi chọn nông dân"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0])['values']
            farmer_id = values[0]
            
            # Get full farmer data
            farmers = self.db_manager.get_farmers(self.user_id)
            for farmer in farmers:
                if farmer['id'] == farmer_id:
                    self.current_farmer = farmer
                    self.display_farmer_info(farmer)
                    break
    
    def display_farmer_info(self, farmer):
        """Hiển thị thông tin nông dân lên form"""
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, farmer['name'])
        
        self.phone_entry.delete(0, 'end')
        self.phone_entry.insert(0, farmer.get('phone', ''))
        
        self.address_entry.delete(0, 'end')
        self.address_entry.insert(0, farmer.get('address', ''))
        
        self.note_entry.delete("1.0", "end")
        self.note_entry.insert("1.0", farmer.get('note', ''))
        
        self.save_button.configure(text="💾 THÊM MỚI", fg_color="#27ae60")
        self.update_button.configure(state="normal")
    
    def on_double_click(self, event):
        """Xử lý double click để xem chi tiết"""
        self.show_farmer_details()
    
    def show_farmer_details(self):
        """Hiển thị chi tiết nông dân trong cửa sổ mới"""
        if not self.current_farmer:
            return
        
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Chi tiết nông dân: {self.current_farmer['name']}")
        detail_window.geometry("500x400")
        detail_window.transient(self)
        detail_window.grab_set()
        
        # Display details
        main_frame = ctk.CTkFrame(detail_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        info_text = f"""
        📋 THÔNG TIN CHI TIẾT
        
        👤 Họ tên: {self.current_farmer['name']}
        📞 Điện thoại: {self.current_farmer.get('phone', 'Chưa cập nhật')}
        📍 Địa chỉ: {self.current_farmer.get('address', 'Chưa cập nhật')}
        💰 Công nợ hiện tại: {self.current_farmer.get('total_debt', 0):,.0f} VNĐ
        📝 Ghi chú: {self.current_farmer.get('note', 'Không có')}
        
        🕐 Ngày tạo: {self.current_farmer.get('created_at', '')[:19] if self.current_farmer.get('created_at') else 'Không rõ'}
        """
        
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_label.pack(pady=20)
        
        close_btn = ctk.CTkButton(main_frame, text="Đóng", command=detail_window.destroy, width=100)
        close_btn.pack(pady=10)
    
    def view_transaction_history(self):
        """Xem lịch sử giao dịch của nông dân"""
        if not self.current_farmer:
            return
        
        # This will be implemented when transaction frame is ready
        messagebox.showinfo("Thông báo", "Tính năng đang phát triển!")
    
    def show_context_menu(self, event):
        """Hiển thị context menu"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def clear_form(self):
        """Xóa form nhập liệu"""
        self.name_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.address_entry.delete(0, 'end')
        self.note_entry.delete("1.0", "end")
        self.current_farmer = None
        self.save_button.configure(text="💾 THÊM MỚI", fg_color="#27ae60")
    
    def cancel_edit(self):
        """Hủy chỉnh sửa"""
        self.clear_form()
        self.tree.selection_remove(self.tree.selection())