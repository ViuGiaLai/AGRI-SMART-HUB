Copy
# ☕ Agri-Smart Hub (GASH) - Gia Lai Agri-Management Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-Supabase-green)](https://supabase.com/)
[![AI Framework](https://img.shields.io/badge/AI-Agentic--AI-orange)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Empowering Vietnam's Highland Agriculture with Agentic AI and Digital Transformation.**

**Agri-Smart Hub (GASH)** là hệ thống quản lý và định giá nông sản thông minh dành cho các đại lý thu mua cà phê, hồ tiêu tại Gia Lai. Dự án tích hợp **Agentic AI** để tự động hóa quy trình thu mua, dự báo thị trường và tối ưu hóa lợi nhuận cho chuỗi cung ứng nông sản toàn cầu.

---

## 🚀 Key Features

- **🏠 Multi-Tenant Dashboard:** Hệ thống quản lý đa người dùng (nhiều đại lý dùng chung một nền tảng) với bảo mật dữ liệu tuyệt đối nhờ **Supabase RLS**.
- **⚖️ Automated Grading Engine:** Tự động hóa công thức "Trừ lùi" (độ ẩm, tạp chất) đặc thù của vùng Gia Lai, giúp minh bạch hóa quá trình thu mua.
- **🤖 Agentic AI Advisor:** Sử dụng **Gemini AI** đóng vai trò trợ lý ảo thông minh, tự động phân tích giá sàn thế giới (London/NY) và đưa ra lời khuyên thu mua cho đại lý.
- **📉 Price Forecasting:** Mô hình dự báo xu hướng giá dựa trên dữ liệu lịch sử và biến động kinh tế vĩ mô.
- **💻 Desktop-First Experience:** Ứng dụng Desktop chạy ổn định, giao diện hiện đại (Modern UI) tích hợp khả năng hoạt động Offline.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Backend/DB:** [Supabase](https://supabase.com/) (PostgreSQL + Auth + RLS)
- **UI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **AI/LLM:** Google Gemini 1.5 Flash (via LangChain/Google AI Studio)
- **Data Analysis:** Pandas, Matplotlib, Scikit-learn

## 📂 Project Structure

```text
GASH_Project/
├── core/               # Business Logic & AI Agents
├── database/           # Supabase client & API services
├── ui/                 # GUI Frames & Screens (CustomTkinter)
├── models/             # ML Models for forecasting
├── main.py             # Entry point of the application
└── .env                # Environment Variables (Protected)
⚙️ Installation
Clone the repository:

Copy
git clone <https://github.com/ViuGiaLai/AGRI-SMART-HUB.git>
cd AGRI-SMART-HUB
Setup Virtual Environment:

Copy
python -m venv venv
.\venv\Scripts\activate  # Windows
Install Dependencies:

Copy
pip install -r requirements.txt
Configuration: Tạo file .env tại thư mục gốc và cấu hình các thông tin sau:

Copy
SUPABASE_URL="YOUR_SUPABASE_URL"
SUPABASE_KEY="YOUR_SUPABASE_KEY"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
Run the App:

Copy
python main.py
📅 Roadmap (NCKH 2026-2027)
 Week 1-2: Business logic research & Database Schema design.
 Week 3: Build Auth System & Multi-tenant Login.
 Week 4-6: Core Agri-Management Modules (In/Out/Inventory).
 Week 7-9: Agentic AI integration for Price Advisor.
 Week 10+: Final Testing & Scientific Documentation.