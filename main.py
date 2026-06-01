# -*- coding: utf-8 -*-
import customtkinter as ctk
from ui.dashboard import DashboardFrame
from ui.transaction_frame import TransactionFrame
from ui.farmer_frame import FarmerFrame
from ui.grading_rules_frame import GradingRulesFrame
from ui.my_products_frame import MyProductsFrame
from ui.login_screen import LoginScreen
from database.client import get_supabase
from database.db_manager import DatabaseManager
from tkinter import messagebox
from datetime import datetime
import json
import os

# Cấu hình theme cho CustomTkinter
ctk.set_appearance_mode("system")  # Modes: "system", "light", "dark"
ctk.set_default_color_theme("green")  # Themes: "blue", "dark-blue", "green"

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Cấu hình cửa sổ chính
        self.title("GASH - Gia Lai Agri-Smart Hub")
        # Use a much larger default window
        self.geometry("1600x900")
        self.minsize(1200, 800)
        
        # Center window on screen
        self.center_window()
        
        # Biến quản lý trạng thái
        self.current_user = None
        self.current_frame = None
        self.frames = {}  # Lưu trữ các frame đã tạo
        # Database manager
        try:
            self.db = DatabaseManager(get_supabase())
        except Exception:
            self.db = None
        
        # Tạo header bar
        self.create_header()
        
        # Tạo sidebar (sẽ hiển thị sau khi login)
        self.sidebar = None
        
        # Tạo main content area
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="right", fill="both", expand=True, padx=(0, 0))
        
        # Khởi tạo menu trạng thái chưa đăng nhập
        self.show_login()
        
        # Bind sự kiện đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto save session
        self.load_session()
        
    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.update_idletasks()
        # If width/height are not yet calculated, fall back to the requested geometry
        width = self.winfo_width() or int(self.winfo_reqwidth() or 1366)
        height = self.winfo_height() or int(self.winfo_reqheight() or 800)
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        try:
            self.geometry(f'{width}x{height}+{x}+{y}')
        except Exception:
            # fallback: just center using requested geometry
            self.geometry(f'1600x900+{x}+{y}')
    
    def create_header(self):
        """Tạo header bar với thông tin người dùng"""
        self.header = ctk.CTkFrame(
            self, 
            height=60, 
            corner_radius=0,
            fg_color=("#2ecc71", "#1a5d1a")
        )
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)
        
        # Logo và tiêu đề
        self.header_left = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_left.pack(side="left", padx=20, pady=10)
        
        self.logo_label = ctk.CTkLabel(
            self.header_left,
            text="🌾",
            font=("Segoe UI Emoji", 28)
        )
        self.logo_label.pack(side="left", padx=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_left,
            text="GASH - Gia Lai Agri-Smart Hub",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(side="left")
        
        # Header right (user info)
        self.header_right = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_right.pack(side="right", padx=20, pady=10)
        
        # User info (sẽ cập nhật sau khi login)
        self.user_label = ctk.CTkLabel(
            self.header_right,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        self.user_label.pack(side="left", padx=(0, 15))
        
        # Theme switcher
        self.theme_switch = ctk.CTkSwitch(
            self.header_right,
            text="🌙 Dark Mode",
            command=self.toggle_theme,
            progress_color="#27ae60",
            button_color="#27ae60",
            button_hover_color="#219a52"
        )
        self.theme_switch.pack(side="left", padx=(0, 15))
        
        # Fullscreen button
        self.fullscreen_btn = ctk.CTkButton(
            self.header_right,
            text="⛶ Toàn màn hình",
            command=self.toggle_fullscreen,
            width=100,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            text_color="white",
            hover_color=("#27ae60", "#2ecc71"),
            font=ctk.CTkFont(size=10)
        )
        self.fullscreen_btn.pack(side="left", padx=(0, 15))
        
        # Logout button (ẩn ban đầu)
        self.logout_btn = ctk.CTkButton(
            self.header_right,
            text="Đăng xuất",
            command=self.logout,
            width=80,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color="white",
            text_color="white",
            hover_color=("#e74c3c", "#c0392b")
        )
        
        # DateTime label
        self.datetime_label = ctk.CTkLabel(
            self.header_right,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="white"
        )
        self.datetime_label.pack(side="left", padx=(15, 0))
        
        # Cập nhật thời gian thực
        self.update_datetime()
    
    def create_sidebar(self):
        """Tạo sidebar menu sau khi đăng nhập"""
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.destroy()
        
        self.sidebar = ctk.CTkFrame(
            self, 
            width=250, 
            corner_radius=0,
            fg_color=("#f8f9fa", "#2b2b2b")
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 0))
        self.sidebar.pack_propagate(False)
        
        # User profile section
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(fill="x", padx=20, pady=(30, 20))
        
        self.avatar_label = ctk.CTkLabel(
            self.profile_frame,
            text="👤",
            font=("Segoe UI Emoji", 48)
        )
        self.avatar_label.pack()
        
        if self.current_user:
            email = self.current_user.get('email', 'user@example.com')
            name = email.split('@')[0]
            self.user_name_label = ctk.CTkLabel(
                self.profile_frame,
                text=name.title(),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            self.user_name_label.pack(pady=(5, 0))
            
            self.user_email_label = ctk.CTkLabel(
                self.profile_frame,
                text=email,
                font=ctk.CTkFont(size=11),
                text_color=("gray60", "gray50")
            )
            self.user_email_label.pack()
        
        # Menu items
        self.menu_items = [
            {"icon": "📊", "text": "Dashboard", "command": self.show_dashboard, "frame": "dashboard"},
            {"icon": "👨‍🌾", "text": "Quản lý nông dân", "command": self.show_farmer_management, "frame": "farmers"},
            {"icon": "📦", "text": "Sản phẩm", "command": self.show_my_products, "frame": "products"},
            {"icon": "⚙️", "text": "Quy tắc trừ lùi", "command": self.show_grading_rules, "frame": "rules"},
            {"icon": "📋", "text": "Giao dịch", "command": self.show_transaction_management, "frame": "transactions"},
            {"icon": "📈", "text": "Phân tích thị trường", "command": self.show_market_analysis, "frame": "market"},
            {"icon": "📄", "text": "Báo cáo", "command": self.show_reports, "frame": "reports"},
            {"icon": "⚙️", "text": "Cài đặt", "command": self.show_settings, "frame": "settings"}
        ]
        
        self.menu_buttons = {}
        for item in self.menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{item['icon']}  {item['text']}",
                command=item['command'],
                anchor="w",
                height=45,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("#333333", "#ffffff"),
                hover_color=("#e8f5e9", "#2e2e2e")
            )
            btn.pack(fill="x", padx=15, pady=2)
            self.menu_buttons[item['frame']] = btn
        
        # Highlight active menu
        self.active_menu = None
    
    def highlight_menu(self, frame_name):
        """Highlight menu item đang active"""
        for name, btn in self.menu_buttons.items():
            if name == frame_name:
                btn.configure(fg_color=("#27ae60", "#2ecc71"), text_color="white")
                self.active_menu = name
            else:
                btn.configure(fg_color="transparent", text_color=("#333333", "#ffffff"))
    
    def toggle_fullscreen(self):
        """Chuyển đổi chế độ toàn màn hình"""
        self.is_fullscreen = getattr(self, 'is_fullscreen', False)
        if not self.is_fullscreen:
            self.state('zoomed')
            self.fullscreen_btn.configure(text="⛶ Thoát toàn màn hình")
            self.is_fullscreen = True
        else:
            self.state('normal')
            self.geometry("1600x900")
            self.fullscreen_btn.configure(text="⛶ Toàn màn hình")
            self.is_fullscreen = False

    
    def update_datetime(self):
        """Cập nhật thời gian thực"""
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.configure(text=f"🕐 {current_time}")
        self.after(1000, self.update_datetime)
    
    def toggle_theme(self):
        """Chuyển đổi theme sáng/tối"""
        current = ctk.get_appearance_mode()
        if current == "Light":
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="☀️ Light Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="🌙 Dark Mode")
        
        # Lưu preference
        self.save_preference("theme", ctk.get_appearance_mode())
    
    def save_preference(self, key, value):
        """Lưu preference của người dùng"""
        pref_file = "user_preferences.json"
        try:
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    prefs = json.load(f)
            else:
                prefs = {}
            
            prefs[key] = value
            
            with open(pref_file, 'w') as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving preference: {e}")
    
    def load_preferences(self):
        """Tải preference của người dùng"""
        pref_file = "user_preferences.json"
        try:
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    prefs = json.load(f)
                
                # Apply theme preference
                theme = prefs.get("theme", "light")
                ctk.set_appearance_mode(theme)
                if theme == "dark":
                    self.theme_switch.configure(text="☀️ Light Mode")
                    self.theme_switch.select()
                else:
                    self.theme_switch.configure(text="🌙 Dark Mode")
                    self.theme_switch.deselect()
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def save_session(self):
        """Lưu session đăng nhập"""
        if self.current_user:
            session_data = {
                "user_email": self.current_user.get('email'),
                "timestamp": datetime.now().isoformat()
            }
            try:
                with open(".session", 'w') as f:
                    json.dump(session_data, f)
            except:
                pass
    
    def load_session(self):
        """Tải session đăng nhập"""
        try:
            if os.path.exists(".session"):
                with open(".session", 'r') as f:
                    session_data = json.load(f)
                # Có thể tự động đăng nhập lại nếu cần
                # self.auto_login(session_data.get('user_email'))
        except:
            pass
    
    def clear_session(self):
        """Xóa session đăng nhập"""
        try:
            if os.path.exists(".session"):
                os.remove(".session")
        except:
            pass
    
    def show_login(self):
        """Hiển thị màn hình đăng nhập"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Hide sidebar và logout button
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.pack_forget()
        
        self.logout_btn.pack_forget()
        self.user_label.configure(text="")
        
        # Show login frame
        self.login_frame = LoginScreen(self.main_content, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)
    
    def on_login_success(self, user):
        """Xử lý khi đăng nhập thành công"""
        self.current_user = {"email": user.email, "id": user.id}
        print(f"✅ Đăng nhập thành công: {user.email}")
        
        # Cập nhật header
        self.user_label.configure(text=f"👋 Xin chào, {user.email.split('@')[0]}")
        self.logout_btn.pack(side="left", padx=(0, 15))
        
        # Tạo sidebar
        self.create_sidebar()
        
        # Xóa login frame và hiển thị dashboard
        self.login_frame.destroy()
        self.show_dashboard()
        
        # Lưu session
        self.save_session()
        
        # Hiển thị thông báo chào mừng
        self.show_welcome_message(user.email)
    
    def show_welcome_message(self, email):
        """Hiển thị thông báo chào mừng"""
        name = email.split('@')[0]
        welcome_msg = ctk.CTkToplevel(self)
        welcome_msg.title("Chào mừng")
        welcome_msg.geometry("400x200")
        welcome_msg.transient(self)
        welcome_msg.grab_set()
        
        # Center the window
        welcome_msg.update_idletasks()
        x = (welcome_msg.winfo_screenwidth() // 2) - (400 // 2)
        y = (welcome_msg.winfo_screenheight() // 2) - (200 // 2)
        welcome_msg.geometry(f'+{x}+{y}')
        
        content = ctk.CTkFrame(welcome_msg, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)
        
        icon = ctk.CTkLabel(content, text="🎉", font=("Segoe UI Emoji", 48))
        icon.pack(pady=(0, 10))
        
        label = ctk.CTkLabel(
            content,
            text=f"Chào mừng {name.title()} đến với\nGASH - Hệ thống quản lý nông sản thông minh",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        label.pack(pady=(0, 20))
        
        ok_btn = ctk.CTkButton(
            content,
            text="Bắt đầu",
            command=welcome_msg.destroy,
            width=150
        )
        ok_btn.pack()
        
        # Auto close after 3 seconds
        welcome_msg.after(3000, welcome_msg.destroy)
    
    def show_dashboard(self):
        """Hiển thị Dashboard"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Always recreate dashboard frame to avoid widget destruction issues
        self.frames["dashboard"] = DashboardFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["dashboard"].pack(fill="both", expand=True)
        self.highlight_menu("dashboard")
    
    def show_farmer_management(self):
        """Hiển thị quản lý nông dân"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["farmers"] = FarmerFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["farmers"].pack(fill="both", expand=True)
        self.highlight_menu("farmers")
    
    def show_my_products(self):
        """Hiển thị danh sách sản phẩm"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["products"] = MyProductsFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["products"].pack(fill="both", expand=True)
        self.highlight_menu("products")
    
    def show_grading_rules(self):
        """Hiển thị cấu hình quy tắc trừ lùi"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["rules"] = GradingRulesFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["rules"].pack(fill="both", expand=True)
        self.highlight_menu("rules")
    
    def show_market_analysis(self):
        """Hiển thị phân tích thị trường"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # TODO: Create MarketAnalysisFrame
        label = ctk.CTkLabel(
            self.main_content,
            text="📈 Phân tích thị trường\n(Đang phát triển)",
            font=ctk.CTkFont(size=24, weight="bold"),
            justify="center"
        )
        label.pack(expand=True)
        
        self.highlight_menu("market")
    
    def show_transaction_management(self):
        """Hiển thị quản lý giao dịch"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["transactions"] = TransactionFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["transactions"].pack(fill="both", expand=True)
        self.highlight_menu("transactions")
    

    
    def show_reports(self):
        """Hiển thị báo cáo"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # TODO: Create ReportsFrame
        label = ctk.CTkLabel(
            self.main_content,
            text="📄 Báo cáo & Thống kê\n(Đang phát triển)",
            font=ctk.CTkFont(size=24, weight="bold"),
            justify="center"
        )
        label.pack(expand=True)
        
        self.highlight_menu("reports")
    
    def show_settings(self):
        """Hiển thị cài đặt"""
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # TODO: Create SettingsFrame
        label = ctk.CTkLabel(
            self.main_content,
            text="⚙️ Cài đặt hệ thống\n(Đang phát triển)",
            font=ctk.CTkFont(size=24, weight="bold"),
            justify="center"
        )
        label.pack(expand=True)
        
        self.highlight_menu("settings")
    
    def logout(self):
        """Đăng xuất"""
        # Xác nhận đăng xuất
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            # Clear session
            self.clear_session()
            
            # Reset current user
            self.current_user = None
            
            # Clear frames cache
            self.frames.clear()
            
            # Show login screen
            self.show_login()
            
            # Thông báo
            messagebox.showinfo("Thành công", "Đã đăng xuất thành công!")
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát chương trình?"):
            self.save_preference("window_size", self.geometry())
            self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.load_preferences()
    app.mainloop()