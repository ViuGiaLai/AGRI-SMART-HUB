import customtkinter as ctk

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        
        # Tiêu đề
        self.title_label = ctk.CTkLabel(self, text="HỆ THỐNG GASH", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=20)
        
        # Nhập Email
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email đăng nhập", width=250)
        self.email_entry.pack(pady=10)
        
        # Nhập Mật khẩu
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mật khẩu", show="*", width=250)
        self.password_entry.pack(pady=10)
        
        # Nút đăng nhập
        self.login_button = ctk.CTkButton(self, text="Đăng nhập", command=self.login)
        self.login_button.pack(pady=15)
        
        # Label hiển thị lỗi
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()
        
    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if email and password:
            # Ở đây sau này sẽ gọi API Supabase auth.sign_in_with_password
            if self.on_login_success:
                self.on_login_success()
        else:
            self.error_label.configure(text="Vui lòng nhập đầy đủ thông tin")
