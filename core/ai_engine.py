import os
import google.generativeai as genai
from dotenv import load_dotenv

# Tải cấu hình
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Lỗi cấu hình Gemini API: {e}")
else:
    print("Cảnh báo: GEMINI_API_KEY chưa được cấu hình")

def ask_gemini(prompt: str) -> str:
    """
    Hàm gửi câu hỏi đến Gemini và nhận phản hồi (Dùng cho AI Agent phân tích giá, thị trường)
    """
    if not api_key:
        return "Lỗi: Chưa cấu hình GEMINI_API_KEY trong file .env"
        
    try:
        # Sử dụng model gemini-1.5-flash hoặc gemini-pro
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi kết nối Gemini API: {e}"
