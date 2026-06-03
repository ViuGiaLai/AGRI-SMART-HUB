# ☕ Agri-Smart Hub (GASH) - Gia Lai Agri-Management Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-Supabase-green)](https://supabase.com/)
[![AI Framework](https://img.shields.io/badge/AI-Agentic--AI-orange)](https://aistudio.google.com/)
[![Hugging Face Spaces](https://img.shields.io/badge/HuggingFace-Spaces-yellow)](https://huggingface.co/spaces)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Empowering Vietnam's Highland Agriculture with Agentic AI and Digital Transformation.**

**Agri-Smart Hub (GASH)** là hệ thống quản lý và định giá nông sản thông minh dành cho các đại lý thu mua cà phê, hồ tiêu tại Gia Lai. Dự án tích hợp **Agentic AI** để tự động hóa quy trình thu mua, dự báo thị trường và tối ưu hóa lợi nhuận cho chuỗi cung ứng nông sản toàn cầu.

---

## 🚀 Key Features

- **🏠 Multi-Tenant Dashboard:** Hệ thống quản lý đa người dùng (nhiều đại lý dùng chung một nền tảng) với bảo mật dữ liệu tuyệt đối nhờ **Supabase RLS**.
- **⚖️ Automated Grading Engine:** Tự động hóa công thức "Trừ lùi" (độ ẩm, tạp chất) đặc thù của vùng Gia Lai, giúp minh bạch hóa quá trình thu mua.
- **🤖 Agentic AI Advisor:** Sử dụng **Gemini AI** đóng vai trò trợ lý ảo thông minh, tự động phân tích giá sàn thế giới (London/NY) và đưa ra lời khuyên thu mua cho đại lý.
- **📉 Price Forecasting:** Mô hình dự báo xu hướng giá dựa trên dữ liệu lịch sử và biến động kinh tế vĩ mô.
- **🌐 Web Edition (Gradio):** Phiên bản web có thể deploy lên Hugging Face Spaces — xem thị trường, chat với AI Advisor, báo cáo giá cả.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Backend/DB:** [Supabase](https://supabase.com/) (PostgreSQL + Auth + RLS)
- **Desktop UI:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Web UI:** [Gradio](https://gradio.app/) (dành cho Hugging Face Spaces)
- **AI/LLM:** Google Gemini, OpenRouter, Groq, DeepSeek
- **Data Analysis:** Pandas, Matplotlib
- **Caching:** Redis (fallback in-memory)

## 📂 Project Structure

```text
AGRI-SMART-HUB/
├── core/               # Business Logic & AI Agents
│   ├── agent/          # AgriSmartAgent (ReAct + Function Calling)
│   ├── ai_engine.py    # GeminiAgent
│   ├── llm_provider.py # Unified LLM Provider (Gemini/OpenRouter/Groq/DeepSeek)
│   ├── web_researcher.py # Web market data scraping
│   ├── market_data.py  # Market data management
│   ├── advisor_context.py # Context builder for AI Advisor
│   └── ...
├── database/           # Supabase client & DB operations
├── ui/                 # Desktop GUI (CustomTkinter) — KHÔNG dùng cho web
├── app.py              # 🆕 Gradio Web Application (HF Spaces entry point)
├── main.py             # Desktop app entry point
└── .env                # Environment Variables (Protected)
```

---

## 🌐 Deploy lên Hugging Face Spaces

### Cách 1: Deploy nhanh (click button)

[![Deploy to Hugging Face](https://img.shields.io/badge/Deploy%20to-HuggingFace-blue?logo=huggingface)](https://huggingface.co/new-space?template=gradio)

1. Click nút trên để tạo Space mới
2. Chọn **Gradio** làm SDK
3. Upload các file sau lên Space:
   - `app.py` (entry point)
   - `requirements.txt`
   - `README.md`
   - Thư mục `core/`
   - Thư mục `database/`
4. Vào tab **Settings** → **Repository secrets** thêm:
   - `SUPABASE_URL`: URL của Supabase project
   - `SUPABASE_KEY`: anon public key
   - `GEMINI_API_KEY`: (tùy chọn) Google Gemini API key
5. Space sẽ tự động build và deploy!

### Cách 2: Deploy bằng Git

```bash
# Clone project
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# Copy source code
cp -r /path/to/AGRI-SMART-HUB/* .
rm -rf ui/ main.py  # Không cần desktop UI trên web

# Push lên HF Spaces
git add .
git commit -m "Initial deploy of GASH Web"
git push
```

### Cấu hình Secrets

Vào **Settings > Repository secrets** trên HF Spaces, thêm:

| Secret | Mô tả | Bắt buộc |
|--------|-------|----------|
| `SUPABASE_URL` | Supabase project URL (`https://xxx.supabase.co`) | ✅ Có |
| `SUPABASE_KEY` | Supabase anon public key | ✅ Có |
| `GEMINI_API_KEY` | Google AI Studio API key | ❌ Tùy chọn (cho AI Advisor) |
| `OPENROUTER_API_KEY` | OpenRouter API key | ❌ Tùy chọn |
| `GROQ_API_KEY` | Groq API key | ❌ Tùy chọn |

---

## ⚙️ Installation (Desktop)

```bash
git clone https://github.com/ViuGiaLai/AGRI-SMART-HUB.git
cd AGRI-SMART-HUB
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

# Tạo file .env với nội dung:
# SUPABASE_URL="YOUR_SUPABASE_URL"
# SUPABASE_KEY="YOUR_SUPABASE_KEY"
# GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

python main.py
```

---

## 📅 Roadmap (NCKH 2026-2027)

- **Week 1-2:** Business logic research & Database Schema design
- **Week 3:** Build Auth System & Multi-tenant Login
- **Week 4-6:** Core Agri-Management Modules (In/Out/Inventory)
- **Week 7-9:** Agentic AI integration for Price Advisor
- **Week 10+:** Final Testing & Scientific Documentation
- **🆕 Phase 2:** Web Edition (Gradio) + Hugging Face Spaces deployment