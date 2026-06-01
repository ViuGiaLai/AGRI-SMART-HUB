import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Tải các biến môi trường
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = None

if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Lỗi khởi tạo Supabase Client: {e}")
else:
    print("Cảnh báo: SUPABASE_URL hoặc SUPABASE_KEY chưa được cấu hình trong file .env")
