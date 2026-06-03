# -*- coding: utf-8 -*-
"""
AGRI-SMART HUB — Full Gradio Web Application
==============================================
Login (Supabase Auth) + 10 tabs from main.py.
Dùng cho Hugging Face Spaces.
"""

import base64
import os
import sys
import io
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import gradio as gr
import pandas as pd

# ──────────────────────────────────────────────
# HELPER — Load logo as base64 (cross-platform)
# ──────────────────────────────────────────────

def _get_logo_html() -> str:
    """Return HTML img tag with base64-encoded logo, fallback to emoji."""
    paths = [
        r"D:\all_my_project\AGRI-SMART-HUB\assets\GASH-VIU.png",
        "assets/GASH-VIU.png",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "GASH-VIU.png"),
    ]
    for p in paths:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/png;base64,{b64}" alt="GASH Logo" style="width:120px;height:auto;">'
        except (FileNotFoundError, IOError):
            continue
    return "🌾"


# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gash-web")

# ──────────────────────────────────────────────
# MEGA CSS — Agriculture Theme 🍃
# ──────────────────────────────────────────────
# CSS to forcefully hide login elements when they have hide class
LOGIN_CLEANUP_CSS = """
.login-page.hide, .login-page.hidden,
.login-page[class*="hide"],
.login-page[class*="hidden"],
.login-page[style*="display: none"],
.login-page[style*="display:none"] {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  min-width: 0 !important;
  min-height: 0 !important;
  max-width: 0 !important;
  max-height: 0 !important;
  flex-grow: 0 !important;
  flex-shrink: 1 !important;
  overflow: hidden !important;
  position: absolute !important;
  opacity: 0 !important;
  pointer-events: none !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
}
"""

MEGA_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans:wght@300;400;500;600;700&display=swap');

/* ─── BASE ─── */
:root {
  --green-900: #1a3c2a;
  --green-800: #1f4d33;
  --green-700: #2d6a43;
  --green-600: #3d8b5a;
  --green-500: #4caf50;
  --green-400: #66bb6a;
  --green-300: #81c784;
  --green-200: #a5d6a7;
  --green-100: #c8e6c9;
  --green-50: #e8f5e9;

  --gold-500: #f9a825;
  --gold-400: #fbc02d;
  --gold-300: #fdd835;
  --gold-100: #fff8e1;

  --earth-600: #6d4c41;
  --earth-400: #8d6e63;
  --earth-200: #d7ccc8;
  --earth-50: #efebe9;

  --red-500: #e53935;
  --red-100: #ffebee;
  --blue-500: #1e88e5;
  --blue-100: #e3f2fd;

  --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%);
  --card-bg: rgba(255, 255, 255, 0.9);
  --card-border: rgba(0, 0, 0, 0.08);
  --card-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  --text-primary: #1a1a2e;
  --text-secondary: rgba(26, 26, 46, 0.7);
  --text-muted: rgba(26, 26, 46, 0.4);
  --glass-bg: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(0, 0, 0, 0.06);
}

/* ─── GRADIO OVERRIDES ─── */
body, .gradio-container {
  font-family: 'Inter', 'Noto Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  background: var(--bg-gradient) !important;
  color: var(--text-primary) !important;
  max-width: 100% !important;
  margin: 0 !important;
  min-height: 100vh;
}

.gradio-container {
  padding: 0 !important;
  background: transparent !important;
}

/* Kill extra white backgrounds from Gradio theme containers */
.gr-box, .gr-form, .gr-panel, .gr-group, 
.gr-block, .wrap, .contain, .panel {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--green-700); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--green-500); }

/* ─── TYPOGRAPHY ─── */
h1, h2, h3, h4, h5, h6 { font-family: 'Inter', sans-serif !important; color: #1a1a2e !important; }
h1 { font-size: 1.8em !important; font-weight: 800 !important; letter-spacing: -0.02em !important; }
h2 { font-size: 1.4em !important; font-weight: 700 !important; border: none !important; padding-bottom: 8px !important; margin-top: 0 !important; }
h3 { font-size: 1.1em !important; font-weight: 600 !important; }
p, li, .prose { color: var(--text-secondary) !important; line-height: 1.6 !important; }

/* ─── CONTAINERS ─── */
.app-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 8px 16px;
}

/* ─── TOP BAR ─── */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 12px;
  margin-bottom: 8px;
}
.top-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.top-bar-logo {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--green-500), var(--green-700));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1em;
}
.top-bar-title {
  font-weight: 700; font-size: 1em; color: #1a1a2e;
}
.top-bar-subtitle {
  font-size: 0.75em; color: var(--text-muted);
}
.top-bar-right {
  display: flex; align-items: center; gap: 8px;
}

/* ─── CARDS ─── */
.card {
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--card-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

/* ─── KPI CARDS ─── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.kpi-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  border-radius: 16px 16px 0 0;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.kpi-card .kpi-icon { font-size: 1.8em; margin-bottom: 8px; }
.kpi-card .kpi-label { font-size: 0.8em; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.kpi-card .kpi-value { font-size: 1.6em; font-weight: 700; color: var(--text-primary); }

.kpi-green::before { background: linear-gradient(90deg, #4caf50, #66bb6a); }
.kpi-gold::before { background: linear-gradient(90deg, #f9a825, #fbc02d); }
.kpi-blue::before { background: linear-gradient(90deg, #1e88e5, #42a5f5); }
.kpi-purple::before { background: linear-gradient(90deg, #7e57c2, #ab47bc); }
.kpi-teal::before { background: linear-gradient(90deg, #00897b, #26a69a); }

/* ─── BUTTONS ─── */
.gr-button, button.gradio-button {
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 0.9em !important;
  padding: 10px 20px !important;
  cursor: pointer !important;
  transition: all 0.25s ease !important;
  text-transform: none !important;
  letter-spacing: 0.01em !important;
  font-family: 'Inter', sans-serif !important;
}
button.gradio-button-primary {
  background: linear-gradient(135deg, #2d6a43, #4caf50) !important;
  color: white !important;
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3) !important;
}
button.gradio-button-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(76, 175, 80, 0.4) !important;
}
button.gradio-button-secondary {
  background: rgba(255,255,255,0.6) !important;
  color: var(--text-primary) !important;
  border: 1px solid rgba(0,0,0,0.08) !important;
}
button.gradio-button-secondary:hover {
  background: rgba(255,255,255,0.9) !important;
}
button.gradio-button-stop {
  background: rgba(229, 57, 53, 0.15) !important;
  color: #ef5350 !important;
  border: 1px solid rgba(229, 57, 53, 0.25) !important;
}
button.gradio-button-stop:hover {
  background: rgba(229, 57, 53, 0.25) !important;
}

/* ─── INPUTS ─── */
input, textarea, select, .gr-input, .gr-text-input, .gr-number-input {
  background: #fff !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  border-radius: 10px !important;
  color: #1a1a2e !important;
  padding: 10px 14px !important;
  font-size: 0.9em !important;
  transition: all 0.2s ease !important;
  font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus, select:focus, .gr-input:focus {
  border-color: var(--green-500) !important;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.15) !important;
  outline: none !important;
}
input::placeholder, textarea::placeholder {
  color: rgba(26,26,46,0.4) !important;
}

/* ─── DROPDOWN ─── */
.gr-dropdown, select {
  background: #fff !important;
  border: 1px solid rgba(0,0,0,0.12) !important;
  border-radius: 10px !important;
  color: #1a1a2e !important;
}
.gr-dropdown:focus {
  border-color: var(--green-500) !important;
}

/* ─── RADIO ─── */
.gr-radio {
  background: transparent !important;
  border: none !important;
}
.gr-radio label {
  color: var(--text-secondary) !important;
}
.gr-radio input:checked + label {
  color: #1a3c2a !important;
}

/* ─── TABS ─── */
.tabs {
  border: none !important;
  background: transparent !important;
}
.gr-tabs {
  border: none !important;
  background: transparent !important;
}
.gr-tabs > .tab-nav {
  background: rgba(255,255,255,0.6) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 12px !important;
  padding: 3px !important;
  border: 1px solid rgba(0,0,0,0.06) !important;
  gap: 2px !important;
  overflow-x: auto !important;
  flex-wrap: nowrap !important;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.gr-tabs > .tab-nav button {
  background: transparent !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 8px 14px !important;
  color: rgba(26,26,46,0.5) !important;
  font-weight: 500 !important;
  font-size: 0.82em !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
}
.gr-tabs > .tab-nav button:hover {
  color: #1a1a2e !important;
  background: rgba(0,0,0,0.04) !important;
}
.gr-tabs > .tab-nav button.selected {
  background: #fff !important;
  color: #1a1a2e !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}
.gr-tabs > .tab-nav button:focus { outline: none !important; }

/* ─── ACCORDION ─── */
.gr-accordion {
  background: rgba(255,255,255,0.7) !important;
  border: 1px solid rgba(0,0,0,0.06) !important;
  border-radius: 12px !important;
  margin-bottom: 12px !important;
  overflow: hidden !important;
}
.gr-accordion > .label-wrap {
  background: rgba(255,255,255,0.7) !important;
  padding: 14px 16px !important;
  font-weight: 600 !important;
  color: #1a1a2e !important;
  border: none !important;
}

/* ─── DATAFRAME / TABLE ─── */
.gr-dataframe {
  border: 1px solid rgba(0,0,0,0.06) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  background: #fff !important;
}
.gr-dataframe table {
  border-collapse: collapse !important;
  width: 100% !important;
}
.gr-dataframe th {
  background: #e8f5e9 !important;
  color: #1a3c2a !important;
  font-weight: 600 !important;
  font-size: 0.85em !important;
  padding: 10px 12px !important;
  text-align: left !important;
  border-bottom: 1px solid rgba(0,0,0,0.04) !important;
}
.gr-dataframe td {
  background: transparent !important;
  color: var(--text-primary) !important;
  padding: 10px 12px !important;
  border-bottom: 1px solid rgba(0,0,0,0.03) !important;
  font-size: 0.88em !important;
}
.gr-dataframe tr:hover td {
  background: rgba(0,0,0,0.02) !important;
}

/* ─── CHATBOT ─── */
.gr-chatbot {
  background: rgba(255,255,255,0.8) !important;
  border: 1px solid rgba(0,0,0,0.06) !important;
  border-radius: 16px !important;
}
.gr-chatbot .message-wrap {
  padding: 8px !important;
}
.gr-chatbot .message {
  border-radius: 16px !important;
  padding: 12px 16px !important;
  max-width: 85% !important;
  font-size: 0.9em !important;
  line-height: 1.55 !important;
}
.gr-chatbot .message.user {
  background: linear-gradient(135deg, var(--green-700), var(--green-600)) !important;
  color: white !important;
  margin-left: auto !important;
  border-bottom-right-radius: 4px !important;
}
.gr-chatbot .message.bot {
  background: #fff !important;
  color: var(--text-primary) !important;
  border: 1px solid rgba(0,0,0,0.06) !important;
  border-bottom-left-radius: 4px !important;
}

/* ─── FILE COMPONENT ─── */
.gr-file, .gr-upload {
  background: rgba(255,255,255,0.6) !important;
  border: 1px dashed rgba(0,0,0,0.12) !important;
  border-radius: 12px !important;
  color: var(--text-secondary) !important;
}

/* ─── MARKDOWN CONTENT ─── */
.markdown-content h2 {
  color: #1a1a2e !important;
  font-size: 1.3em !important;
  margin-top: 16px !important;
}
.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
.markdown-content th {
  background: #e8f5e9;
  color: #1a3c2a;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.markdown-content td {
  padding: 8px 12px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(0,0,0,0.03);
}

/* ─── LOGIN PAGE ─── */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-gradient);
  position: relative;
  overflow: hidden;
}
@keyframes float-glow {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.05); }
}

