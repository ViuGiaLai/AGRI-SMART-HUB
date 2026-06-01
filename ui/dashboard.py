import customtkinter as ctk
from core.calculator import calculate_coffee_subtraction, calculate_pepper_subtraction
from tkinter import messagebox
from datetime import datetime

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Cấu hình grid chính
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Scrollable frame cho nội dung
        self.main_canvas = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Header với gradient background
        self.header_frame = ctk.CTkFrame(
            self.main_canvas, 
            corner_radius=15,
            fg_color=("#2ecc71", "#1a5d1a")
        )
        self.header_frame.pack(fill="x", pady=(10, 20), padx=20)
        
        # Icon và tiêu đề
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="🌾",
            font=("Segoe UI Emoji", 40)
        )
        self.logo_label.pack(side="left", padx=(20, 10), pady=15)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="BẢNG ĐIỀU KHIỂN GASH", 
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(side="left", pady=15)
        
        # DateTime display
        self.datetime_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="white"
        )
        self.datetime_label.pack(side="right", padx=20, pady=15)
        
        # Main content frame
        self.content_frame = ctk.CTkFrame(self.main_canvas, corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left column - Input form
        self.left_frame = ctk.CTkFrame(self.content_frame, corner_radius=15, fg_color="transparent")
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right column - Results
        self.right_frame = ctk.CTkFrame(self.content_frame, corner_radius=15, fg_color="transparent")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # === LEFT COLUMN: INPUT FORM ===
        self.form_card = ctk.CTkFrame(self.left_frame, corner_radius=15, border_width=2, border_color=("#2ecc71", "#27ae60"))
        self.form_card.pack(fill="both", expand=True)
        
        # Form title
        self.form_title = ctk.CTkLabel(
            self.form_card,
            text="📊 THÔNG SỐ NÔNG SẢN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#2c3e50", "#ecf0f1")
        )
        self.form_title.pack(pady=(20, 15))
        
        # Product type selection with icon
        self.product_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.product_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.product_label = ctk.CTkLabel(
            self.product_frame,
            text="🌱 Loại nông sản:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.product_label.pack(anchor="w", pady=(0, 5))
        
        self.product_var = ctk.StringVar(value="Cà phê")
        self.product_menu = ctk.CTkOptionMenu(
            self.product_frame,
            values=["Cà phê", "Hồ tiêu"],
            variable=self.product_var,
            command=self.on_product_change,
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            fg_color=("#27ae60", "#2ecc71"),
            button_color=("#219a52", "#27ae60"),
            button_hover_color=("#1e8449", "#1e5a1e")
        )
        self.product_menu.pack(fill="x")
        
        # Input fields container
        self.inputs_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.inputs_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Gross weight field
        self.create_input_field(
            self.inputs_frame,
            "⚖️ Tổng cân (kg):",
            "gross_entry",
            "Nhập tổng trọng lượng",
            "📦 Ví dụ: 1000 kg"
        )
        
        # Package weight field
        self.create_input_field(
            self.inputs_frame,
            "📦 Khối lượng bao bì (kg):",
            "package_entry",
            "Nhập trọng lượng bao bì",
            "🎒 Ví dụ: 15 kg",
            row=1
        )
        
        # Moisture field
        self.create_input_field(
            self.inputs_frame,
            "💧 Độ ẩm thực tế (%):",
            "moisture_entry",
            "Nhập độ ẩm",
            "🌡️ Ví dụ: 17.5%",
            row=2
        )
        
        # Impurity field
        self.create_input_field(
            self.inputs_frame,
            "🧹 Tạp chất thực tế (%):",
            "impurity_entry",
            "Nhập tỷ lệ tạp chất",
            "🗑️ Ví dụ: 2.0%",
            row=3
        )
        
        # Quality standards info (for coffee/pepper)
        self.info_frame = ctk.CTkFrame(self.form_card, fg_color=("#f8f9fa", "#1a1a1a"), corner_radius=10)
        self.info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.info_title = ctk.CTkLabel(
            self.info_frame,
            text="📋 TIÊU CHUẨN CHẤT LƯỢNG",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#7f8c8d", "#bdc3c7")
        )
        self.info_title.pack(pady=(10, 5))
        
        self.info_content = ctk.CTkLabel(
            self.info_frame,
            text="Cà phê: ẩm 12.5% | tạp 0.5%\nHồ tiêu: ẩm 13% | tạp 1%",
            font=ctk.CTkFont(size=10),
            justify="center"
        )
        self.info_content.pack(pady=(0, 10))
        
        # Calculate button
        self.calc_button = ctk.CTkButton(
            self.form_card,
            text="🧮 TÍNH TOÁN TRỪ LÙI",
            command=self.calculate,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=12,
            fg_color=("#27ae60", "#2ecc71"),
            hover_color=("#219a52", "#27ae60")
        )
        self.calc_button.pack(padx=20, pady=(0, 20), fill="x")
        
        # === RIGHT COLUMN: RESULTS ===
        self.result_card = ctk.CTkFrame(self.right_frame, corner_radius=15, border_width=2, border_color=("#3498db", "#2980b9"))
        self.result_card.pack(fill="both", expand=True)
        
        # Result header
        self.result_header = ctk.CTkFrame(self.result_card, fg_color=("#3498db", "#2980b9"), corner_radius=15)
        self.result_header.pack(fill="x", pady=(0, 15))
        
        self.result_title = ctk.CTkLabel(
            self.result_header,
            text="📈 KẾT QUẢ TÍNH TOÁN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        self.result_title.pack(pady=12)
        
        # Result display area
        self.result_container = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.result_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Net weight display (large)
        self.net_weight_frame = ctk.CTkFrame(
            self.result_container,
            fg_color=("#27ae60", "#2ecc71"),
            corner_radius=15,
            height=120
        )
        self.net_weight_frame.pack(fill="x", pady=(0, 15))
        self.net_weight_frame.pack_propagate(False)
        
        self.net_weight_label = ctk.CTkLabel(
            self.net_weight_frame,
            text="CÂN TỊNH THỰC TẾ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        self.net_weight_label.pack(pady=(15, 5))
        
        self.net_weight_value = ctk.CTkLabel(
            self.net_weight_frame,
            text="0.00 kg",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        )
        self.net_weight_value.pack(pady=(0, 15))
        
        # Detailed results
        self.result_text = ctk.CTkTextbox(
            self.result_container,
            height=200,
            font=ctk.CTkFont(size=12),
            corner_radius=10,
            border_width=1,
            border_color=("#bdc3c7", "#7f8c8d")
        )
        self.result_text.pack(fill="both", expand=True)
        
        # Action buttons
        self.action_frame = ctk.CTkFrame(self.result_container, fg_color="transparent")
        self.action_frame.pack(fill="x", pady=(10, 0))
        
        self.export_button = ctk.CTkButton(
            self.action_frame,
            text="📎 Xuất kết quả",
            command=self.export_result,
            height=35,
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#2471a3"),
            font=ctk.CTkFont(size=11)
        )
        self.export_button.pack(side="left", padx=(0, 5), expand=True, fill="x")
        
        self.clear_button = ctk.CTkButton(
            self.action_frame,
            text="🗑️ Xóa dữ liệu",
            command=self.clear_inputs,
            height=35,
            fg_color=("#e74c3c", "#c0392b"),
            hover_color=("#c0392b", "#a93226"),
            font=ctk.CTkFont(size=11)
        )
        self.clear_button.pack(side="right", padx=(5, 0), expand=True, fill="x")
        
        # Initialize with example data
        self.set_example_data()
        
        # Update datetime
        self.update_datetime()
        
        # Bind Enter key
        self.bind_enter_keys()
    
    def create_input_field(self, parent, label_text, attr_name, placeholder, tooltip, row=0):
        """Tạo input field với label và entry"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 15) if row < 3 else (0, 0))
        
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        label.pack(anchor="w", pady=(0, 5))
        
        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            height=42,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            border_width=1,
            border_color=("#bdc3c7", "#7f8c8d")
        )
        entry.pack(fill="x")
        
        # Tooltip label
        tooltip_label = ctk.CTkLabel(
            frame,
            text=tooltip,
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray50")
        )
        tooltip_label.pack(anchor="w", pady=(3, 0))
        
        setattr(self, attr_name, entry)
    
    def on_product_change(self, choice):
        """Xử lý khi thay đổi loại sản phẩm"""
        if choice == "Cà phê":
            self.info_content.configure(text="Cà phê: ẩm 12.5% | tạp 0.5%")
        else:
            self.info_content.configure(text="Hồ tiêu: ẩm 13% | tạp 1%")
        
        # Clear results when product changes
        self.clear_results()
    
    def update_datetime(self):
        """Cập nhật thời gian thực"""
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.configure(text=f"🕐 {current_time}")
        self.after(1000, self.update_datetime)
    
    def bind_enter_keys(self):
        """Bind phím Enter để tính toán"""
        entries = [self.gross_entry, self.package_entry, self.moisture_entry, self.impurity_entry]
        for entry in entries:
            entry.bind("<Return>", lambda e: self.calculate())
    
    def set_example_data(self):
        """Đặt dữ liệu mẫu"""
        self.gross_entry.insert(0, "1000")
        self.package_entry.insert(0, "15")
        self.moisture_entry.insert(0, "17.5")
        self.impurity_entry.insert(0, "2.0")
    
    def clear_inputs(self):
        """Xóa tất cả dữ liệu nhập"""
        self.gross_entry.delete(0, 'end')
        self.package_entry.delete(0, 'end')
        self.moisture_entry.delete(0, 'end')
        self.impurity_entry.delete(0, 'end')
        self.clear_results()
    
    def clear_results(self):
        """Xóa kết quả hiển thị"""
        self.net_weight_value.configure(text="0.00 kg")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "📊 Kết quả sẽ hiển thị tại đây sau khi tính toán...")
    
    def validate_inputs(self):
        """Kiểm tra dữ liệu nhập"""
        try:
            gross = float(self.gross_entry.get() or 0)
            package = float(self.package_entry.get() or 0)
            moisture = float(self.moisture_entry.get() or 0)
            impurity = float(self.impurity_entry.get() or 0)
            
            if gross <= 0:
                messagebox.showwarning("Cảnh báo", "Tổng cân phải lớn hơn 0!")
                return False
            
            if package < 0 or package >= gross:
                messagebox.showwarning("Cảnh báo", "Khối lượng bao bì không hợp lệ!")
                return False
            
            if moisture < 0 or moisture > 100:
                messagebox.showwarning("Cảnh báo", "Độ ẩm phải từ 0-100%!")
                return False
            
            if impurity < 0 or impurity > 100:
                messagebox.showwarning("Cảnh báo", "Tạp chất phải từ 0-100%!")
                return False
            
            return True
        except ValueError:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập số hợp lệ!")
            return False
    
    def calculate(self):
        """Tính toán và hiển thị kết quả"""
        if not self.validate_inputs():
            return
        
        try:
            product_type = self.product_var.get()
            gross_weight = float(self.gross_entry.get())
            package_weight = float(self.package_entry.get())
            measured_moisture = float(self.moisture_entry.get())
            measured_impurity = float(self.impurity_entry.get())
            
            # Disable button trong khi tính
            self.calc_button.configure(state="disabled", text="⏳ ĐANG TÍNH TOÁN...")
            self.update()
            
            if product_type == "Cà phê":
                res = calculate_coffee_subtraction(
                    gross_weight=gross_weight,
                    package_weight=package_weight,
                    measured_moisture=measured_moisture,
                    measured_impurity=measured_impurity
                )
            else:
                res = calculate_pepper_subtraction(
                    gross_weight=gross_weight,
                    package_weight=package_weight,
                    measured_moisture=measured_moisture,
                    measured_impurity=measured_impurity
                )
            
            # Hiển thị kết quả
            self.display_results(res, product_type)
            
        except Exception as e:
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", f"❌ LỖI TÍNH TOÁN:\n{str(e)}\n\nVui lòng kiểm tra lại thông số đầu vào!")
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi tính toán:\n{str(e)}")
        finally:
            self.calc_button.configure(state="normal", text="🧮 TÍNH TOÁN TRỪ LÙI")
    
    def display_results(self, res, product_type):
        """Hiển thị kết quả chi tiết"""
        # Update large net weight display
        self.net_weight_value.configure(text=f"{res['net_weight']:,.2f} kg")
        
        # Clear and insert detailed results
        self.result_text.delete("1.0", "end")
        
        # Format with colors and icons (using text since CTkTextbox doesn't support rich text easily)
        text = f"{'='*50}\n"
        text += f"   🌾 KẾT QUẢ THU MUA {product_type.upper()}   \n"
        text += f"{'='*50}\n\n"
        
        text += f"📊 THÔNG SỐ ĐẦU VÀO:\n"
        text += f"   • Tổng cân (kg):        {res.get('gross_weight', 0):>10,.2f}\n"
        text += f"   • Bao bì (kg):          {res.get('package_weight', 0):>10,.2f}\n"
        text += f"   • Độ ẩm đo được (%):    {res.get('measured_moisture', 0):>10,.1f}\n"
        text += f"   • Tạp chất đo được (%): {res.get('measured_impurity', 0):>10,.1f}\n\n"
        
        text += f"🔧 QUÁ TRÌNH TRỪ LÙI:\n"
        text += f"   • Cân sau bao bì:       {res['weight_after_package']:>10,.2f} kg\n"
        text += f"   • Trừ ẩm:              -{res['moisture_subtraction']:>10,.2f} kg\n"
        text += f"   • Trừ tạp chất:        -{res['impurity_subtraction']:>10,.2f} kg\n\n"
        
        text += f"{'─'*50}\n"
        text += f"🏆 CÂN TỊNH THỰC TẾ:\n"
        text += f"   📦 {res['net_weight']:>10,.2f} kg\n"
        
        if "quality_grade" in res:
            grade_icon = "🌟" if res['quality_grade'] == "Loại 1" else "⭐"
            text += f"\n{grade_icon} XẾP LOẠI CHẤT LƯỢNG:\n"
            text += f"   • {res['quality_grade']}\n"
        
        if "note" in res:
            text += f"\n💡 GHI CHÚ:\n   • {res['note']}\n"
        
        text += f"\n{'='*50}\n"
        text += f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        
        self.result_text.insert("1.0", text)
    
    def export_result(self):
        """Xuất kết quả ra file"""
        if not self.result_text.get("1.0", "end-1c").strip() or "0.00 kg" in self.net_weight_value.cget("text") == "0.00 kg":
            messagebox.showwarning("Cảnh báo", "Chưa có kết quả để xuất! Vui lòng tính toán trước.")
            return
        
        from tkinter import filedialog
        import os
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"ket_qua_{self.product_var.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.get("1.0", "end-1c"))
                messagebox.showinfo("Thành công", f"Đã xuất kết quả ra file:\n{os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất file:\n{str(e)}")