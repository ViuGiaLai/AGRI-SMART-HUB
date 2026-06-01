#!/usr/bin/env python3
"""
Test script for login and registration logic without GUI.
This simulates the LoginScreen functionality using the Supabase client.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def test_sign_up(email, password):
    """Test user registration."""
    print(f"Đang đăng ký tài khoản: {email}")
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        print("✅ Đăng ký thành công!")
        print(f"   User ID: {response.user.id}")
        print(f"   Email: {response.user.email}")
        print("   Vui lòng kiểm tra email để xác nhận tài khoản.")
        return response.user
    except Exception as e:
        print(f"❌ Lỗi đăng ký: {e}")
        return None

def test_sign_in(email, password):
    """Test user login."""
    print(f"Đang đăng nhập: {email}")
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print("✅ Đăng nhập thành công!")
        print(f"   User ID: {response.user.id}")
        print(f"   Email: {response.user.email}")
        return response.user
    except Exception as e:
        print(f"❌ Lỗi đăng nhập: {e}")
        return None

def test_sign_out():
    """Test user sign out."""
    try:
        supabase.auth.sign_out()
        print("✅ Đăng xuất thành công!")
    except Exception as e:
        print(f"❌ Lỗi đăng xuất: {e}")

if __name__ == "__main__":
    print("=== KIỂM TRA ĐĂNG NHẬP / ĐĂNG KÝ VỚI SUPABASE AUTH ===\n")
    
    # Use a test email (you can change this)
    TEST_EMAIL = "test@example.com"
    TEST_PASSWORD = "SecurePass123!"
    
    # 1. Test registration
    user = test_sign_up(TEST_EMAIL, TEST_PASSWORD)
    
    if user:
        # 2. Test login
        test_sign_in(TEST_EMAIL, TEST_PASSWORD)
        
        # 3. Test sign out
        test_sign_out()
    
    print("\n=== KẾT THÚC KIỄM TRA ===")