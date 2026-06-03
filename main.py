# -*- coding: utf-8 -*-
import os
import customtkinter as ctk
from PIL import Image
from ui.dashboard import DashboardFrame
from ui.transaction_frame import TransactionFrame
from ui.farmer_frame import FarmerFrame
from ui.grading_rules_frame import GradingRulesFrame
from ui.my_products_frame import MyProductsFrame
from ui.login_screen import LoginScreen
from ui.ai_advisor_frame import AIAdvisorFrame
from ui.report_frame import ReportFrame
from ui.market_frame import MarketFrame
from ui.market_connection_frame import MarketConnectionFrame
from ui.settings_frame import SettingsFrame
from ui.inventory_management import InventoryManagementFrame
from core.notification_system import add_alerts_to_dashboard
from ui import theme as T
from database.client import get_supabase
from database.db_manager import DatabaseManager
from tkinter import messagebox
from datetime import datetime
import json
import os

# Digital Forest & Wealth — light mode mặc định cho độ tương phản tốt
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

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
        self.frames = {}
        self.notification_system = None
        # Database manager
        try:
            self.db = DatabaseManager(get_supabase())
        except Exception:
            self.db = None
        
        # Shell: sidebar | (topbar + content)
        self.body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True)

        self.sidebar = None
        self.right_shell = ctk.CTkFrame(self.body, fg_color="transparent", corner_radius=0)
        self.right_shell.pack(side="right", fill="both", expand=True)

        self.topbar = None
        self.main_content = ctk.CTkFrame(
            self.right_shell, fg_color=T.BG_MAIN, corner_radius=0
        )
        
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
    
    def create_topbar(self):
        """Topbar: tên đại lý, thời gian thực, đăng xuất."""
        if self.topbar and self.topbar.winfo_exists():
            self.topbar.destroy()

        self.topbar = ctk.CTkFrame(
            self.right_shell,
            height=T.TOPBAR_HEIGHT,
            corner_radius=0,
            fg_color=T.BG_TOPBAR,
        )
        self.topbar.pack(fill="x", side="top")
        self.topbar.pack_propagate(False)

        left = ctk.CTkFrame(self.topbar, fg_color="transparent")
        left.pack(side="left", padx=24, pady=12)
        ctk.CTkLabel(left, text="🌾", font=("Segoe UI Emoji", 22)).pack(side="left")
        self.agent_title = ctk.CTkLabel(
            left,
            text="Gia Lai Agri-Smart Hub",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=T.TEXT_ON_DARK,
        )
        self.agent_title.pack(side="left", padx=(8, 0))

        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.pack(side="right", padx=20, pady=10)

        self.datetime_label = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=12), text_color="#bdc3c7",
        )
        self.datetime_label.pack(side="left", padx=(0, 20))

        self.theme_switch = ctk.CTkSwitch(
            right, text="Dark", command=self.toggle_theme,
            width=44, progress_color=T.PRIMARY, button_color=T.PRIMARY,
        )
        self.theme_switch.pack(side="left", padx=(0, 12))

        # User avatar
        try:
            avatar_path = os.path.join(os.path.dirname(__file__), "assets", "GASH-VIU.png")
            avatar_img = ctk.CTkImage(Image.open(avatar_path), size=(28, 28))
            self.user_avatar = ctk.CTkLabel(right, image=avatar_img, text="")
            self.user_avatar.pack(side="left", padx=(0, 8))
        except:
            self.user_avatar = ctk.CTkLabel(right, text="👤", font=ctk.CTkFont(size=18))
            self.user_avatar.pack(side="left", padx=(0, 8))

        self.user_label = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=T.TEXT_ON_DARK,
        )
        self.user_label.pack(side="left", padx=(0, 12))

        self.logout_btn = ctk.CTkButton(
            right, text="Đăng xuất", command=self.logout,
            width=100, height=36, corner_radius=T.CORNER_RADIUS_SM,
            fg_color=T.DANGER, hover_color="#c0392b",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.update_datetime()
    
    def create_sidebar(self):
        """Sidebar xanh đen — điều hướng chính."""
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.destroy()

        self.sidebar = ctk.CTkFrame(
            self.body, width=T.SIDEBAR_WIDTH, corner_radius=0, fg_color=T.BG_SIDEBAR,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(24, 20))
        
        # App logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "GASH-VIU.png")
            logo_img = ctk.CTkImage(Image.open(logo_path), size=(40, 40))
            ctk.CTkLabel(brand, image=logo_img, text="").pack(anchor="w")
        except Exception as e:
            print(f"Không load được logo: {e}")
            ctk.CTkLabel(brand, text="🌱", font=ctk.CTkFont(size=28)).pack(anchor="w")
        
        ctk.CTkLabel(brand, text="AGRI-SMART HUB", font=ctk.CTkFont(size=14, weight="bold"), text_color=T.PRIMARY).pack(anchor="w", pady=(5, 0))

        if self.current_user:
            email = self.current_user.get("email", "")
            name = email.split("@")[0].title()
            pf = ctk.CTkFrame(self.sidebar, fg_color=T.SECONDARY_LIGHT, corner_radius=T.CORNER_RADIUS_SM)
            pf.pack(fill="x", padx=12, pady=(0, 16))
            ctk.CTkLabel(pf, text="👤", font=("Segoe UI Emoji", 28)).pack(pady=(10, 0))
            ctk.CTkLabel(pf, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_ON_DARK).pack()
            ctk.CTkLabel(pf, text="Đại lý thu mua", font=ctk.CTkFont(size=10), text_color="#95a5a6").pack(pady=(0, 10))

        self.menu_items = [
            {"icon": "📊", "text": "Dashboard", "command": self.show_dashboard, "frame": "dashboard"},
            {"icon": "📋", "text": "Giao dịch", "command": self.show_transaction_management, "frame": "transactions"},
            {"icon": "👨‍🌾", "text": "Nông dân", "command": self.show_farmer_management, "frame": "farmers"},
            {"icon": "📦", "text": "Quản lý kho", "command": self.show_inventory_management, "frame": "inventory_mgmt"},
            {"icon": "🏷️", "text": "Sản phẩm", "command": self.show_my_products, "frame": "products"},
            {"icon": "🤖", "text": "AI Advisor", "command": self.show_ai_advisor, "frame": "ai_advisor"},
            {"icon": "📄", "text": "Báo cáo", "command": self.show_reports, "frame": "reports"},
            {"icon": "🌐", "text": "Kết nối", "command": self.show_market_connection, "frame": "connection"},
            {"icon": "⚙️", "text": "Cài đặt", "command": self.show_settings, "frame": "settings"},
        ]

        self.menu_buttons = {}
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=8)
        for item in self.menu_items:
            btn = ctk.CTkButton(
                nav,
                text=f"  {item['icon']}   {item['text']}",
                command=item["command"],
                anchor="w",
                height=44,
                corner_radius=T.CORNER_RADIUS_SM,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color="#ecf0f1",
                hover_color=T.SECONDARY_LIGHT,
            )
            btn.pack(fill="x", pady=3, padx=4)
            self.menu_buttons[item["frame"]] = btn

        ctk.CTkButton(
            self.sidebar, text="  ⚙️  Quy tắc trừ lùi",
            command=self.show_grading_rules, anchor="w", height=40,
            corner_radius=T.CORNER_RADIUS_SM, fg_color="transparent",
            text_color="#7f8c8d", hover_color=T.SECONDARY_LIGHT,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=12, pady=(0, 16))

        self.active_menu = None
    
    def highlight_menu(self, frame_name):
        """Highlight menu item đang active"""
        for name, btn in self.menu_buttons.items():
            if name == frame_name:
                btn.configure(fg_color=T.PRIMARY, text_color=T.TEXT_ON_DARK)
                self.active_menu = name
            else:
                btn.configure(fg_color="transparent", text_color="#ecf0f1")
    
    
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
        else:
            ctk.set_appearance_mode("light")
        
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
                if hasattr(self, "theme_switch") and self.theme_switch.winfo_exists():
                    if theme == "dark":
                        self.theme_switch.select()
                    else:
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
        
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.pack_forget()
        if self.topbar and self.topbar.winfo_exists():
            self.topbar.pack_forget()
        self.main_content.pack_forget()

        self.right_shell.pack(fill="both", expand=True)
        self.login_frame = LoginScreen(self.right_shell, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)
    
    def on_login_success(self, user):
        """Xử lý khi đăng nhập thành công"""
        self.current_user = {"email": user.email, "id": user.id}
        print(f"✅ Đăng nhập thành công: {user.email}")
        
        self.login_frame.destroy()

        self.create_sidebar()
        self.create_topbar()
        self.main_content.pack(fill="both", expand=True)

        agent = user.email.split("@")[0].title()
        self.user_label.configure(text=f"Đại lý: {agent}")
        self.agent_title.configure(text=f"Đại lý {agent}")

        # TỐI ƯU: Fetch dữ liệu thị trường CHỈ khi dashboard cần (lazy)
        # Thay vì crawl web ngay khi login — để background thread làm sau
        if self.db:
            self._lazy_fetch_market_data()

        self.show_dashboard()
        
        # Lưu session
        self.save_session()
        
        # Hiển thị thông báo chào mừng
        self.show_welcome_message(user.email)
    
    def _lazy_fetch_market_data(self):
        """
        TỐI ƯU: Fetch dữ liệu thị trường trong background thread.
        Không block UI — dashboard sẽ hiển thị dữ liệu cũ nếu có,
        và tự cập nhật khi fetch xong.
        """
        import threading

        def _do_fetch():
            try:
                from core.market_data import MarketDataManager
                market_mgr = MarketDataManager(self.db)
                fetch_result = market_mgr.ensure_real_data_available()
                if fetch_result.get("success"):
                    total = fetch_result.get("total_saved", 0)
                    if total > 0:
                        print(f"✅ Background fetch: đã lưu {total} bản ghi giá thị trường")
                else:
                    errors = fetch_result.get("errors", [])
                    if errors:
                        print(f"⚠️ Background fetch: {'; '.join(errors)}")
            except Exception as e:
                print(f"⚠️ Background fetch error: {e}")

        # Đợi 2s để dashboard load xong, rồi fetch background
        self.after(2000, lambda: threading.Thread(target=_do_fetch, daemon=True).start())

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
    
    def _stop_notifications(self):
        """Dừng giám sát cảnh báo khi rời Dashboard."""
        if self.notification_system:
            self.notification_system.stop_monitoring()
            self.notification_system = None

    def show_dashboard(self):
        """Hiển thị Dashboard kèm cảnh báo thông minh."""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.frames["dashboard"] = DashboardFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user["id"],
        )
        self.frames["dashboard"].pack(fill="both", expand=True)

        if self.db:
            self.notification_system = add_alerts_to_dashboard(
                self.frames["dashboard"],
                self.db,
                self.current_user["id"],
                root_window=self,
            )

        self.highlight_menu("dashboard")

    def show_inventory_management(self):
        """Hiển thị quản lý tồn kho."""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.frames["inventory_mgmt"] = InventoryManagementFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user["id"],
        )
        self.frames["inventory_mgmt"].pack(fill="both", expand=True)
        self.highlight_menu("inventory_mgmt")
    
    def show_farmer_management(self):
        """Hiển thị quản lý nông dân"""
        self._stop_notifications()
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
        self._stop_notifications()
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
        self._stop_notifications()
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
        
        self.frames["market"] = MarketFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["market"].pack(fill="both", expand=True)
        
        self.highlight_menu("market")

    def show_market_connection(self):
        """Hiển thị Kết nối Thị trường Nông sản"""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.frames["connection"] = MarketConnectionFrame(
            self.main_content,
        )
        self.frames["connection"].pack(fill="both", expand=True)
        self.highlight_menu("connection")
    
    def show_transaction_management(self):
        """Hiển thị quản lý giao dịch"""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["transactions"] = TransactionFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user['id']
        )
        self.frames["transactions"].pack(fill="both", expand=True)
        self.highlight_menu("transactions")
    

    
    def show_ai_advisor(self):
        """Hiển thị AI Advisor"""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["ai_advisor"] = AIAdvisorFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user["id"],
        )
        self.frames["ai_advisor"].pack(fill="both", expand=True)
        self.highlight_menu("ai_advisor")
    

    
    def show_reports(self):
        """Hiển thị báo cáo"""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.frames["reports"] = ReportFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user["id"],
        )
        self.frames["reports"].pack(fill="both", expand=True)
        self.highlight_menu("reports")
    
    def show_settings(self):
        """Hiển thị cài đặt hệ thống (5 tab)"""
        self._stop_notifications()
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.frames["settings"] = SettingsFrame(
            self.main_content,
            db_manager=self.db,
            user_id=self.current_user["id"] if self.current_user else None,
            main_app=self,
        )
        self.frames["settings"].pack(fill="both", expand=True)
        self.highlight_menu("settings")
    
    def logout(self):
        """Đăng xuất"""
        # Xác nhận đăng xuất
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            self._stop_notifications()
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
        """Dừng notification system khi đóng app."""
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát chương trình?"):
            self._stop_notifications()
            self.save_preference("window_size", self.geometry())
            self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.load_preferences()
    app.mainloop()