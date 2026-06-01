# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import messagebox
import re
from database.client import get_supabase
import json
import os

class LoginScreen(ctk.CTkFrame):
    SAVED_ACCOUNTS_FILE = ".saved_accounts.json"
    
    def __init__(self, parent, login_success_callback):
        super().__init__(parent)
        self.login_success_callback = login_success_callback
        self.supabase = get_supabase()
        
        # Cấu hình grid cho frame chính
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Frame chính với hiệu ứng đổ bóng
        self.main_frame = ctk.CTkFrame(self, corner_radius=20)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Cấu hình grid cho main_frame
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(9, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Icon/Logo (có thể thay bằng image)
        self.logo_label = ctk.CTkLabel(
            self.main_frame, 
            text="🌾", 
            font=("Segoe UI Emoji", 48)
        )
        self.logo_label.grid(row=0, column=0, pady=(30, 10))
        
        # Tiêu đề
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="AGRI-SMART HUB", 
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color=("#1a5d1a", "#4a9e4a")
        )
        self.title_label.grid(row=1, column=0, pady=(0, 10))
        
        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Đăng nhập để tiếp tục",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray50")
        )
        self.subtitle_label.grid(row=2, column=0, pady=(0, 20))
        
        # === PHẦN TÀI KHOẢN ĐÃ LƯU ===
        self.saved_accounts = self.load_saved_accounts()
        if self.saved_accounts:
            self.saved_accounts_label = ctk.CTkLabel(
                self.main_frame,
                text="📝 Tài khoản đã lưu:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray70", "gray40")
            )
            self.saved_accounts_label.grid(row=3, column=0, padx=40, sticky="w", pady=(0, 8))
            
            self.saved_accounts_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self.saved_accounts_frame.grid(row=4, column=0, padx=40, sticky="ew", pady=(0, 15))
            
            for account_email in self.saved_accounts[:3]:  # Tối đa 3 tài khoản
                btn = ctk.CTkButton(
                    self.saved_accounts_frame,
                    text=f"👤 {account_email}",
                    command=lambda email=account_email: self.use_saved_account(email),
                    height=35,
                    font=ctk.CTkFont(size=11),
                    fg_color=("#e8f5e9", "#1e3a1e"),
                    text_color=("#2e8b57", "#4a9e4a"),
                    hover_color=("#d4f1d4", "#2e5a2e"),
                    corner_radius=8
                )
                btn.pack(fill="x", pady=3)
            
            # Nút xóa tất cả tài khoản lưu
            self.clear_accounts_btn = ctk.CTkButton(
                self.main_frame,
                text="🗑️ Xóa tài khoản đã lưu",
                command=self.clear_saved_accounts,
                height=25,
                font=ctk.CTkFont(size=9),
                fg_color="transparent",
                border_width=1,
                border_color=("gray70", "gray50"),
                text_color=("gray70", "gray50"),
                hover_color=("#ffebee", "#3e1a1a")
            )
            self.clear_accounts_btn.grid(row=5, column=0, padx=40, sticky="e", pady=(0, 15))
            
            input_row = 6
        else:
            input_row = 3
        
        # Frame chứa các input
        self.inputs_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.inputs_frame.grid(row=input_row, column=0, padx=40, sticky="ew")
        
        # Email input với icon
        self.email_frame = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
        self.email_frame.pack(fill="x", pady=(0, 15))
        
        self.email_icon = ctk.CTkLabel(
            self.email_frame, 
            text="📧", 
            font=("Segoe UI Emoji", 14),
            width=30
        )
        self.email_icon.pack(side="left", padx=(0, 5))
        
        self.email_entry = ctk.CTkEntry(
            self.email_frame, 
            placeholder_text="Email",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.email_entry.pack(side="left", fill="x", expand=True)
        
        # Password input với icon
        self.password_frame = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
        self.password_frame.pack(fill="x", pady=(0, 10))
        
        self.password_icon = ctk.CTkLabel(
            self.password_frame, 
            text="🔒", 
            font=("Segoe UI Emoji", 14),
            width=30
        )
        self.password_icon.pack(side="left", padx=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            self.password_frame, 
            placeholder_text="Mật khẩu", 
            show="•",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Checkbox hiển thị mật khẩu
        self.show_password_var = ctk.BooleanVar(value=False)
        self.show_password_check = ctk.CTkCheckBox(
            self.inputs_frame,
            text="Hiển thị mật khẩu",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            font=ctk.CTkFont(size=11)
        )
        self.show_password_check.pack(anchor="e", pady=(0, 15))
        
        # Nút đăng nhập
        self.login_button = ctk.CTkButton(
            self.main_frame, 
            text="ĐĂNG NHẬP", 
            command=self.login,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("#2e8b57", "#3cb371"),
            hover_color=("#1e6b47", "#2e9b67")
        )
        self.login_button.grid(row=input_row+1, column=0, padx=40, pady=(10, 15), sticky="ew")
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.main_frame, 
            text="Đang xử lý...", 
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        
        # Frame chứa các nút phụ
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.grid(row=input_row+2, column=0, pady=(0, 30))
        
        self.register_button = ctk.CTkButton(
            self.buttons_frame, 
            text="Tạo tài khoản mới", 
            fg_color="transparent",
            border_width=1,
            border_color=("#2e8b57", "#3cb371"),
            text_color=("#2e8b57", "#3cb371"),
            hover_color=("#e8f5e9", "#1e2a1e"),
            command=self.register,
            height=35,
            width=150,
            font=ctk.CTkFont(size=12)
        )
        self.register_button.pack(side="left", padx=5)
        
        self.forgot_button = ctk.CTkButton(
            self.buttons_frame, 
            text="Quên mật khẩu?", 
            fg_color="transparent",
            text_color=("gray60", "gray50"),
            hover_color=("#e8f5e9", "#1e2a1e"),
            command=self.forgot_password,
            height=35,
            width=120,
            font=ctk.CTkFont(size=12)
        )
        self.forgot_button.pack(side="left", padx=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="orange"
        )
        self.status_label.grid(row=input_row+3, column=0, pady=(0, 10))
        
        # Bind events
        self.email_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.login())
    
    def load_saved_accounts(self):
        """Tải danh sách tài khoản đã lưu"""
        try:
            if os.path.exists(self.SAVED_ACCOUNTS_FILE):
                with open(self.SAVED_ACCOUNTS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get("accounts", [])
        except Exception as e:
            print(f"Error loading saved accounts: {e}")
        return []
    
    def save_account(self, email):
        """Lưu tài khoản đã dùng"""
        try:
            accounts = self.load_saved_accounts()
            
            # Đưa email vừa dùng lên đầu
            if email in accounts:
                accounts.remove(email)
            accounts.insert(0, email)
            
            # Giữ tối đa 5 tài khoản
            accounts = accounts[:5]
            
            with open(self.SAVED_ACCOUNTS_FILE, 'w') as f:
                json.dump({"accounts": accounts}, f)
        except Exception as e:
            print(f"Error saving account: {e}")
    
    def clear_saved_accounts(self):
        """Xóa tất cả tài khoản đã lưu"""
        try:
            if os.path.exists(self.SAVED_ACCOUNTS_FILE):
                os.remove(self.SAVED_ACCOUNTS_FILE)
            messagebox.showinfo("Thành công", "Đã xóa tất cả tài khoản đã lưu")
            # Tải lại trang
            self.master.master.show_login()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi xóa: {e}")
    
    def use_saved_account(self, email):
        """Sử dụng tài khoản đã lưu"""
        self.email_entry.delete(0, 'end')
        self.email_entry.insert(0, email)
        self.password_entry.focus()

        
    def toggle_password_visibility(self):
        """Toggle mật khẩu hiển thị"""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="•")
    
    def validate_email(self, email):
        """Kiểm tra định dạng email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def show_loading(self, show):
        """Hiển thị/ẩn loading indicator"""
        # Check if widgets still exist
        if not self.winfo_exists():
            return
        
        if show:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="disabled", text="ĐANG XỰ LÝ...")
            self.update_idletasks()
        else:
            if self.login_button.winfo_exists():
                self.login_button.configure(state="normal", text="ĐĂNG NHẬP")
    
    def update_status(self, message, is_error=False):
        """Cập nhật status message"""
        self.status_label.configure(
            text=message,
            text_color="red" if is_error else "orange"
        )
        self.after(3000, lambda: self.status_label.configure(text=""))
    
    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email or not password:
            self.update_status("Vui lòng nhập đầy đủ Email và Mật khẩu", True)
            return
        
        if not self.validate_email(email):
            self.update_status("Email không hợp lệ", True)
            return
        
        if len(password) < 6:
            self.update_status("Mật khẩu phải có ít nhất 6 ký tự", True)
            return
        
        self.show_loading(True)
        
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            self.show_loading(False)
            # Lưu tài khoản khi đăng nhập thành công
            self.save_account(email)
            self.login_success_callback(response.user)
        except Exception as e:
            self.show_loading(False)
            error_msg = str(e)
            if "Invalid login credentials" in error_msg:
                self.update_status("Email hoặc mật khẩu không đúng!", True)
            elif "Email not confirmed" in error_msg:
                self.update_status("Vui lòng xác nhận email trước khi đăng nhập", True)
            else:
                self.update_status(f"Lỗi: {error_msg[:50]}", True)
            
            # Reset password field
            self.password_entry.delete(0, 'end')
    
    def register(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.update_status("Vui lòng nhập Email và Mật khẩu để đăng ký", True)
            return
        
        if not self.validate_email(email):
            self.update_status("Email không hợp lệ", True)
            return
        
        if len(password) < 6:
            self.update_status("Mật khẩu phải có ít nhất 6 ký tự", True)
            return
        
        # Hiển thị dialog xác nhận
        dialog = ctk.CTkInputDialog(
            text="Nhập lại mật khẩu để xác nhận:",
            title="Xác nhận đăng ký"
        )
        confirm_password = dialog.get_input()
        
        if confirm_password != password:
            self.update_status("Mật khẩu xác nhận không khớp!", True)
            return
        
        self.show_loading(True)
        
        try:
            self.supabase.auth.sign_up({
                "email": email, 
                "password": password
            })
            self.show_loading(False)
            
            # Hiển thị thông báo thành công với hướng dẫn
            success_msg = ctk.CTkToplevel(self)
            success_msg.title("Thành công")
            success_msg.geometry("400x200")
            success_msg.resizable(False, False)
            
            # Center the window
            success_msg.transient(self)
            success_msg.grab_set()
            
            label = ctk.CTkLabel(
                success_msg,
                text="✅ Đăng ký thành công!\n\nVui lòng kiểm tra email để\nxác nhận tài khoản trước khi đăng nhập.",
                font=ctk.CTkFont(size=13),
                justify="center"
            )
            label.pack(expand=True, padx=20, pady=20)
            
            ok_button = ctk.CTkButton(
                success_msg,
                text="OK",
                command=success_msg.destroy,
                width=100
            )
            ok_button.pack(pady=(0, 20))
            
        except Exception as e:
            self.show_loading(False)
            error_msg = str(e)
            if "User already registered" in error_msg:
                self.update_status("Email đã được đăng ký!", True)
            else:
                self.update_status(f"Lỗi: {error_msg[:50]}", True)
    
    def forgot_password(self):
        """Xử lý quên mật khẩu"""
        dialog = ctk.CTkInputDialog(
            text="Nhập email của bạn để đặt lại mật khẩu:",
            title="Quên mật khẩu"
        )
        email = dialog.get_input()
        
        if not email:
            return
        
        if not self.validate_email(email):
            self.update_status("Email không hợp lệ!", True)
            return
        
        self.show_loading(True)
        
        try:
            self.supabase.auth.reset_password_for_email(email)
            self.show_loading(False)
            
            # Hiển thị thông báo
            messagebox.showinfo(
                "Thành công", 
                "Link đặt lại mật khẩu đã được gửi đến email của bạn.\nVui lòng kiểm tra hộp thư."
            )
            self.update_status("Đã gửi email đặt lại mật khẩu", False)
            
        except Exception as e:
            self.show_loading(False)
            self.update_status(f"Không thể gửi email: {str(e)[:50]}", True)
    
    def clear_inputs(self):
        """Xóa nội dung các input"""
        self.email_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.status_label.configure(text="")