.login-card {
  background: #fff;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 24px;
  padding: 32px 36px;
  width: 400px;
  max-width: 92vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.6s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-logo {
  width: 120px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-logo img {
  width: 120px;
  height: auto;
}
.login-title {
  text-align: center;
  font-size: 1.6em;
  font-weight: 800;
  color: #1a1a2e;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}
.login-subtitle {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9em;
  margin-bottom: 24px;
}

/* ─── DEMO CREDENTIALS ─── */
.demo-info {
  background: #fff8e1;
  border: 1px solid #f9a825;
  border-radius: 12px;
  padding: 14px 16px;
  margin: 12px 0 18px;
  font-size: 1em;
  color: #e65100;
  text-align: center;
  line-height: 1.6;
}
.demo-info .demo-label {
  font-size: 0.92em;
  font-weight: 600;
  color: #e65100;
  display: block;
  margin-bottom: 10px;
}
.demo-info .demo-creds {
  font-size: 1.3em;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: 0.01em;
  display: block;
  background: rgba(255, 193, 7, 0.15);
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 8px;
}

/* ─── NARROW INPUTS ─── */
.login-card input, .login-card textarea, .login-card select {
  padding: 8px 12px !important;
  font-size: 0.88em !important;
  background: rgba(255,255,255,0.9) !important;
  color: #1a3c2a !important;
  border: 1px solid rgba(0,0,0,0.10) !important;
}
.login-card input::placeholder {
  color: #999 !important;
}
.login-card .gr-input {
  padding: 8px 12px !important;
  font-size: 0.88em !important;
  background: rgba(255,255,255,0.9) !important;
  color: #1a3c2a !important;
  border: 1px solid rgba(0,0,0,0.10) !important;
}
.login-card label, .login-card .gr-label, .login-card .label-text {
  color: #1a3c2a !important;
  font-weight: 600 !important;
  font-size: 0.85em !important;
}
.login-card .gr-button {
  padding: 8px 16px !important;
  font-size: 0.88em !important;
}
.login-footer {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.8em;
}

.login-error {
  background: #ffebee;
  border: 1px solid #e57373;
  color: #c62828;
  border-radius: 10px;
  padding: 10px 14px;
  margin: 8px 0;
  font-size: 0.88em;
}
.login-success {
  background: #e8f5e9;
  border: 1px solid #81c784;
  color: #2e7d32;
  border-radius: 10px;
  padding: 10px 14px;
  margin: 8px 0;
  font-size: 0.88em;
}

/* ─── STATUS BADGE ─── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.82em;
  font-weight: 500;
}
.status-badge.online {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}
.status-badge.offline {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

/* ─── ANIMATIONS ─── */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.loading-dot {
  display: inline-block;
  width: 6px; height: 6px;
  background: var(--green-400);
  border-radius: 50%;
  margin: 0 3px;
  animation: pulse-dot 1.4s ease-in-out infinite;
}
.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

/* ─── SECTION DIVIDERS ─── */
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.section-title .line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(0,0,0,0.10), transparent);
}

/* ─── FOOTER ─── */
.app-footer {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 0.82em;
  border-top: 1px solid rgba(0,0,0,0.06);
  margin-top: 32px;
}

/* ─── RESPONSIVE ─── */
@media (max-width: 768px) {
  .app-wrapper { padding: 4px 8px; }
  .login-card { padding: 28px 20px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .top-bar { flex-direction: column; gap: 4px; text-align: center; padding: 4px 8px; }
  .top-bar-left { gap: 4px; }
  .top-bar-title { font-size: 0.9em; }
  .gr-tabs > .tab-nav { overflow-x: auto; }
  .gr-tabs > .tab-nav button { font-size: 0.72em !important; padding: 6px 10px !important; }
}
@media (max-width: 480px) {
  .kpi-grid { grid-template-columns: 1fr; }
}
"""


# ──────────────────────────────────────────────
# APP STATE
# ──────────────────────────────────────────────
class AppState:
    supabase_url: str = ""
    supabase_key: str = ""
    gemini_key: str = ""
    openrouter_key: str = ""
    groq_key: str = ""
    db_manager: Any = None
    current_user_id: str = ""
    current_user_email: str = ""
    initialized: bool = False

    @classmethod
    def get_db(cls):
        if cls.db_manager is not None:
            return cls.db_manager
        if not cls.supabase_url or not cls.supabase_key:
            return None
        try:
            from database.client import get_supabase, reset_supabase_client
            os.environ["SUPABASE_URL"] = cls.supabase_url
            os.environ["SUPABASE_KEY"] = cls.supabase_key
            if cls.gemini_key: os.environ["GEMINI_API_KEY"] = cls.gemini_key
            if cls.openrouter_key: os.environ["OPENROUTER_API_KEY"] = cls.openrouter_key
            if cls.groq_key: os.environ["GROQ_API_KEY"] = cls.groq_key

            reset_supabase_client()
            client = get_supabase()
            from database.db_manager import DatabaseManager as DB
            cls.db_manager = DB(client)
            cls.initialized = True
            return cls.db_manager
        except Exception as e:
            logger.error(f"DB init error: {e}")
            return None

    @classmethod
    def reset(cls):
        cls.db_manager = None
        cls.initialized = False

    @classmethod
    def ensure_user(cls):
        if not cls.current_user_id:
            return None
        return cls.current_user_id


# ──────────────────────────────────────────────
# AUTH FUNCTIONS
# ──────────────────────────────────────────────

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def do_login(email: str, password: str) -> dict:
    """Đăng nhập qua Supabase Auth. Trả về dict có success + message + user info."""
    result = {"success": False, "message": "", "email": "", "user_id": ""}

    if not email or not password:
        result["message"] = "Vui lòng nhập email và mật khẩu"
        return result

    if not validate_email(email):
        result["message"] = "Email không hợp lệ"
        return result

    if len(password) < 6:
        result["message"] = "Mật khẩu phải có ít nhất 6 ký tự"
        return result

    db = AppState.get_db()
    if not db:
        result["message"] = "⚠️ Database chưa kết nối! Kiểm tra SUPABASE_URL và SUPABASE_KEY trong Settings."
        return result

    try:
        from database.client import get_supabase
        client = get_supabase()
        response = client.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password
        })
        user = response.user
        result["success"] = True
        result["message"] = f"✅ Đăng nhập thành công! Chào mừng {email}"
        result["email"] = email
        result["user_id"] = user.id
        AppState.current_user_id = user.id
        AppState.current_user_email = email
        return result
    except Exception as e:
        err = str(e)
        if "Invalid login credentials" in err:
            result["message"] = "❌ Email hoặc mật khẩu không đúng!"
        elif "Email not confirmed" in err:
            result["message"] = "❌ Vui lòng xác nhận email trước khi đăng nhập"
        else:
            result["message"] = f"❌ Lỗi: {err[:80]}"
        return result


def do_register(email: str, password: str) -> dict:
    """Đăng ký tài khoản mới qua Supabase Auth."""
    result = {"success": False, "message": ""}

    if not email or not password:
        result["message"] = "Vui lòng nhập email và mật khẩu"
        return result

    if not validate_email(email):
        result["message"] = "Email không hợp lệ"
        return result

    if len(password) < 6:
        result["message"] = "Mật khẩu phải có ít nhất 6 ký tự"
        return result

    db = AppState.get_db()
    if not db:
        result["message"] = "⚠️ Database chưa kết nối!"
        return result

    try:
        from database.client import get_supabase
        client = get_supabase()
        client.auth.sign_up({
            "email": email.strip(),
            "password": password
        })
        result["success"] = True
        result["message"] = (
            "✅ **Đăng ký thành công!**\n\n"
            "Vui lòng kiểm tra email để xác nhận tài khoản trước khi đăng nhập."
        )
        return result
    except Exception as e:
        err = str(e)
        if "User already registered" in err:
            result["message"] = "❌ Email này đã được đăng ký!"
        else:
            result["message"] = f"❌ Lỗi: {err[:80]}"
        return result


def do_forgot_password(email: str) -> dict:
    """Gửi email đặt lại mật khẩu."""
    result = {"success": False, "message": ""}

    if not email:
        result["message"] = "Vui lòng nhập email"
        return result

    if not validate_email(email):
        result["message"] = "Email không hợp lệ"
        return result

    db = AppState.get_db()
    if not db:
        result["message"] = "⚠️ Database chưa kết nối!"
        return result

    try:
        from database.client import get_supabase
        client = get_supabase()
        client.auth.reset_password_for_email(email.strip())
        result["success"] = True
        result["message"] = "📧 Link đặt lại mật khẩu đã được gửi đến email của bạn!"
        return result
    except Exception as e:
        result["message"] = f"❌ Lỗi: {str(e)[:80]}"
        return result


# ──────────────────────────────────────────────
# FORMAT HELPERS
# ──────────────────────────────────────────────

def format_vnd(amount: float) -> str:
    if not amount: return "0 ₫"
    return f"{amount:,.0f} ₫"


def format_kg(kg: float) -> str:
    if not kg: return "0 kg"
    return f"{kg:,.1f} kg"


# ──────────────────────────────────────────────
# TAB 1: DASHBOARD
# ──────────────────────────────────────────────

def render_dashboard() -> Tuple[str, str, str, str, str, str, str]:
    """Return dashboard HTML and KPI values."""
    db = AppState.get_db()
    user_id = AppState.ensure_user()

    if not db or not user_id:
        info = "⚠️ Vui lòng đăng nhập và cấu hình database trước."
        return info, "—", "—", "—", "—", "—", "—"

    try:
        stats = db.get_dashboard_stats(user_id) or {}
        total_stock = stats.get("total_stock", 0) or 0
        total_trans = stats.get("total_transactions", 0) or 0
        total_value = stats.get("total_value", 0) or 0
        total_farmers = stats.get("total_farmers", 0) or 0

        coffee_price = 0
        cprices = db.get_market_prices("Cà phê", days=1)
        if cprices:
            coffee_price = cprices[0].get("price_local", 0) or 0

        web_prices_html = ""
        try:
            from core.web_researcher import WebMarketResearcher
            researcher = WebMarketResearcher()
            coffee = researcher.research_coffee()
            pepper = researcher.research_pepper()
            if coffee and coffee.best_price():
                web_prices_html += f"☕ **Cà phê:** {format_vnd(coffee.best_price())}/kg ({coffee.sources[0].source_name if coffee.sources else 'N/A'})\n\n"
            if pepper and pepper.best_price():
                web_prices_html += f"🌶️ **Hồ tiêu:** {format_vnd(pepper.best_price())}/kg ({pepper.sources[0].source_name if pepper.sources else 'N/A'})\n\n"
        except Exception as e:
            logger.warning(f"Web research error: {e}")

        products = ["Cà phê", "Hồ tiêu", "Sầu riêng", "Lúa gạo", "Cao su", "Điều nhân", "Cacao", "Mắc ca"]
        table_rows = []
        for product in products:
            rows = db.get_market_prices(product, days=7)
            if rows:
                prices = [r.get("price_local", 0) or 0 for r in rows if (r.get("price_local") or 0) > 0]
                if prices:
                    latest = prices[0]
                    oldest = prices[-1] if len(prices) > 1 else latest
                    change = ((latest - oldest) / oldest * 100) if oldest else 0
                    trend = "📈" if change > 0.5 else ("📉" if change < -0.5 else "➡️")
                    table_rows.append(f"| {product} | **{format_vnd(latest)}/kg** | {trend} {change:+.1f}% |")
                else:
                    table_rows.append(f"| {product} | — | — |")
            else:
                table_rows.append(f"| {product} | ⏳ Đang cập nhật | — |")

        table = "| Sản phẩm | Giá | Xu hướng |\n|---------|-----|---------|\n" + "\n".join(table_rows)

        recent_html = ""
        transactions = db.get_transactions(user_id)[:10]
        for t in transactions:
            farmer = t.get("farmers", {}).get("name", "N/A")
            product = t.get("products", {}).get("name", "N/A")
            net = t.get("net_weight", 0) or 0
            amount = t.get("total_amount", 0) or 0
            paid = "✅" if t.get("payment_status") == "paid" else "📝"
            date_str = str(t.get("created_at", ""))[:10]
            recent_html += f"- {paid} {date_str}: {format_kg(net)} {product} từ {farmer} ({format_vnd(amount)})\n"

        if not recent_html:
            recent_html = "Chưa có giao dịch gần đây."

        info = f"""
## 📊 Tổng Quan Thị Trường

{web_prices_html}

### 💹 Bảng Giá Thị Trường
{table}

### 🕐 Hoạt động gần đây
{recent_html}

*Dữ liệu cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}*
"""
        return info, format_kg(total_stock), format_vnd(total_value), str(total_trans), str(total_farmers), format_vnd(coffee_price), ""

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"❌ Lỗi: {str(e)}", "—", "—", "—", "—", "—", "—"


# ──────────────────────────────────────────────
# TAB 2: TRANSACTIONS
# ──────────────────────────────────────────────

def get_transaction_form_data():
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    farmers = []
    products = []
    if db and user_id:
        try:
            farmers = [f"{f['name']} - {f.get('phone','')}" for f in db.get_farmers(user_id)]
            products = [p["name"] for p in db.get_products(user_id)]
        except:
            pass
    if not farmers: farmers = ["Chưa có nông dân"]
    if not products: products = ["Chưa có sản phẩm"]
    return farmers, products


def calculate_net_weight_fn(gross, package, moisture, impurity, product_name, unit_price):
    try:
        gross = float(gross or 0)
        package = float(package or 0)
        moisture = float(moisture or 0)
        impurity = float(impurity or 0)
        unit_price = float(unit_price or 0)
    except ValueError:
        return "### ⚠️ Vui lòng nhập số hợp lệ", "### ⚠️", "### ⚠️"
    raw_net = max(0, gross - package)
    moisture_excess = max(0, moisture - 12.5)
    impurity_excess = max(0, impurity - 0.5)
    moisture_sub = raw_net * moisture_excess * 1.2 / 100
    impurity_sub = raw_net * impurity_excess * 1.0 / 100
    net = max(0, raw_net - moisture_sub - impurity_sub)
    return (f"### 🔻 Trừ: **{raw_net - net:,.1f} kg**",
            f"### ✅ Cân tịnh: **{net:,.1f} kg**",
            f"### 💵 Thành tiền: **{net * unit_price:,.0f} ₫**")


def save_transaction(farmer, product, gross, package, moisture, impurity, price, payment):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    if not user_id: return "⚠️ Vui lòng đăng nhập"

    try:
        gross = float(gross or 0)
        package = float(package or 0)
        moisture = float(moisture or 0)
        impurity = float(impurity or 0)
        price = float(price or 0)
    except ValueError:
        return "❌ Vui lòng nhập số hợp lệ"
    if gross <= 0 or price <= 0:
        return "❌ Tổng cân và đơn giá phải > 0"

    farmers = db.get_farmers(user_id)
    farmer_id = None
    for f in farmers:
        key = f"{f['name']} - {f.get('phone','')}"
        if key == farmer or f['name'] == farmer:
            farmer_id = f['id']
            break
    if not farmer_id: return "❌ Không tìm thấy nông dân"

    products = db.get_products(user_id)
    product_id = None
    for p in products:
        if p['name'] == product:
            product_id = p['id']
            break
    if not product_id: return "❌ Không tìm thấy sản phẩm"

    raw_net = max(0, gross - package)
    moisture_excess = max(0, moisture - 12.5)
    impurity_excess = max(0, impurity - 0.5)
    moisture_sub = raw_net * moisture_excess * 1.2 / 100
    impurity_sub = raw_net * impurity_excess * 1.0 / 100
    net = max(0, raw_net - moisture_sub - impurity_sub)
    total = net * price

    from database.models import Transaction as Tx
    tx = Tx(
        id=None, user_id=user_id,
        farmer_id=farmer_id, product_id=product_id,
        gross_weight=gross, package_weight=package,
        measured_moisture=moisture, measured_impurity=impurity,
        net_weight=net, unit_price=price,
        total_amount=total, payment_status='paid' if payment in ('paid', 'Trả ngay') else 'debt',
    )
    result = db.create_transaction(tx)
    if result:
        return f"✅ **Giao dịch thành công!**\n- Cân tịnh: {format_kg(net)}\n- Thành tiền: {format_vnd(total)}"
    return "❌ Không thể lưu giao dịch"


def list_transactions() -> pd.DataFrame:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return pd.DataFrame([{"Lỗi": "Database not connected"}])
    txs = db.get_transactions(user_id)
    data = []
    for t in txs:
        data.append({
            "Ngày": str(t.get("created_at", ""))[:10],
            "Nông dân": t.get("farmers", {}).get("name", "N/A"),
            "Sản phẩm": t.get("products", {}).get("name", "N/A"),
            "Cân tịnh (kg)": round(float(t.get("net_weight") or 0), 1),
            "Thành tiền (VNĐ)": format_vnd(float(t.get("total_amount") or 0)),
            "TT": "✅" if t.get("payment_status") == "paid" else "📝",
        })
    if not data: return pd.DataFrame([{"Thông báo": "Chưa có giao dịch nào"}])
    return pd.DataFrame(data)


# ──────────────────────────────────────────────
# TAB 3: FARMERS
# ──────────────────────────────────────────────

def list_farmers() -> pd.DataFrame:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return pd.DataFrame([{"Lỗi": "Database not connected"}])
    farmers = db.get_farmers(user_id)
    data = [{"ID": f["id"], "Tên": f["name"], "SĐT": f.get("phone", ""),
             "Địa chỉ": f.get("address", ""), "Công nợ (VNĐ)": format_vnd(float(f.get("total_debt") or 0)),
             "Ngày tạo": str(f.get("created_at", ""))[:10]} for f in farmers]
    if not data: return pd.DataFrame([{"Thông báo": "Chưa có nông dân"}])
    return pd.DataFrame(data)


def save_farmer(name, phone, address):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    if not name.strip(): return "❌ Tên không được để trống"
    from database.models import Farmer
    farmer = Farmer(id=None, user_id=user_id, name=name.strip(),
                    phone=phone.strip(), address=address.strip(), total_debt=0)
    result = db.create_farmer(farmer)
    if result: return f"✅ Đã thêm nông dân **{name}**"
    return "❌ Không thể thêm nông dân"


def delete_farmer(farmer_name):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    farmers = db.get_farmers(user_id)
    for f in farmers:
        if f["name"] == farmer_name.strip():
            db.delete_farmer(f["id"])
            return f"✅ Đã xóa nông dân **{farmer_name}**"
    return "❌ Không tìm thấy nông dân"


def get_farmer_debt_summary() -> str:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    farmers = db.get_farmers(user_id)
    total = sum(float(f.get("total_debt") or 0) for f in farmers)
    in_debt = sum(1 for f in farmers if (f.get("total_debt") or 0) > 0)
    top = sorted([f for f in farmers if (f.get("total_debt") or 0) > 0],
                 key=lambda x: float(x.get("total_debt") or 0), reverse=True)[:5]
    html = f"**💰 Tổng công nợ:** {format_vnd(total)} | **Số hộ nợ:** {in_debt}\n\n"
    if top:
        html += "**Top hộ nợ nhiều nhất:**\n"
        for i, f in enumerate(top, 1):
            html += f"{i}. **{f['name']}** - {format_vnd(float(f.get('total_debt') or 0))}\n"
    return html


# ──────────────────────────────────────────────
# TAB 4: INVENTORY
# ──────────────────────────────────────────────

def list_inventory() -> pd.DataFrame:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return pd.DataFrame([{"Lỗi": "Database not connected"}])
    inv = db.get_inventory(user_id)
    data = [{"Sản phẩm": i.get("products", {}).get("name", "N/A"),
             "Tồn kho (kg)": round(float(i.get("current_stock") or 0), 1),
             "Cập nhật": str(i.get("last_updated", ""))[:16]} for i in inv]
    if not data: return pd.DataFrame([{"Thông báo": "Kho trống"}])
    return pd.DataFrame(data)


def adjust_inventory(product_name, quantity, adj_type):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    try:
        qty = float(quantity or 0)
    except ValueError:
        return "❌ Số lượng không hợp lệ"
    if qty <= 0: return "❌ Số lượng phải > 0"
    products = db.get_products(user_id)
    pid = None
    for p in products:
        if p["name"] == product_name:
            pid = p["id"]
            break
    if not pid: return "❌ Không tìm thấy sản phẩm"
    is_add = adj_type == "gain"
    ok = db.update_inventory(user_id, pid, qty, is_add=is_add)
    if ok:
        action = "tăng" if is_add else "giảm"
        return f"✅ Đã {action} tồn kho **{product_name}** {format_kg(qty)}"
    return "❌ Không thể cập nhật tồn kho"


# ──────────────────────────────────────────────
# TAB 5: PRODUCTS
# ──────────────────────────────────────────────

def list_products() -> pd.DataFrame:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return pd.DataFrame([{"Lỗi": "Database not connected"}])
    prods = db.get_products(user_id)
    data = [{"ID": p["id"], "Tên": p["name"], "Danh mục": p.get("category", "—"),
             "Đơn vị": p.get("base_unit", "kg"), "Ngày tạo": str(p.get("created_at", ""))[:10]} for p in prods]
    if not data: return pd.DataFrame([{"Thông báo": "Chưa có sản phẩm"}])
    return pd.DataFrame(data)


def save_product(name, category):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    if not name.strip(): return "❌ Tên không được để trống"
    from database.models import Product
    prod = Product(id=None, user_id=user_id, name=name.strip(), category=category.strip() if category.strip() else None)
    result = db.create_product(prod)
    if result: return f"✅ Đã thêm sản phẩm **{name}**"
    return "❌ Không thể thêm sản phẩm"


def delete_product(product_name):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    prods = db.get_products(user_id)
    for p in prods:
        if p["name"] == product_name.strip():
            db.delete_product(p["id"])
            return f"✅ Đã xóa sản phẩm **{product_name}**"
    return "❌ Không tìm thấy sản phẩm"


# ──────────────────────────────────────────────
# TAB 6: AI ADVISOR
# ──────────────────────────────────────────────

def ai_chat(message: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    """Chat handler — returns list of dicts with 'role' and 'content' (Gradio 6.0 format)."""
    if not message or not message.strip():
        return "", history

    db = AppState.get_db()
    if not db:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "⚠️ **Database chưa kết nối.** Vui lòng cấu hình Settings trước."})
        return "", history

    user_id = AppState.ensure_user()
    if not user_id:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "⚠️ **Vui lòng đăng nhập để sử dụng AI Advisor.**"})
        return "", history

    try:
        from core.agent.agri_agent import create_agri_agent
        from core.advisor_context import build_advisor_context, format_context_for_display
        from core.llm_provider import get_llm_router

        context = build_advisor_context(db, user_id)
        context_display = format_context_for_display(context)

        router = get_llm_router()
        if not router.all_configured:
            from core.ai_engine import get_gemini_agent
            agent = get_gemini_agent()
            if not agent.config.configured:
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": "⚠️ **Chưa cấu hình API Key cho AI.**\n\nVào tab **Settings → AI & API** và nhập ít nhất một API key:\n- **GEMINI_API_KEY** (khuyên dùng)\n- **OPENROUTER_API_KEY**\n- **GROQ_API_KEY**"})
                return "", history
            result = agent.ask_advisor(message, context)
            response = result.get("response", "") if result["success"] else f"❌ {result.get('error', 'Lỗi')}"
            if context_display and response:
                response += f"\n\n---\n{context_display}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return "", history

        agent = create_agri_agent(db, user_id)
        result = agent.run(message)
        if result["success"]:
            response = result["response"]
            if context_display:
                response += f"\n\n---\n{context_display}"
        else:
            response = f"❌ {result.get('error', 'Lỗi')}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        return "", history

    except Exception as e:
        logger.error(f"AI error: {e}")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": f"❌ **Lỗi:** {str(e)}"})
        return "", history


# ──────────────────────────────────────────────
# TAB 7: REPORTS
# ──────────────────────────────────────────────

def export_transactions_excel() -> Optional[bytes]:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return None
    txs = db.get_transactions(user_id)
    data = [{"Ngày": str(t.get("created_at", ""))[:10], "Nông dân": t.get("farmers", {}).get("name", "N/A"),
             "Sản phẩm": t.get("products", {}).get("name", "N/A"), "Tổng cân (kg)": t.get("gross_weight"),
             "Bao bì (kg)": t.get("package_weight"), "Độ ẩm (%)": t.get("measured_moisture"),
             "Tạp chất (%)": t.get("measured_impurity"), "Cân tịnh (kg)": t.get("net_weight"),
             "Đơn giá (VNĐ/kg)": t.get("unit_price"), "Thành tiền (VNĐ)": t.get("total_amount"),
             "Thanh toán": "Đã trả" if t.get("payment_status") == "paid" else "Ghi nợ"} for t in txs]
    if not data: return None
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Giao dịch", index=False)
    buf.seek(0)
    return buf.getvalue()


def export_products_excel() -> Optional[bytes]:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return None
    prods = db.get_products(user_id)
    data = [{"Tên sản phẩm": p["name"], "Danh mục": p.get("category", ""),
             "Đơn vị": p.get("base_unit", "kg"), "Ngày tạo": str(p.get("created_at", ""))[:10]} for p in prods]
    if not data: return None
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Sản phẩm", index=False)
    buf.seek(0)
    return buf.getvalue()


def export_farmers_excel() -> Optional[bytes]:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return None
    farmers = db.get_farmers(user_id)
    data = [{"Tên nông dân": f["name"], "Số điện thoại": f.get("phone", ""),
             "Địa chỉ": f.get("address", ""), "Công nợ (VNĐ)": f.get("total_debt", 0)} for f in farmers]
    if not data: return None
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Nông dân", index=False)
    buf.seek(0)
    return buf.getvalue()


def export_inventory_excel() -> Optional[bytes]:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return None
    inv = db.get_inventory(user_id)
    data = [{"Sản phẩm": i.get("products", {}).get("name", "N/A"), "Tồn kho (kg)": i.get("current_stock", 0)} for i in inv]
    if not data: return None
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Tồn kho", index=False)
    buf.seek(0)
    return buf.getvalue()


# ──────────────────────────────────────────────
# TAB 8: MARKET CONNECTION
# ──────────────────────────────────────────────

def get_market_connection_html() -> str:
    try:
        from core.market_connection import MarketConnectionManager
        manager = MarketConnectionManager()
        data = manager.get_connections()
        if not data or data.error:
            return f"⚠️ Không thể tải dữ liệu kết nối"
        html = f"""
## 🌐 Kết nối Thị trường Nông sản

**Nguồn:** {data.source_name} | **Cập nhật:** {data.fetched_at}

### 📊 Thống kê
- 🤝 **Đối tác:** {data.stats.get('total_partners', 0)}
- 📍 **Tỉnh thành:** {data.stats.get('total_provinces', 0)}

### 📂 Danh mục kết nối
"""
        for cat in data.categories[:6]:
            html += f"- **{cat.icon} {cat.name}** ({cat.count} đối tác)\n"
        html += "\n### 🌟 Đối tác nổi bật\n"
        for p in data.partners[:6]:
            html += f"- {p.icon} **{p.name}**: {p.description}\n"
        return html
    except ImportError:
        return "⚠️ Module market_connection chưa được cài đặt."
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"


# ──────────────────────────────────────────────
# TAB 9: GRADING RULES
# ──────────────────────────────────────────────

def list_grading_rules() -> pd.DataFrame:
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return pd.DataFrame([{"Lỗi": "Database not connected"}])
    rules = db.get_grading_rules(user_id)
    data = [{"Sản phẩm": r.get("products", {}).get("name", "N/A"), "Ẩm chuẩn (%)": r.get("std_moisture", "—"),
             "Tỉ lệ trừ ẩm": f"×{r.get('moisture_ratio', '—')}", "Tạp chuẩn (%)": r.get("std_impurity", "—"),
             "Tỉ lệ trừ tạp": f"×{r.get('impurity_ratio', '—')}", "Kích hoạt": "✅" if r.get("is_active") else "❌"} for r in rules]
    if not data: return pd.DataFrame([{"Thông báo": "Chưa có quy tắc trừ lùi"}])
    return pd.DataFrame(data)


def save_grading_rule(product_name, std_moisture, moisture_ratio, std_impurity, impurity_ratio):
    db = AppState.get_db()
    user_id = AppState.ensure_user()
    if not db: return "⚠️ Database not connected"
    try:
        sm = float(std_moisture or 12.5)
        mr = float(moisture_ratio or 1.2)
        si = float(std_impurity or 0.5)
        ir = float(impurity_ratio or 1.0)
    except ValueError:
        return "❌ Giá trị không hợp lệ"
    prods = db.get_products(user_id)
    pid = None
    for p in prods:
        if p["name"] == product_name:
            pid = p["id"]
            break
    if not pid: return "❌ Không tìm thấy sản phẩm"
    existing = db.get_grading_rules(user_id, pid)
    if existing:
        db.update_grading_rule(existing[0]["id"], {"std_moisture": sm, "moisture_ratio": mr, "std_impurity": si, "impurity_ratio": ir, "is_active": True})
        return f"✅ Đã cập nhật quy tắc cho **{product_name}**"
    from database.models import GradingRule
    rule = GradingRule(id=None, user_id=user_id, product_id=pid, std_moisture=sm, moisture_ratio=mr, std_impurity=si, impurity_ratio=ir, is_active=True)
    result = db.create_grading_rule(rule)
    if result: return f"✅ Đã tạo quy tắc cho **{product_name}**"
    return "❌ Không thể tạo quy tắc"


# ──────────────────────────────────────────────
# TAB 10: SETTINGS
# ──────────────────────────────────────────────

def save_settings(supabase_url, supabase_key, gemini_key, openrouter_key, groq_key):
    AppState.supabase_url = supabase_url.strip()
    AppState.supabase_key = supabase_key.strip()
    AppState.gemini_key = gemini_key.strip()
    AppState.openrouter_key = openrouter_key.strip()
    AppState.groq_key = groq_key.strip()
    AppState.reset()
    db = AppState.get_db()
    if db:
        return "✅ **Kết nối thành công!** Database đã sẵn sàng."
    return "⚠️ **Chưa kết nối được database.** Kiểm tra SUPABASE_URL và SUPABASE_KEY."


def get_settings_defaults():
    return (AppState.supabase_url or os.environ.get("SUPABASE_URL", ""),
            AppState.supabase_key or os.environ.get("SUPABASE_KEY", ""),
            AppState.gemini_key or os.environ.get("GEMINI_API_KEY", ""),
            AppState.openrouter_key or os.environ.get("OPENROUTER_API_KEY", ""),
            AppState.groq_key or os.environ.get("GROQ_API_KEY", ""))


def get_status_html():
    db = AppState.get_db()
    email = AppState.current_user_email
    if db and email:
        return f'<span class="status-badge online">🟢 Đã kết nối · {email}</span>'
    elif db:
        return '<span class="status-badge online">🟢 Đã kết nối</span>'
    return '<span class="status-badge offline">🔴 Chưa kết nối</span>'


# ──────────────────────────────────────────────
# LOGIN UI FUNCTIONS (Gradio event handlers)
# ──────────────────────────────────────────────

def _handle_login(email: str, password: str) -> Tuple[str, str, str, str]:
    """Login handler: returns (auth_state, login_msg_html, user_display_md, status_html)"""
    result = do_login(email, password)
    if result["success"]:
        return (
            "logged_in",
            f'<div class="login-success">✅ Đăng nhập thành công! Chào mừng <strong>{result["email"]}</strong></div>',
            f"<div style='display:flex;align-items:center;gap:8px;'><div><div style='font-weight:600;font-size:0.95em;'>Xin chào, {result['email'].split('@')[0].title()}!</div><div style='font-size:0.78em;color:var(--text-muted);'>Gia Lai Agri-Smart Hub</div></div></div>",
            get_status_html(),
        )
    else:
        return (
            "login",
            f'<div class="login-error">{result["message"]}</div>',
            "",
            get_status_html(),
        )


def _handle_register(email: str, password: str) -> str:
    """Register handler."""
    result = do_register(email, password)
    # Return success/error with styling
    if result["success"]:
        return f'<div class="login-success">{result["message"]}</div>'
    return f'<div class="login-error">{result["message"]}</div>'


def _handle_forgot(email: str) -> str:
    """Forgot password handler."""
    result = do_forgot_password(email)
    if result["success"]:
        return f'<div class="login-success">{result["message"]}</div>'
    return f'<div class="login-error">{result["message"]}</div>'


def _handle_logout() -> Tuple[str, str, str, str, str]:
    """Logout handler: clear user state, show login."""
    AppState.current_user_id = ""
    AppState.current_user_email = ""
    return ("", "", "login", '<div class="login-success">🔓 Đã đăng xuất thành công!</div>', get_status_html())


# ──────────────────────────────────────────────
# BUILD GRADIO APP
# ──────────────────────────────────────────────

def build_app():
    with gr.Blocks(
        title="GASH - Gia Lai Agri-Smart Hub",
    ) as demo:

        # ──────── STATE ────────
        auth_state = gr.State("login")

        # ==================== LOGIN VIEW ====================
        with gr.Column(visible=True, elem_classes="login-page login-card-parent") as login_page:
            logo_html = _get_logo_html()
            gr.HTML(f"""
            <div class="login-card">
                <div class="login-logo">
                    {logo_html}
                </div>
                <div class="login-title">AGRI-SMART HUB</div>
                <div class="login-subtitle">Hệ thống quản lý nông sản thông minh — Gia Lai</div>
            """)

            # --- Login form ---
            with gr.Column(visible=True, elem_id="login_form") as login_form:
                login_email = gr.Textbox(
                    label="📧 Email",
                    placeholder="Nhập email của bạn",
                    value="",
                    elem_classes="gr-input",
                )
                login_password = gr.Textbox(
                    label="🔒 Mật khẩu",
                    placeholder="Nhập mật khẩu",
                    type="password",
                    value="",
                    elem_classes="gr-input",
                )
                # Demo credentials info — nổi bật, to, dễ nhìn
                gr.HTML("""
                <div class="demo-info">
                    <span class="demo-label">🧪 Tài khoản dùng thử</span>
                    <span class="demo-creds">📧 viu106018@donga.edu.vn · 🔑 123456</span>
                </div>
                """)
                login_btn = gr.Button("ĐĂNG NHẬP", variant="primary", size="lg")
                login_msg = gr.HTML("")

                with gr.Row():
                    switch_to_register = gr.Button("📝 Tạo tài khoản", variant="secondary", size="sm", scale=1)
                    switch_to_forgot = gr.Button("🔑 Quên mật khẩu?", variant="secondary", size="sm", scale=1)

            # --- Register form (hidden) ---
            with gr.Column(visible=False, elem_id="register_form") as register_form:
                reg_email = gr.Textbox(label="📧 Email", placeholder="Nhập email của bạn")
                reg_password = gr.Textbox(label="🔒 Mật khẩu (ít nhất 6 ký tự)", placeholder="Nhập mật khẩu", type="password")
                reg_confirm = gr.Textbox(label="🔒 Xác nhận mật khẩu", placeholder="Nhập lại mật khẩu", type="password")
                register_btn = gr.Button("📝 ĐĂNG KÝ", variant="primary", size="lg")
                reg_msg = gr.HTML("")

                with gr.Row():
                    back_to_login_from_reg = gr.Button("← Quay lại đăng nhập", variant="secondary", size="sm")
                    gr.HTML("")

            # --- Forgot password form (hidden) ---
            with gr.Column(visible=False, elem_id="forgot_form") as forgot_form:
                forgot_email = gr.Textbox(label="📧 Email", placeholder="Nhập email của bạn")
                forgot_btn = gr.Button("📧 GỬI YÊU CẦU ĐẶT LẠI", variant="primary", size="lg")
                forgot_msg = gr.HTML("")

                with gr.Row():
                    back_to_login_from_forgot = gr.Button("← Quay lại đăng nhập", variant="secondary", size="sm")
                    gr.HTML("")

            gr.HTML("""
                <div class="login-footer">🌾 GASH — Gia Lai Agri-Smart Hub · Phiên bản Web</div>
            </div>
            """)

        # ==================== MAIN APP VIEW ====================
        with gr.Column(visible=False, elem_classes="app-wrapper") as main_app:
            # ──────── TOP BAR ────────
            gr.HTML("""
            <div class="top-bar">
                <div class="top-bar-left">
                    <div class="top-bar-logo">🌾</div>
                    <div>
                        <div class="top-bar-title" id="user-greeting-title">GASH — Agri-Smart Hub</div>
                        <div class="top-bar-subtitle">Hệ thống quản lý nông sản · Gia Lai</div>
                    </div>
                </div>
                <div class="top-bar-right" id="top-bar-status">
            """)
            user_display = gr.HTML("")
            status = gr.HTML(get_status_html())
            gr.HTML("""
                    <button id="logout-btn" class="gr-button gr-button-stop" onclick="document.querySelector('#logout-btn-internal').click()" style="padding:4px 12px !important;font-size:0.8em !important;">🚪 Đăng xuất</button>
                </div>
            </div>
            """)
            logout_btn = gr.Button("🚪 Đăng xuất", variant="stop", size="sm", elem_id="logout-btn-internal", visible=False, elem_classes="gr-button-stop")

            # ──────── TABS ────────
            with gr.Tabs(elem_classes="tabs"):

                # ===== TAB 1: DASHBOARD =====
                with gr.TabItem("📊 Dashboard", id="dashboard"):
                    gr.HTML(f"""
                    <div class="section-title">
                        <h2 style="margin:0;">📈 Tổng Quan Thị Trường</h2>
                        <span class="line"></span>
                    </div>
                    <p style="color:var(--text-muted);font-size:0.88em;margin:0 0 20px 0;">
                        Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                    """)

                    with gr.Row():
                        with gr.Column(scale=1, min_width=160):
                            kpi_stock = gr.HTML("""<div class="kpi-card kpi-green">
                                <div class="kpi-icon">📦</div>
                                <div class="kpi-label">Tồn kho</div>
                                <div class="kpi-value">—</div>
                            </div>""")
                        with gr.Column(scale=1, min_width=160):
                            kpi_revenue = gr.HTML("""<div class="kpi-card kpi-gold">
                                <div class="kpi-icon">💰</div>
                                <div class="kpi-label">Doanh thu</div>
                                <div class="kpi-value">—</div>
                            </div>""")
                        with gr.Column(scale=1, min_width=160):
                            kpi_trans = gr.HTML("""<div class="kpi-card kpi-blue">
                                <div class="kpi-icon">📋</div>
                                <div class="kpi-label">Giao dịch</div>
                                <div class="kpi-value">—</div>
                            </div>""")
                        with gr.Column(scale=1, min_width=160):
                            kpi_farmers = gr.HTML("""<div class="kpi-card kpi-purple">
                                <div class="kpi-icon">👨‍🌾</div>
                                <div class="kpi-label">Nông dân</div>
                                <div class="kpi-value">—</div>
                            </div>""")
                        with gr.Column(scale=1, min_width=160):
                            kpi_coffee = gr.HTML("""<div class="kpi-card kpi-teal">
                                <div class="kpi-icon">☕</div>
                                <div class="kpi-label">Giá Cà phê</div>
                                <div class="kpi-value">—</div>
                            </div>""")

                    with gr.Row():
                        refresh_btn = gr.Button("🔄 Làm mới dữ liệu", variant="primary", size="sm", scale=0)

                    dashboard_content = gr.Markdown(
                        'Nhấn **🔄 Làm mới** để tải dữ liệu.'
                    )

                    def refresh_dashboard():
                        info, stock, rev, trans, farmers, cf, _ = render_dashboard()
                        # Build rich KPI HTML cards
                        stock_card = f"""<div class="kpi-card kpi-green">
                            <div class="kpi-icon">📦</div>
                            <div class="kpi-label">Tồn kho</div>
                            <div class="kpi-value">{stock}</div>
                        </div>"""
                        rev_card = f"""<div class="kpi-card kpi-gold">
                            <div class="kpi-icon">💰</div>
                            <div class="kpi-label">Doanh thu</div>
                            <div class="kpi-value">{rev}</div>
                        </div>"""
                        trans_card = f"""<div class="kpi-card kpi-blue">
                            <div class="kpi-icon">📋</div>
                            <div class="kpi-label">Giao dịch</div>
                            <div class="kpi-value">{trans}</div>
                        </div>"""
                        farmers_card = f"""<div class="kpi-card kpi-purple">
                            <div class="kpi-icon">👨‍🌾</div>
                            <div class="kpi-label">Nông dân</div>
                            <div class="kpi-value">{farmers}</div>
                        </div>"""
                        coffee_card = f"""<div class="kpi-card kpi-teal">
                            <div class="kpi-icon">☕</div>
                            <div class="kpi-label">Giá Cà phê</div>
                            <div class="kpi-value">{cf}</div>
                        </div>"""
                        # Wrap dashboard content in a nice card
                        if info.startswith("❌"):
                            content_md = f"<div class='login-error'>{info}</div>"
                        else:
                            content_md = info

                        return (
                            stock_card, rev_card, trans_card, farmers_card, coffee_card,
                            content_md
                        )

                    refresh_btn.click(
                        fn=refresh_dashboard,
                        outputs=[kpi_stock, kpi_revenue, kpi_trans, kpi_farmers, kpi_coffee, dashboard_content],
                    )
                    demo.load(
                        fn=refresh_dashboard,
                        outputs=[kpi_stock, kpi_revenue, kpi_trans, kpi_farmers, kpi_coffee, dashboard_content],
                    )

                # ===== TAB 2: GIAO DỊCH =====
                with gr.TabItem("📋 Giao dịch", id="transactions"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">📋 Quản lý giao dịch thu mua</h2>
                        <span class="line"></span>
                    </div>
                    """)

                    # Nút chuyển đổi giữa Nhập và Danh sách (thay thế nested tabs)
                    with gr.Row():
                        switch_to_input_btn = gr.Button("➕ Nhập giao dịch", variant="primary", size="sm", scale=1)
                        switch_to_list_btn = gr.Button("📋 Danh sách giao dịch", variant="secondary", size="sm", scale=1)

                    # ─── NHẬP GIAO DỊCH ───
                    with gr.Column(visible=True, elem_id="tx_input_section") as tx_input_section:
                        with gr.Row():
                            with gr.Column(scale=1):
                                farmer_dd = gr.Dropdown(
                                    label="👨‍🌾 Nông dân",
                                    choices=["Chưa có nông dân"],
                                    value="Chưa có nông dân",
                                )
                                product_dd = gr.Dropdown(
                                    label="📦 Sản phẩm",
                                    choices=["Chưa có sản phẩm"],
                                    value="Chưa có sản phẩm",
                                )
                            with gr.Column(scale=1):
                                gross_input = gr.Number(label="⚖️ Tổng cân (kg)", value=0, minimum=0)
                                package_input = gr.Number(label="📦 Bao bì (kg)", value=0, minimum=0)
                            with gr.Column(scale=1):
                                moisture_input = gr.Number(label="💧 Độ ẩm (%)", value=12.5, minimum=0, maximum=100)
                                impurity_input = gr.Number(label="🧹 Tạp chất (%)", value=0.5, minimum=0, maximum=100)
                            with gr.Column(scale=1):
                                price_input = gr.Number(label="💰 Đơn giá (VNĐ/kg)", value=0, minimum=0)
                                payment_dd = gr.Radio(label="Thanh toán", choices=["Trả ngay", "Ghi nợ"], value="Trả ngay")

                        gr.HTML('<div style="margin: 12px 0;"></div>')
                        with gr.Row():
                            calc_btn = gr.Button("🧮 Tính toán", variant="secondary", size="sm", scale=0)
                            save_tx_btn = gr.Button("💾 Lưu giao dịch", variant="primary", scale=0)

                        with gr.Row():
                            with gr.Column(scale=1):
                                sub_label = gr.HTML("""
                                <div class="card" style="padding:16px;text-align:center;background:rgba(229,57,53,0.08);border-color:rgba(229,57,53,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">TRỪ LÙI</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#ef9a9a;">0 kg</div>
                                </div>
                                """)
                            with gr.Column(scale=1):
                                net_label = gr.HTML("""
                                <div class="card" style="padding:16px;text-align:center;background:rgba(76,175,80,0.08);border-color:rgba(76,175,80,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">CÂN TỊNH</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#81c784;">0 kg</div>
                                </div>
                                """)
                            with gr.Column(scale=1):
                                total_label = gr.HTML("""
                                <div class="card" style="padding:16px;text-align:center;background:rgba(249,168,37,0.08);border-color:rgba(249,168,37,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">THÀNH TIỀN</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#fdd835;">0 ₫</div>
                                </div>
                                """)

                        tx_result = gr.HTML("")

                        def calc_fn(gross, package, moisture, impurity, product, price):
                            r1, r2, r3 = calculate_net_weight_fn(gross, package, moisture, impurity, product, price)
                            import re
                            m1 = re.search(r'\*\*([\d,]+\.?\d*)\s*kg\*\*', r1)
                            m2 = re.search(r'\*\*([\d,]+\.?\d*)\s*kg\*\*', r2)
                            m3 = re.search(r'\*\*([\d,]+\.?\d*)\s*₫\*\*', r3)
                            sub_val = m1.group(1) if m1 else "0"
                            net_val = m2.group(1) if m2 else "0"
                            total_val = m3.group(1) if m3 else "0"
                            return (
                                f"""<div class="card" style="padding:16px;text-align:center;background:rgba(229,57,53,0.08);border-color:rgba(229,57,53,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">TRỪ LÙI</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#ef9a9a;">{sub_val} kg</div>
                                </div>""",
                                f"""<div class="card" style="padding:16px;text-align:center;background:rgba(76,175,80,0.08);border-color:rgba(76,175,80,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">CÂN TỊNH</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#81c784;">{net_val} kg</div>
                                </div>""",
                                f"""<div class="card" style="padding:16px;text-align:center;background:rgba(249,168,37,0.08);border-color:rgba(249,168,37,0.15);">
                                    <div style="font-size:0.8em;color:var(--text-muted);">THÀNH TIỀN</div>
                                    <div style="font-size:1.3em;font-weight:700;color:#fdd835;">{total_val} ₫</div>
                                </div>""",
                                ""
                            )
                        calc_btn.click(
                            fn=calc_fn,
                            inputs=[gross_input, package_input, moisture_input, impurity_input, product_dd, price_input],
                            outputs=[sub_label, net_label, total_label, tx_result],
                        )

                        def load_tx_form():
                            farmers, products = get_transaction_form_data()
                            return (
                                gr.Dropdown(choices=farmers, value=farmers[0] if farmers else "Chưa có nông dân"),
                                gr.Dropdown(choices=products, value=products[0] if products else "Chưa có sản phẩm"),
                            )

                        def save_tx(farmer, product, gross, package, moisture, impurity, price, payment):
                            msg = save_transaction(farmer, product, gross, package, moisture, impurity, price, payment)
                            if msg.startswith("✅"):
                                return f'<div class="login-success">{msg}</div>'
                            return f'<div class="login-error">{msg}</div>'

                        demo.load(fn=load_tx_form, outputs=[farmer_dd, product_dd])
                        save_tx_btn.click(
                            fn=save_tx,
                            inputs=[farmer_dd, product_dd, gross_input, package_input, moisture_input, impurity_input, price_input, payment_dd],
                            outputs=tx_result,
                        )

                    # ─── DANH SÁCH GIAO DỊCH ───
                    with gr.Column(visible=False, elem_id="tx_list_section") as tx_list_section:
                        refresh_tx_btn = gr.Button("🔄 Làm mới", size="sm")
                        tx_table = gr.Dataframe(
                            label="Danh sách giao dịch",
                            headers=["Ngày", "Nông dân", "Sản phẩm", "Cân tịnh (kg)", "Thành tiền (VNĐ)", "TT"],
                        )
                        refresh_tx_btn.click(fn=list_transactions, outputs=tx_table)

                    # Chuyển đổi giữa Nhập và Danh sách
                    def _show_tx_input():
                        return gr.update(visible=True), gr.update(visible=False), gr.update(variant="primary"), gr.update(variant="secondary")
                    def _show_tx_list():
                        return gr.update(visible=False), gr.update(visible=True), gr.update(variant="secondary"), gr.update(variant="primary")

                    switch_to_input_btn.click(
                        fn=_show_tx_input,
                        outputs=[tx_input_section, tx_list_section, switch_to_input_btn, switch_to_list_btn],
                    )
                    switch_to_list_btn.click(
                        fn=_show_tx_list,
                        outputs=[tx_input_section, tx_list_section, switch_to_input_btn, switch_to_list_btn],
                    )

                # ===== TAB 3: NÔNG DÂN =====
                with gr.TabItem("👨‍🌾 Nông dân", id="farmers"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">👨‍🌾 Quản lý nông dân & Công nợ</h2>
                        <span class="line"></span>
                    </div>
                    """)
                    with gr.Row():
                        with gr.Column(scale=1):
                            farmer_name = gr.Textbox(label="👤 Tên nông dân *", placeholder="Nhập tên nông dân")
                            farmer_phone = gr.Textbox(label="📞 Số điện thoại", placeholder="Số điện thoại")
                            farmer_address = gr.Textbox(label="📍 Địa chỉ", placeholder="Địa chỉ")
                            with gr.Row():
                                add_farmer_btn = gr.Button("➕ Thêm", variant="primary")
                                del_farmer_btn = gr.Button("🗑️ Xóa", variant="stop")
                            farmer_msg = gr.HTML("")
                        with gr.Column(scale=2):
                            debt_summary = gr.HTML(
                                f'<div class="card" style="padding:20px;"><h3>💰 Tổng quan công nợ</h3>'
                                f'<p style="color:var(--text-muted);">Nhấn "Làm mới" để xem dữ liệu</p></div>'
                            )
                            refresh_farmer_btn = gr.Button("🔄 Làm mới", size="sm")
                            farmer_table = gr.Dataframe(label="Danh sách nông dân")

                    def add_farmer_fn(name, phone, address):
                        msg = save_farmer(name, phone, address)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    def del_farmer_fn(name):
                        msg = delete_farmer(name)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    add_farmer_btn.click(fn=add_farmer_fn, inputs=[farmer_name, farmer_phone, farmer_address], outputs=farmer_msg)
                    del_farmer_btn.click(fn=del_farmer_fn, inputs=farmer_name, outputs=farmer_msg)

                    def refresh_farmers():
                        debt = get_farmer_debt_summary()
                        debt_html = f'<div class="card" style="padding:20px;"><div class="markdown-content">{debt}</div></div>'
                        return list_farmers(), debt_html
                    refresh_farmer_btn.click(fn=refresh_farmers, outputs=[farmer_table, debt_summary])

                # ===== TAB 4: TỒN KHO =====
                with gr.TabItem("📦 Tồn kho", id="inventory"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">📦 Quản lý tồn kho</h2>
                        <span class="line"></span>
                    </div>
                    """)
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.HTML('<div class="card" style="padding:20px;">')
                            inv_product = gr.Textbox(label="📦 Sản phẩm", placeholder="Tên sản phẩm")
                            inv_qty = gr.Number(label="Số lượng (kg)", value=0, minimum=0)
                            inv_type = gr.Radio(label="Loại điều chỉnh", choices=["loss", "gain"], value="loss")
                            adj_btn = gr.Button("📝 Xác nhận điều chỉnh", variant="primary")
                            adj_result = gr.HTML("")
                            gr.HTML('</div>')
                        with gr.Column(scale=2):
                            refresh_inv_btn = gr.Button("🔄 Làm mới", size="sm")
                            inv_table = gr.Dataframe(label="Bảng tồn kho")

                    def adj_inv_fn(product, qty, adj_type):
                        msg = adjust_inventory(product, qty, adj_type)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    adj_btn.click(fn=adj_inv_fn, inputs=[inv_product, inv_qty, inv_type], outputs=adj_result)
                    refresh_inv_btn.click(fn=list_inventory, outputs=inv_table)

                # ===== TAB 5: SẢN PHẨM =====
                with gr.TabItem("🏷️ Sản phẩm", id="products"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">🏷️ Quản lý sản phẩm</h2>
                        <span class="line"></span>
                    </div>
                    """)
                    with gr.Row():
                        with gr.Column(scale=1):
                            prod_name = gr.Textbox(label="📦 Tên sản phẩm *", placeholder="VD: Cà phê nhân")
                            prod_cat = gr.Dropdown(
                                label="🏷️ Danh mục",
                                choices=["Cà phê", "Hồ tiêu", "Điều", "Cacao", "Lúa gạo", "Khác"],
                                value="Khác",
                            )
                            with gr.Row():
                                add_prod_btn = gr.Button("➕ Thêm", variant="primary")
                                del_prod_btn = gr.Button("🗑️ Xóa", variant="stop")
                            prod_msg = gr.HTML("")
                        with gr.Column(scale=2):
                            refresh_prod_btn = gr.Button("🔄 Làm mới", size="sm")
                            prod_table = gr.Dataframe(label="Danh sách sản phẩm")

                    def add_prod_fn(name, cat):
                        msg = save_product(name, cat)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    def del_prod_fn(name):
                        msg = delete_product(name)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    add_prod_btn.click(fn=add_prod_fn, inputs=[prod_name, prod_cat], outputs=prod_msg)
                    del_prod_btn.click(fn=del_prod_fn, inputs=prod_name, outputs=prod_msg)
                    refresh_prod_btn.click(fn=list_products, outputs=prod_table)

                # ===== TAB 6: AI ADVISOR =====
                with gr.TabItem("🤖 AI Advisor", id="ai_advisor"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">🤖 Trò chuyện với AI Advisor</h2>
                        <span class="line"></span>
                    </div>
                    <div class="card" style="padding:16px;margin-bottom:16px;">
                        <p style="margin:0;color:var(--text-secondary);">
                            💡 Hỏi về giá thị trường, xu hướng, khuyến nghị mua/bán.
                            <br>Ví dụ: <em>"Giá cà phê hôm nay?"</em> · <em>"Phân tích thị trường hồ tiêu?"</em>
                        </p>
                    </div>
                    """)
                    chatbot = gr.Chatbot(
                        label="",
                        height=450,
                        avatar_images=("🧑‍🌾", "🌿"),
                        show_label=False,
                        elem_classes="gr-chatbot",
                    )
                    with gr.Row():
                        msg = gr.Textbox(
                            label="",
                            placeholder="Nhập câu hỏi...",
                            scale=4,
                            container=False,
                            elem_classes="gr-input",
                        )
                        send = gr.Button("📤 Gửi", variant="primary", scale=1, min_width=100)
                    clear = gr.Button("🗑️ Xóa lịch sử", variant="secondary", size="sm")

                    def respond(msg_text, chat):
                        if not msg_text or not msg_text.strip():
                            return "", chat
                        return ai_chat(msg_text, chat)
                    msg.submit(respond, [msg, chatbot], [msg, chatbot])
                    send.click(respond, [msg, chatbot], [msg, chatbot])
                    clear.click(lambda: [], outputs=chatbot)

                # ===== TAB 7: BÁO CÁO =====
                with gr.TabItem("📄 Báo cáo", id="reports"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">📄 Xuất báo cáo Excel</h2>
                        <span class="line"></span>
                    </div>
                    <p style="color:var(--text-muted);">Xuất dữ liệu ra file Excel để lưu trữ hoặc in ấn.</p>
                    """)
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("""
                            <div class="card" style="padding:20px;text-align:center;">
                                <div style="font-size:2em;margin-bottom:8px;">📊</div>
                                <h3 style="margin:4px 0;">Giao dịch</h3>
                                <p style="font-size:0.85em;color:var(--text-muted);margin:4px 0 16px;">Xuất toàn bộ giao dịch</p>
                            """)
                            tx_file = gr.File(label="", show_label=False)
                            gr.Button("📥 Xuất giao dịch", variant="primary", size="sm").click(
                                fn=export_transactions_excel, outputs=tx_file
                            )
                            gr.HTML("</div>")
                        with gr.Column():
                            gr.HTML("""
                            <div class="card" style="padding:20px;text-align:center;">
                                <div style="font-size:2em;margin-bottom:8px;">👨‍🌾</div>
                                <h3 style="margin:4px 0;">Nông dân</h3>
                                <p style="font-size:0.85em;color:var(--text-muted);margin:4px 0 16px;">Xuất danh sách nông dân</p>
                            """)
                            farmer_file = gr.File(label="", show_label=False)
                            gr.Button("📥 Xuất nông dân", variant="primary", size="sm").click(
                                fn=export_farmers_excel, outputs=farmer_file
                            )
                            gr.HTML("</div>")
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("""
                            <div class="card" style="padding:20px;text-align:center;">
                                <div style="font-size:2em;margin-bottom:8px;">🏷️</div>
                                <h3 style="margin:4px 0;">Sản phẩm</h3>
                                <p style="font-size:0.85em;color:var(--text-muted);margin:4px 0 16px;">Xuất danh sách sản phẩm</p>
                            """)
                            prod_file = gr.File(label="", show_label=False)
                            gr.Button("📥 Xuất sản phẩm", variant="primary", size="sm").click(
                                fn=export_products_excel, outputs=prod_file
                            )
                            gr.HTML("</div>")
                        with gr.Column():
                            gr.HTML("""
                            <div class="card" style="padding:20px;text-align:center;">
                                <div style="font-size:2em;margin-bottom:8px;">📦</div>
                                <h3 style="margin:4px 0;">Tồn kho</h3>
                                <p style="font-size:0.85em;color:var(--text-muted);margin:4px 0 16px;">Xuất bảng tồn kho</p>
                            """)
                            inv_file = gr.File(label="", show_label=False)
                            gr.Button("📥 Xuất tồn kho", variant="primary", size="sm").click(
                                fn=export_inventory_excel, outputs=inv_file
                            )
                            gr.HTML("</div>")

                # ===== TAB 8: KẾT NỐI =====
                with gr.TabItem("🌐 Kết nối", id="connection"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">🌐 Kết nối Thị trường Nông sản</h2>
                        <span class="line"></span>
                    </div>
                    """)
                    conn_content = gr.HTML(
                        f'<div class="card" style="padding:24px;"><div class="markdown-content">'
                        f'{get_market_connection_html()}</div></div>'
                    )

                    def refresh_conn():
                        html = get_market_connection_html()
                        return f'<div class="card" style="padding:24px;"><div class="markdown-content">{html}</div></div>'

                    gr.Button("🔄 Làm mới", size="sm").click(fn=refresh_conn, outputs=conn_content)

                # ===== TAB 9: QUY TẮC TRỪ LÙI =====
                with gr.TabItem("⚙️ Quy tắc trừ lùi", id="grading"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">⚙️ Cấu hình quy tắc trừ lùi</h2>
                        <span class="line"></span>
                    </div>
                    <p style="color:var(--text-muted);">
                        Thiết lập tiêu chuẩn độ ẩm, tạp chất và tỉ lệ trừ cho từng sản phẩm.
                    </p>
                    """)
                    with gr.Row():
                        with gr.Column(scale=1):
                            rule_product = gr.Textbox(label="📦 Sản phẩm", placeholder="Tên sản phẩm")
                            std_moisture = gr.Number(label="💧 Độ ẩm chuẩn (%)", value=12.5)
                            moisture_ratio = gr.Number(label="Tỉ lệ trừ ẩm (×)", value=1.2)
                            std_impurity = gr.Number(label="🧹 Tạp chuẩn (%)", value=0.5)
                            impurity_ratio = gr.Number(label="Tỉ lệ trừ tạp (×)", value=1.0)
                            save_rule_btn = gr.Button("💾 Lưu quy tắc", variant="primary")
                            rule_msg = gr.HTML("")
                        with gr.Column(scale=2):
                            refresh_rules_btn = gr.Button("🔄 Làm mới", size="sm")
                            rules_table = gr.Dataframe(label="Danh sách quy tắc")

                    def save_rule_fn(prod, sm, mr, si, ir):
                        msg = save_grading_rule(prod, sm, mr, si, ir)
                        if msg.startswith("✅"):
                            return f'<div class="login-success">{msg}</div>'
                        return f'<div class="login-error">{msg}</div>'

                    save_rule_btn.click(fn=save_rule_fn, inputs=[rule_product, std_moisture, moisture_ratio, std_impurity, impurity_ratio], outputs=rule_msg)
                    refresh_rules_btn.click(fn=list_grading_rules, outputs=rules_table)

                # ===== TAB 10: SETTINGS =====
                with gr.TabItem("⚙️ Cài đặt", id="settings"):
                    gr.HTML("""
                    <div class="section-title">
                        <h2 style="margin:0;">⚙️ Cấu hình hệ thống</h2>
                        <span class="line"></span>
                    </div>
                    """)
                    with gr.Accordion("🔌 Database (Supabase)", open=True):
                        supabase_url = gr.Textbox(
                            label="SUPABASE_URL",
                            placeholder="https://xxx.supabase.co",
                        )
                        supabase_key = gr.Textbox(
                            label="SUPABASE_KEY",
                            placeholder="eyJ...",
                            type="password",
                        )
                    with gr.Accordion("🤖 AI & API", open=True):
                        gr.HTML("""
                        <p style="color:var(--text-secondary);margin-bottom:12px;">
                            Cần ít nhất <strong>1 API key</strong> để AI Advisor hoạt động.
                            <br>Gemini được khuyên dùng nhất.
                        </p>
                        """)
                        gemini_key = gr.Textbox(
                            label="🔑 GEMINI_API_KEY",
                            placeholder="AIzaSy...",
                            type="password",
                        )
                        openrouter_key = gr.Textbox(
                            label="🔑 OPENROUTER_API_KEY",
                            placeholder="sk-or-v1-...",
                            type="password",
                        )
                        groq_key = gr.Textbox(
                            label="🔑 GROQ_API_KEY",
                            placeholder="gsk_...",
                            type="password",
                        )

                    save_btn = gr.Button("💾 Lưu cấu hình", variant="primary")
                    save_status = gr.HTML("")

                    demo.load(fn=get_settings_defaults, outputs=[supabase_url, supabase_key, gemini_key, openrouter_key, groq_key])
                    def _save_settings_handler(u, k, g, o, r):
                        msg = save_settings(u, k, g, o, r)
                        css_class = "login-success" if msg.startswith("✅") else "login-error"
                        return f'<div class="{css_class}">{msg}</div>'
                    save_btn.click(
                        fn=_save_settings_handler,
                        inputs=[supabase_url, supabase_key, gemini_key, openrouter_key, groq_key],
                        outputs=save_status,
                    ).then(fn=get_status_html, outputs=status)

            # ──────── FOOTER ────────
            gr.HTML("""
            <div class="app-footer">
                <p>🌾 <strong>GASH — Gia Lai Agri-Smart Hub</strong> | Phiên bản Web (Gradio) | Dữ liệu được cập nhật liên tục</p>
            </div>
            """)

        # ──────── LOGIN / LOGOUT EVENTS ────────
        def _toggle_after_login(s):
            if s == "logged_in":
                return gr.update(visible=False), gr.update(visible=True)
            return gr.update(visible=True), gr.update(visible=False)

        login_btn.click(
            fn=_handle_login,
            inputs=[login_email, login_password],
            outputs=[auth_state, login_msg, user_display, status],
        ).then(
            fn=_toggle_after_login,
            inputs=[auth_state],
            outputs=[login_page, main_app],
        ).then(
            fn=refresh_dashboard,
            outputs=[kpi_stock, kpi_revenue, kpi_trans, kpi_farmers, kpi_coffee, dashboard_content],
        ).then(
            fn=load_tx_form,
            outputs=[farmer_dd, product_dd],
        )

        # Register button
        register_btn.click(fn=_handle_register, inputs=[reg_email, reg_password], outputs=reg_msg)

        # Forgot password button
        forgot_btn.click(fn=_handle_forgot, inputs=forgot_email, outputs=forgot_msg)

        # Switch between login/register/forgot views
        def _show_register():
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
        switch_to_register.click(fn=_show_register, outputs=[login_form, register_form, forgot_form])

        def _show_forgot():
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        switch_to_forgot.click(fn=_show_forgot, outputs=[login_form, register_form, forgot_form])

        def _show_login():
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        back_to_login_from_reg.click(fn=_show_login, outputs=[login_form, register_form, forgot_form])
        back_to_login_from_forgot.click(fn=_show_login, outputs=[login_form, register_form, forgot_form])

        # Logout button
        logout_btn.click(
            fn=_handle_logout,
            outputs=[login_email, login_password, auth_state, login_msg, status],
        ).then(
            fn=lambda: gr.update(value=""),
            outputs=[user_display],
        ).then(
            fn=lambda: (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            ),
            outputs=[login_page, main_app, login_form, register_form, forgot_form],
        )

    return demo


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    load_dotenv()

    su = os.environ.get("SUPABASE_URL", "")
    sk = os.environ.get("SUPABASE_KEY", "")
    print(f"🔍 SUPABASE_URL: {'✅ Đã load' if su else '❌ TRỐNG'}")
    print(f"🔍 SUPABASE_KEY: {'✅ Đã load ({} ký tự)'.format(len(sk)) if sk else '❌ TRỐNG'}")

    AppState.supabase_url = su
    AppState.supabase_key = sk
    AppState.gemini_key = os.environ.get("GEMINI_API_KEY", "")
    AppState.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    AppState.groq_key = os.environ.get("GROQ_API_KEY", "")

    print("🔌 Đang thử kết nối database...")
    db = AppState.get_db()
    if db:
        print("✅ Kết nối database thành công!")
    else:
        print("❌ Kết nối database thất bại. Kiểm tra SUPABASE_URL và SUPABASE_KEY trong .env")

    demo = build_app()
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
        debug=False,
        theme=gr.themes.Base(
            primary_hue="green",
            font=gr.themes.GoogleFont("Inter"),
        ),
        css=MEGA_CSS + LOGIN_CLEANUP_CSS,
        head="""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <script>
        // After login, force-hide login elements so they don't push menu down
        (function() {
            var checkAndClean = function() {
                var loginEls = document.querySelectorAll('.login-page');
                loginEls.forEach(function(el) {
                    if (el.classList.contains('hide') || el.classList.contains('hidden')) {
                        el.style.setProperty('display', 'none', 'important');
                        el.style.setProperty('width', '0px', 'important');
                        el.style.setProperty('height', '0px', 'important');
                        el.style.setProperty('min-width', '0px', 'important');
                        el.style.setProperty('min-height', '0px', 'important');
                        el.style.setProperty('flex-grow', '0', 'important');
                        el.style.setProperty('position', 'absolute', 'important');
                        el.style.setProperty('overflow', 'hidden', 'important');
                        el.style.setProperty('opacity', '0', 'important');
                        el.style.setProperty('pointer-events', 'none', 'important');
                        el.style.setProperty('margin', '0px', 'important');
                        el.style.setProperty('padding', '0px', 'important');
                    }
                });
            };
            var interval = setInterval(function() {
                var mainApp = document.querySelector('[class*="app-wrapper"]');
                if (mainApp && mainApp.style.display !== 'none' && window.getComputedStyle(mainApp).display !== 'none') {
                    checkAndClean();
                    clearInterval(interval);
                }
            }, 200);
            setTimeout(function() { clearInterval(interval); }, 10000);
        })();
        </script>
        """
    )
