import os
from supabase import create_client, Client
from dotenv import load_dotenv
import customtkinter as ctk

# 1. Tải cấu hình
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Thử nghiệm giao diện
def check_connection():
    try:
        # Thử lấy danh sách sản phẩm (Bảng products)
        response = supabase.table("products").select("*").execute()
        label.configure(text="✅ Kết nối Supabase thành công!", text_color="green")
        print("Dữ liệu:", response.data)
    except Exception as e:
        label.configure(text=f"❌ Lỗi kết nối: {e}", text_color="red")

# Cấu hình giao diện CustomTkinter
app = ctk.CTk()
app.title("GASH - Kiểm tra kết nối")
app.geometry("400x200")

label = ctk.CTkLabel(app, text="Đang kiểm tra kết nối...", font=("Arial", 14))
label.pack(pady=40)

btn = ctk.CTkButton(app, text="Thử kết nối", command=check_connection)
btn.pack()

app.mainloop()
