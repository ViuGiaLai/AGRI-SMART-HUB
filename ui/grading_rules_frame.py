# -*- coding: utf-8 -*-
# ui/grading_rules_frame.py
import customtkinter as ctk
from tkinter import messagebox
from database.db_manager import DatabaseManager
from database.models import GradingRule

class GradingRulesFrame(ctk.CTkFrame):
    """Quản lý quy tắc trừ lùi cho từng sản phẩm"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db_manager = db_manager
        self.user_id = user_id
        self.current_rule = None
        self.products = []
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#9b59b6", "#6c3483"))
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚙️ CẤU HÌNH QUY TẮC TRỪ LÙI",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(pady=15)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self.header_frame,
            text="Mỗi sản phẩm có thể có quy tắc trừ ẩm và tạp chất khác nhau",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        self.info_label.pack(pady=(0, 10))
        
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel - Product list
        self.left_panel = ctk.CTkFrame(self.main_container, width=300, corner_radius=15)
        self.left_panel.pack(side="left", fill="both", padx=(0, 10), pady=10)
        self.left_panel.pack_propagate(False)
        
        # Right panel - Rule configuration
        self.right_panel = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)
        
        self.create_product_panel()
        self.create_rule_panel()
    
    def create_product_panel(self):
        """Tạo panel danh sách sản phẩm"""
        self.product_title = ctk.CTkLabel(
            self.left_panel,
            text="📦 DANH SÁCH SẢN PHẨM",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.product_title.pack(pady=(15, 10))
        
        # Product list frame
        self.product_list_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.product_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add product button
        self.add_product_btn = ctk.CTkButton(
            self.left_panel,
            text="➕ Thêm sản phẩm mới",
            command=self.show_add_product_dialog,
            height=35,
            fg_color="#27ae60"
        )
        self.add_product_btn.pack(padx=10, pady=(0, 15), fill="x")
    
    def create_rule_panel(self):
        """Tạo panel cấu hình quy tắc"""
        # Rule title
        self.rule_title = ctk.CTkLabel(
            self.right_panel,
            text="📋 CẤU HÌNH QUY TẮC TRỪ LÙI",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.rule_title.pack(pady=(20, 15))
        
        # Rule form frame
        self.rule_form = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.rule_form.pack(fill="both", expand=True, padx=30)
        
        # Product selection (disabled, shows current product)
        self.product_display_label = ctk.CTkLabel(
            self.rule_form,
            text="Sản phẩm:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.product_display_label.pack(anchor="w", pady=(0, 5))
        
        self.product_display = ctk.CTkLabel(
            self.rule_form,
            text="Chưa chọn sản phẩm",
            font=ctk.CTkFont(size=13),
            text_color=("#2c3e50", "#ecf0f1")
        )
        self.product_display.pack(anchor="w", pady=(0, 15))
        
        # Moisture rules
        self.moisture_frame = ctk.CTkFrame(self.rule_form, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=10)
        self.moisture_frame.pack(fill="x", pady=(0, 15))
        
        self.moisture_title = ctk.CTkLabel(
            self.moisture_frame,
            text="💧 QUY TẮC TRỪ ẨM",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.moisture_title.pack(pady=(10, 10))
        
        # Standard moisture
        self.std_moisture_frame = ctk.CTkFrame(self.moisture_frame, fg_color="transparent")
        self.std_moisture_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.std_moisture_label = ctk.CTkLabel(
            self.std_moisture_frame,
            text="Độ ẩm tiêu chuẩn (%):",
            font=ctk.CTkFont(size=12)
        )
        self.std_moisture_label.pack(side="left")
        
        self.std_moisture_entry = ctk.CTkEntry(self.std_moisture_frame, width=150, placeholder_text="VD: 12.5")
        self.std_moisture_entry.pack(side="right", padx=(10, 0))
        
        # Moisture ratio
        self.moisture_ratio_frame = ctk.CTkFrame(self.moisture_frame, fg_color="transparent")
        self.moisture_ratio_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.moisture_ratio_label = ctk.CTkLabel(
            self.moisture_ratio_frame,
            text="Tỷ lệ trừ ẩm (1:?):",
            font=ctk.CTkFont(size=12)
        )
        self.moisture_ratio_label.pack(side="left")
        
        self.moisture_ratio_entry = ctk.CTkEntry(self.moisture_ratio_frame, width=150, placeholder_text="VD: 1.2")
        self.moisture_ratio_entry.pack(side="right", padx=(10, 0))
        
        self.moisture_help = ctk.CTkLabel(
            self.moisture_frame,
            text="💡 Ví dụ: Độ ẩm vượt 1% sẽ bị trừ 1.2% trọng lượng",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray50")
        )
        self.moisture_help.pack(pady=(0, 10))
        
        # Impurity rules
        self.impurity_frame = ctk.CTkFrame(self.rule_form, fg_color=("#f0f0f0", "#2b2b2b"), corner_radius=10)
        self.impurity_frame.pack(fill="x", pady=(0, 15))
        
        self.impurity_title = ctk.CTkLabel(
            self.impurity_frame,
            text="🧹 QUY TẮC TRỪ TẠP CHẤT",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.impurity_title.pack(pady=(10, 10))
        
        # Standard impurity
        self.std_impurity_frame = ctk.CTkFrame(self.impurity_frame, fg_color="transparent")
        self.std_impurity_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.std_impurity_label = ctk.CTkLabel(
            self.std_impurity_frame,
            text="Tạp chất tiêu chuẩn (%):",
            font=ctk.CTkFont(size=12)
        )
        self.std_impurity_label.pack(side="left")
        
        self.std_impurity_entry = ctk.CTkEntry(self.std_impurity_frame, width=150, placeholder_text="VD: 0.5")
        self.std_impurity_entry.pack(side="right", padx=(10, 0))
        
        # Impurity ratio
        self.impurity_ratio_frame = ctk.CTkFrame(self.impurity_frame, fg_color="transparent")
        self.impurity_ratio_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.impurity_ratio_label = ctk.CTkLabel(
            self.impurity_ratio_frame,
            text="Tỷ lệ trừ tạp chất (1:?):",
            font=ctk.CTkFont(size=12)
        )
        self.impurity_ratio_label.pack(side="left")
        
        self.impurity_ratio_entry = ctk.CTkEntry(self.impurity_ratio_frame, width=150, placeholder_text="VD: 1.0")
        self.impurity_ratio_entry.pack(side="right", padx=(10, 0))
        
        self.impurity_help = ctk.CTkLabel(
            self.impurity_frame,
            text="💡 Tạp chất vượt 1% sẽ bị trừ X% trọng lượng",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray50")
        )
        self.impurity_help.pack(pady=(0, 10))
        
        # Description
        self.desc_frame = ctk.CTkFrame(self.rule_form, fg_color="transparent")
        self.desc_frame.pack(fill="x", pady=(0, 15))
        
        self.desc_label = ctk.CTkLabel(self.desc_frame, text="📝 Mô tả:", font=ctk.CTkFont(size=12, weight="bold"))
        self.desc_label.pack(anchor="w", pady=(0, 5))
        
        self.desc_entry = ctk.CTkEntry(self.desc_frame, placeholder_text="Ghi chú về quy tắc này")
        self.desc_entry.pack(fill="x")
        
        # Active status
        self.active_frame = ctk.CTkFrame(self.rule_form, fg_color="transparent")
        self.active_frame.pack(fill="x", pady=(0, 20))
        
        self.active_var = ctk.BooleanVar(value=True)
        self.active_checkbox = ctk.CTkCheckBox(
            self.active_frame,
            text="Kích hoạt quy tắc này",
            variable=self.active_var
        )
        self.active_checkbox.pack(anchor="w")
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.rule_form, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=(0, 20))
        
        self.save_rule_btn = ctk.CTkButton(
            self.button_frame,
            text="💾 LƯU QUY TẮC",
            command=self.save_rule,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60"
        )
        self.save_rule_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.reset_rule_btn = ctk.CTkButton(
            self.button_frame,
            text="🔄 ĐẶT LẠI",
            command=self.reset_form,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#95a5a6"
        )
        self.reset_rule_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    def load_data(self):
        """Tải dữ liệu sản phẩm và quy tắc"""
        self.products = self.db_manager.get_products(self.user_id)
        self.display_products()
    
    def display_products(self):
        """Hiển thị danh sách sản phẩm"""
        # Clear existing
        for widget in self.product_list_frame.winfo_children():
            widget.destroy()
        
        if not self.products:
            no_product_label = ctk.CTkLabel(
                self.product_list_frame,
                text="Chưa có sản phẩm nào!\nHãy thêm sản phẩm mới",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_product_label.pack(pady=20)
            return
        
        for product in self.products:
            product_card = ctk.CTkFrame(self.product_list_frame, corner_radius=8, border_width=1)
            product_card.pack(fill="x", pady=(0, 5))
            
            product_name = ctk.CTkLabel(
                product_card,
                text=f"🌱 {product['name']}",
                font=ctk.CTkFont(size=13, weight="bold")
            )
            product_name.pack(side="left", padx=10, pady=8)
            
            # Get rule status
            rules = self.db_manager.get_grading_rules(self.user_id, product['id'])
            is_active = "✅" if rules and rules[0].get('is_active') else "⭕"
            
            status_label = ctk.CTkLabel(product_card, text=is_active, font=ctk.CTkFont(size=12))
            status_label.pack(side="left", padx=(0, 5))
            
            select_btn = ctk.CTkButton(
                product_card,
                text="Chọn",
                width=60,
                height=25,
                command=lambda p=product: self.select_product(p)
            )
            select_btn.pack(side="right", padx=5)
    
    def select_product(self, product):
        """Chọn sản phẩm để cấu hình quy tắc"""
        self.current_product = product
        self.product_display.configure(text=f"{product['name']} - {product.get('category', 'N/A')}")
        
        # Load existing rules for this product
        rules = self.db_manager.get_grading_rules(self.user_id, product['id'])
        if rules:
            self.current_rule = rules[0]
            self.display_rule(self.current_rule)
        else:
            self.current_rule = None
            self.reset_form()
    
    def display_rule(self, rule):
        """Hiển thị quy tắc lên form"""
        self.std_moisture_entry.delete(0, 'end')
        self.std_moisture_entry.insert(0, str(rule.get('std_moisture', 12.5)))
        
        self.moisture_ratio_entry.delete(0, 'end')
        self.moisture_ratio_entry.insert(0, str(rule.get('moisture_ratio', 1.2)))
        
        self.std_impurity_entry.delete(0, 'end')
        self.std_impurity_entry.insert(0, str(rule.get('std_impurity', 0.5)))
        
        self.impurity_ratio_entry.delete(0, 'end')
        self.impurity_ratio_entry.insert(0, str(rule.get('impurity_ratio', 1.0)))
        
        self.desc_entry.delete(0, 'end')
        self.desc_entry.insert(0, rule.get('description', ''))
        
        self.active_var.set(rule.get('is_active', True))
    
    def save_rule(self):
        """Lưu quy tắc trừ lùi"""
        if not hasattr(self, 'current_product') or not self.current_product:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn sản phẩm trước!")
            return
        
        try:
            rule_data = {
                'user_id': self.user_id,
                'product_id': self.current_product['id'],
                'std_moisture': float(self.std_moisture_entry.get() or 12.5),
                'moisture_ratio': float(self.moisture_ratio_entry.get() or 1.2),
                'std_impurity': float(self.std_impurity_entry.get() or 0.5),
                'impurity_ratio': float(self.impurity_ratio_entry.get() or 1.0),
                'description': self.desc_entry.get(),
                'is_active': self.active_var.get()
            }
            
            # Validate
            if rule_data['std_moisture'] < 0 or rule_data['std_moisture'] > 100:
                raise ValueError("Độ ẩm tiêu chuẩn phải từ 0-100%")
            
            if rule_data['moisture_ratio'] < 0:
                raise ValueError("Tỷ lệ trừ ẩm phải lớn hơn 0")
            
            if self.current_rule:
                # Update existing rule
                if self.db_manager.update_grading_rule(self.current_rule['id'], rule_data):
                    messagebox.showinfo("Thành công", f"Đã cập nhật quy tắc cho {self.current_product['name']}!")
                else:
                    messagebox.showerror("Lỗi", "Không thể cập nhật quy tắc!")
            else:
                # Create new rule
                rule = GradingRule(**rule_data, id=None)
                result = self.db_manager.create_grading_rule(rule)
                if result:
                    messagebox.showinfo("Thành công", f"Đã tạo quy tắc cho {self.current_product['name']}!")
                    self.current_rule = result
                else:
                    messagebox.showerror("Lỗi", "Không thể tạo quy tắc!")
            
            self.display_products()  # Refresh product list
            
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {str(e)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
    
    def reset_form(self):
        """Reset form về giá trị mặc định"""
        self.std_moisture_entry.delete(0, 'end')
        self.std_moisture_entry.insert(0, "12.5")
        
        self.moisture_ratio_entry.delete(0, 'end')
        self.moisture_ratio_entry.insert(0, "1.2")
        
        self.std_impurity_entry.delete(0, 'end')
        self.std_impurity_entry.insert(0, "0.5")
        
        self.impurity_ratio_entry.delete(0, 'end')
        self.impurity_ratio_entry.insert(0, "1.0")
        
        self.desc_entry.delete(0, 'end')
        self.active_var.set(True)
    
    def show_add_product_dialog(self):
        """Hiển thị dialog thêm sản phẩm mới"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Thêm sản phẩm mới")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        name_label = ctk.CTkLabel(main_frame, text="Tên sản phẩm:", font=ctk.CTkFont(size=13, weight="bold"))
        name_label.pack(anchor="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, height=40, placeholder_text="VD: Cà phê nhân, Hồ tiêu đen...")
        name_entry.pack(fill="x", pady=(0, 15))
        
        category_label = ctk.CTkLabel(main_frame, text="Danh mục:", font=ctk.CTkFont(size=13, weight="bold"))
        category_label.pack(anchor="w", pady=(0, 5))
        category_entry = ctk.CTkEntry(main_frame, height=40, placeholder_text="VD: Cà phê, Hồ tiêu, Sầu riêng...")
        category_entry.pack(fill="x", pady=(0, 15))
        
        def save_product():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên sản phẩm!")
                return
            
            from database.models import Product
            product = Product(
                id=None,
                user_id=self.user_id,
                name=name,
                category=category_entry.get().strip(),
                base_unit="kg"
            )
            
            result = self.db_manager.create_product(product)
            if result:
                messagebox.showinfo("Thành công", f"Đã thêm sản phẩm {name}!")
                dialog.destroy()
                self.load_data()  # Refresh product list
            else:
                messagebox.showerror("Lỗi", "Không thể thêm sản phẩm!")
        
        save_btn = ctk.CTkButton(main_frame, text="Lưu", command=save_product, height=40, fg_color="#27ae60")
        save_btn.pack(fill="x", pady=10)
        
        cancel_btn = ctk.CTkButton(main_frame, text="Hủy", command=dialog.destroy, height=40, fg_color="#95a5a6")
        cancel_btn.pack(fill="x")