"""
Database client — lazy-load Supabase client để tránh chặn startup.
Chỉ tạo kết nối khi thực sự cần (lần đầu gọi get_supabase()).
"""
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load .env một lần ở module level (không network)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(base_path, '.env')
load_dotenv(env_path)


# === LAZY SUPABASE CLIENT ===
# Không gọi create_client() ở module level — tránh network call khi import
_supabase_instance: Client = None


def get_supabase() -> Client:
    """
    Lấy Supabase client (lazy). Tạo kết nối ở lần gọi đầu tiên.
    """
    global _supabase_instance
    if _supabase_instance is None:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL và SUPABASE_KEY phải được cấu hình trong .env")
        _supabase_instance = create_client(url, key)
    return _supabase_instance


def reset_supabase_client():
    """Reset client (hữu ích cho testing hoặc re-auth)."""
    global _supabase_instance
    _supabase_instance = None