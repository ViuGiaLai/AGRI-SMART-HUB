import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    response = supabase.table("products").select("*").execute()
    print("✅ Kết nối Supabase thành công!")
    print("Dữ liệu:", response.data)
except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")