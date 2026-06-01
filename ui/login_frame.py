import customtkinter as ctk
from tkinter import messagebox
import re

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        
        # Cấu hình grid cho frame chính
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Frame trung tâm với hiệu ứng đổ bóng và bo góc
        self.center_frame = ctk.CTkFrame(
            self, 
            corner_radius=20,
            fg_color=("gray95", "gray12"),
            border_width=2,
            border_color=("#2ecc71", "#27ae60")
        )
        self.center_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        
        # Cấu hình grid cho center_frame
        self.center_frame.grid_rowconfigure(0, weight=0)
        self.center_frame.grid_rowconfigure(8, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)
        
        # Header với icon
        self.header_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(30, 10), sticky="ew")
        
        # Icon logo
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="🏦",
            font=("Segoe UI Emoji", 48)
        )
        self.logo_label.pack(pady=(0, 5))
        
        # Tiêu đề chính
        self.title_label = ctk.CTkLabel(
            self.center_frame, 
            text="HỆ THỐNG GASH", 
            font=ctk.CTkFont(family="Arial", size=26, weight="bold"),
            text_color=("#2c3e50", "#ecf0f1")
        )
        self.title_label.grid(row=1, column=0, pady=(0, 5))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.center_frame,
            text="Đăng nhập để truy cập hệ thống",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        )
        self.subtitle_label.grid(row=2, column=0, pady=(0, 30))
        
        # Frame chứa các input
        self.input_container = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.input_container.grid(row=3, column=0, padx=40, sticky="ew")
        
        # === Email Field ===
        self.email_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.email_frame.pack(fill="x", pady=(0, 20))
        
        # Email label
        self.email_label = ctk.CTkLabel(
            self.email_frame,
            text="📧 Email",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.email_label.pack(anchor="w", pady=(0, 5))
        
        # Email entry với icon
        self.email_entry_frame = ctk.CTkFrame(self.email_frame, fg_color="transparent")
        self.email_entry_frame.pack(fill="x")
        
        self.email_icon = ctk.CTkLabel(
            self.email_entry_frame,
            text="✉️",
            font=("Segoe UI Emoji", 14),
            width=30
        )
        self.email_icon.pack(side="left", padx=(0, 5))
        
        self.email_entry = ctk.CTkEntry(
            self.email_entry_frame,
            placeholder_text="nhập email của bạn",
            height=42,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            border_width=1,
            border_color=("#bdc3c7", "#7f8c8d")
        )
        self.email_entry.pack(side="left", fill="x", expand=True)
        
        # === Password Field ===
        self.password_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.password_frame.pack(fill="x", pady=(0, 10))
        
        # Password label
        self.password_label = ctk.CTkLabel(
            self.password_frame,
            text="🔒 Mật khẩu",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.password_label.pack(anchor="w", pady=(0, 5))
        
        # Password entry frame
        self.password_entry_frame = ctk.CTkFrame(self.password_frame, fg_color="transparent")
        self.password_entry_frame.pack(fill="x")
        
        self.password_icon = ctk.CTkLabel(
            self.password_entry_frame,
            text="🔐",
            font=("Segoe UI Emoji", 14),
            width=30
        )
        self.password_icon.pack(side="left", padx=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            self.password_entry_frame,
            placeholder_text="nhập mật khẩu",
            show="•",
            height=42,
            font=ctk.CTkFont(size=13),
            corner_radius=10,
            border_width=1,
            border_color=("#bdc3c7", "#7f8c8d")
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Toggle password visibility
        self.show_password_var = ctk.BooleanVar(value=False)
        self.toggle_button = ctk.CTkButton(
            self.password_entry_frame,
            text="👁️",
            width=35,
            height=35,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#e0e0e0", "#2a2a2a"),
            command=self.toggle_password_visibility
        )
        self.toggle_button.pack(side="right", padx=(5, 0))
        
        # === Options Frame ===
        self.options_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.options_frame.pack(fill="x", pady=(15, 20))
        
        # Remember me checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Ghi nhớ đăng nhập",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            checkbox_width=18,
            checkbox_height=18
        )
        self.remember_checkbox.pack(side="left")
        
        # Forgot password button
        self.forgot_button = ctk.CTkButton(
            self.options_frame,
            text="Quên mật khẩu?",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#3498db", "#5dade2"),
            hover_color=("#ebf5fb", "#1a2a3a"),
            command=self.forgot_password,
            width=100
        )
        self.forgot_button.pack(side="right")
        
        # === Login Button ===
        self.login_button = ctk.CTkButton(
            self.center_frame,
            text="ĐĂNG NHẬP",
            command=self.login,
            height=48,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=12,
            fg_color=("#27ae60", "#2ecc71"),
            hover_color=("#219a52", "#27ae60"),
            border_width=0
        )
        self.login_button.grid(row=4, column=0, padx=40, pady=(0, 15), sticky="ew")
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.center_frame,
            text="⏳ Đang xử lý...",
            font=ctk.CTkFont(size=11),
            text_color=("#f39c12", "#f1c40f")
        )
        
        # === Register Section ===
        self.register_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.register_frame.grid(row=5, column=0, pady=(0, 30))
        
        self.register_label = ctk.CTkLabel(
            self.register_frame,
            text="Chưa có tài khoản?",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        self.register_label.pack(side="left", padx=(0, 5))
        
        self.register_button = ctk.CTkButton(
            self.register_frame,
            text="Đăng ký ngay",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            text_color=("#27ae60", "#2ecc71"),
            hover_color=("#e8f5e9", "#1a2a1a"),
            command=self.register,
            width=100
        )
        self.register_button.pack(side="left")
        
        # Error label
        self.error_label = ctk.CTkLabel(
            self.center_frame,
            text="",
            text_color="#e74c3c",
            font=ctk.CTkFont(size=11),
            wraplength=300
        )
        self.error_label.grid(row=6, column=0, pady=(0, 10))
        
        # Bind Enter key
        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Load saved credentials if any
        self.load_saved_credentials()
        
    def toggle_password_visibility(self):
        """Toggle hiển thị mật khẩu"""
        if self.show_password_var.get():
            self.password_entry.configure(show="•")
            self.show_password_var.set(False)
            self.toggle_button.configure(text="👁️")
        else:
            self.password_entry.configure(show="")
            self.show_password_var.set(True)
            self.toggle_button.configure(text="🙈")
    
    def validate_email(self, email):
        """Kiểm tra định dạng email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def show_error(self, message):
        """Hiển thị thông báo lỗi"""
        self.error_label.configure(text=f"⚠️ {message}")
        self.after(3000, lambda: self.error_label.configure(text=""))
    
    def show_loading(self, show):
        """Hiển thị trạng thái loading"""
        if show:
            self.login_button.configure(state="disabled", text="⏳ ĐANG XỬ LÝ...")
            self.loading_label.grid(row=4, column=0, pady=(0, 0))
        else:
            self.login_button.configure(state="normal", text="ĐĂNG NHẬP")
            self.loading_label.grid_forget()
    
    def login(self):
        """Xử lý đăng nhập"""
        # Clear previous error
        self.error_label.configure(text="")
        
        # Get credentials
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email or not password:
            self.show_error("Vui lòng nhập đầy đủ email và mật khẩu")
            return
        
        if not self.validate_email(email):
            self.show_error("Email không đúng định dạng")
            return
        
        if len(password) < 6:
            self.show_error("Mật khẩu phải có ít nhất 6 ký tự")
            return
        
        # Show loading
        self.show_loading(True)
        
        # Simulate API call (replace with actual Supabase authentication)
        self.after(1000, lambda: self.perform_login(email, password))
    
    def perform_login(self, email, password):
        """Thực hiện đăng nhập (simulate - replace with actual API)"""
        # TODO: Thay thế bằng API Supabase thực tế
        # from database.client import get_supabase
        # supabase = get_supabase()
        # try:
        #     response = supabase.auth.sign_in_with_password({
        #         "email": email, 
        #         "password": password
        #     })
        #     if self.on_login_success:
        #         self.on_login_success()
        # except Exception as e:
        #     self.show_error("Email hoặc mật khẩu không đúng")
        
        # Simulated login for demo
        if email == "admin@gmail.com" and password == "123456":
            # Save credentials if remember me is checked
            if self.remember_var.get():
                self.save_credentials(email, password)
            
            self.show_loading(False)
            if self.on_login_success:
                self.on_login_success()
        else:
            self.show_loading(False)
            self.show_error("Email hoặc mật khẩu không đúng")
            self.password_entry.delete(0, 'end')
    
    def save_credentials(self, email, password):
        """Lưu thông tin đăng nhập (có thể dùng file hoặc registry)"""
        # Simple implementation using a file
        try:
            import json
            import os
            
            cred_file = "saved_credentials.json"
            data = {"email": email, "password": password if self.show_password_var.get() else ""}
            with open(cred_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def load_saved_credentials(self):
        """Tải thông tin đăng nhập đã lưu"""
        try:
            import json
            import os
            
            cred_file = "saved_credentials.json"
            if os.path.exists(cred_file):
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                    if data.get("email"):
                        self.email_entry.insert(0, data["email"])
                        if data.get("password"):
                            self.password_entry.insert(0, data["password"])
                            self.remember_var.set(True)
        except:
            pass
    
    def register(self):
        """Mở cửa sổ đăng ký"""
        register_window = ctk.CTkToplevel(self)
        register_window.title("Đăng ký tài khoản")
        register_window.geometry("450x550")
        register_window.resizable(False, False)
        
        # Center the window
        register_window.transient(self.master)
        register_window.grab_set()
        
        # Register form
        register_frame = RegisterFrame(register_window, on_register_success=self.on_register_success)
        register_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    def on_register_success(self, email, password):
        """Xử lý khi đăng ký thành công"""
        self.email_entry.delete(0, 'end')
        self.email_entry.insert(0, email)
        self.password_entry.delete(0, 'end')
        self.password_entry.insert(0, password)
        self.show_error("")  # Clear error
        messagebox.showinfo("Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
    
    def forgot_password(self):
        """Xử lý quên mật khẩu"""
        dialog = ctk.CTkInputDialog(
            text="Nhập email của bạn để đặt lại mật khẩu:",
            title="Quên mật khẩu"
        )
        email = dialog.get_input()
        
        if email:
            if not self.validate_email(email):
                self.show_error("Email không hợp lệ!")
                return
            
            # TODO: Gọi API reset password
            # supabase.auth.reset_password_for_email(email)
            
            messagebox.showinfo(
                "Thành công", 
                "Link đặt lại mật khẩu đã được gửi đến email của bạn.\nVui lòng kiểm tra hộp thư."
            )


class RegisterFrame(ctk.CTkFrame):
    """Frame đăng ký tài khoản"""
    def __init__(self, master, on_register_success=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_register_success = on_register_success
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Đăng ký tài khoản mới", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(10, 20))
        
        # Full name
        self.name_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Họ và tên",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Email
        self.email_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Email",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.email_entry.pack(fill="x", pady=(0, 15))
        
        # Password
        self.password_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Mật khẩu (ít nhất 6 ký tự)",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.password_entry.pack(fill="x", pady=(0, 15))
        
        # Confirm password
        self.confirm_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Xác nhận mật khẩu",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.confirm_entry.pack(fill="x", pady=(0, 20))
        
        # Register button
        self.register_button = ctk.CTkButton(
            self,
            text="ĐĂNG KÝ",
            command=self.register,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27ae60",
            hover_color="#219a52"
        )
        self.register_button.pack(fill="x", pady=(0, 10))
        
        # Error label
        self.error_label = ctk.CTkLabel(self, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.error_label.pack()
        
        # Bind Enter key
        self.name_entry.bind("<Return>", lambda e: self.email_entry.focus())
        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.confirm_entry.focus())
        self.confirm_entry.bind("<Return>", lambda e: self.register())
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def register(self):
        """Xử lý đăng ký"""
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        # Validation
        if not name or not email or not password:
            self.error_label.configure(text="Vui lòng điền đầy đủ thông tin")
            return
        
        if not self.validate_email(email):
            self.error_label.configure(text="Email không hợp lệ")
            return
        
        if len(password) < 6:
            self.error_label.configure(text="Mật khẩu phải có ít nhất 6 ký tự")
            return
        
        if password != confirm:
            self.error_label.configure(text="Mật khẩu xác nhận không khớp")
            return
        
        # TODO: Gọi API Supabase để đăng ký
        # supabase.auth.sign_up({"email": email, "password": password})
        
        # Success
        messagebox.showinfo("Thành công", "Đăng ký thành công! Vui lòng kiểm tra email để xác nhận.")
        
        if self.on_register_success:
            self.on_register_success(email, password)
        
        self.master.destroy()