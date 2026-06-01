import customtkinter as ctk
from core.calculator import calculate_coffee_subtraction, calculate_pepper_subtraction

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Tiêu đề Dashboard
        self.title_label = ctk.CTkLabel(self, text="BẢNG ĐIỀU KHIỂN GASH", font=("Arial", 22, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        
        # Chọn loại nông sản
        self.product_label = ctk.CTkLabel(self, text="Loại nông sản:")
        self.product_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.product_var = ctk.StringVar(value="Cà phê")
        self.product_menu = ctk.CTkOptionMenu(self, values=["Cà phê", "Hồ tiêu"], variable=self.product_var)
        self.product_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # Tổng cân (gross weight)
        self.gross_label = ctk.CTkLabel(self, text="Tổng cân (kg):")
        self.gross_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.gross_entry = ctk.CTkEntry(self, placeholder_text="Ví dụ: 1000")
        self.gross_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # Khối lượng bao bì
        self.package_label = ctk.CTkLabel(self, text="Khối lượng bao bì (kg):")
        self.package_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.package_entry = ctk.CTkEntry(self, placeholder_text="Ví dụ: 15")
        self.package_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Độ ẩm thực tế
        self.moisture_label = ctk.CTkLabel(self, text="Độ ẩm thực tế (%):")
        self.moisture_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.moisture_entry = ctk.CTkEntry(self, placeholder_text="Ví dụ: 17.5")
        self.moisture_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        # Tạp chất thực tế
        self.impurity_label = ctk.CTkLabel(self, text="Tạp chất thực tế (%):")
        self.impurity_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.impurity_entry = ctk.CTkEntry(self, placeholder_text="Ví dụ: 2.0")
        self.impurity_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
        
        # Nút tính toán
        self.calc_button = ctk.CTkButton(self, text="TÍNH TOÁN TRỪ LÙI", command=self.calculate)
        self.calc_button.grid(row=6, column=0, columnspan=2, pady=20, padx=10, sticky="ew")
        
        # Kết quả
        self.result_box = ctk.CTkTextbox(self, width=400, height=180)
        self.result_box.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.result_box.insert("0.0", "KẾT QUẢ TÍNH TOÁN SẼ HIỂN THỊ TẠI ĐÂY\n")
        
    def calculate(self):
        try:
            product_type = self.product_var.get()
            gross_weight = float(self.gross_entry.get() or 0.0)
            package_weight = float(self.package_entry.get() or 0.0)
            measured_moisture = float(self.moisture_entry.get() or 0.0)
            measured_impurity = float(self.impurity_entry.get() or 0.0)
            
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
                
            # Hiển thị kết quả chi tiết
            self.result_box.delete("1.0", "end")
            text = f"=== CHĂN NUÔI / THU MUA: {product_type.upper()} ===\n"
            text += f"- Cân thực tế sau bao bì: {res['weight_after_package']:.2f} kg\n"
            text += f"- Trừ ẩm: -{res['moisture_subtraction']:.2f} kg\n"
            text += f"- Trừ tạp chất: -{res['impurity_subtraction']:.2f} kg\n"
            text += f"---------------------------------\n"
            text += f"🏆 CÂN TỊNH THỰC TẾ: {res['net_weight']:.2f} kg\n"
            
            if "quality_grade" in res:
                text += f"- Xếp loại chất lượng: {res['quality_grade']}\n"
                
            self.result_box.insert("1.0", text)
        except Exception as e:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("1.0", f"❌ Lỗi nhập liệu: {e}\n Vui lòng kiểm tra lại các thông số đầu vào.")
