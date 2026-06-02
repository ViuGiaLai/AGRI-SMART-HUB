# -*- coding: utf-8 -*-
"""
AI Advisor — Agentic AI (ReAct + Function Calling).
Hiển thị từng bước: Perceive → Plan → Act (tools) → Reflect.
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading

from database.db_manager import DatabaseManager
from core.agent import create_agri_agent
from ui import theme as T


class AIAdvisorFrame(ctk.CTkFrame):
    """Trợ lý Agentic AI — minh bạch từng bước suy luận."""

    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, fg_color=T.BG_MAIN, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.agri_agent = None
        self.is_loading = False
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        ctk.CTkLabel(
            header, text="🤖 AI Advisor",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=T.TEXT_DARK,
        ).pack(side="left")
        badge = ctk.CTkLabel(
            header, text="  AGENTIC  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=T.PRIMARY, text_color=T.TEXT_ON_DARK,
            corner_radius=8,
        )
        badge.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            header,
            text="Agent tự gọi công cụ (tồn kho, giá, giao dịch, công nợ) — dữ liệu thật từ GASH",
            font=ctk.CTkFont(size=12), text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(12, 0))

        # Body: Chat | Agent steps
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(8, 12))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # —— Chat panel ——
        chat_shell = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD, border_width=1, border_color=("#e0e0e0", "#404040"),
        )
        chat_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        chat_shell.grid_columnconfigure(0, weight=1)
        chat_shell.grid_rowconfigure(0, weight=1)

        self.messages_area = ctk.CTkScrollableFrame(
            chat_shell, fg_color="transparent",
        )
        self.messages_area.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        chips = ctk.CTkFrame(chat_shell, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkLabel(chips, text="Gợi ý:", font=ctk.CTkFont(size=11), text_color=T.TEXT_MUTED).pack(side="left")
        for q in (
            "Phân tích đầy đủ xu hướng giá cà phê",
            "Tôi nên bán hay giữ hàng?",
            "Tổng quan rủi ro đại lý",
            "Top nông dân nợ nhiều",
        ):
            ctk.CTkButton(
                chips, text=q, height=28, corner_radius=14, font=ctk.CTkFont(size=10),
                fg_color=("#e8f5e9", "#2d4a35"), text_color=T.PRIMARY,
                hover_color=T.PRIMARY_LIGHT,
                command=lambda s=q: self._use_suggestion(s),
            ).pack(side="left", padx=3)

        input_bar = ctk.CTkFrame(chat_shell, fg_color=("#f5f5f5", "#252525"), corner_radius=T.CORNER_RADIUS)
        input_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.question_entry = ctk.CTkEntry(
            input_bar, placeholder_text="Hỏi Agent (tự tra cứu dữ liệu GASH)...",
            height=48, corner_radius=T.CORNER_RADIUS_SM, font=ctk.CTkFont(size=14), border_width=0,
        )
        self.question_entry.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=12)
        self.question_entry.bind("<Return>", lambda e: self.send_question())
        self.send_btn = ctk.CTkButton(
            input_bar, text="Gửi ➤", width=100, height=48,
            fg_color=T.PRIMARY, hover_color=T.PRIMARY_DARK,
            font=ctk.CTkFont(size=14, weight="bold"), command=self.send_question,
        )
        self.send_btn.pack(side="right", padx=(0, 8), pady=12)
        ctk.CTkButton(
            input_bar, text="🗑", width=44, height=48,
            fg_color=T.SECONDARY_LIGHT, command=self.clear_chat,
        ).pack(side="right", padx=(0, 4), pady=12)

        # —— Agent steps panel ——
        steps_shell = ctk.CTkFrame(
            body, corner_radius=T.CORNER_RADIUS,
            fg_color=T.BG_CARD, border_width=1, border_color=(T.PRIMARY, "#2d5a3d"),
        )
        steps_shell.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(
            steps_shell, text="🧠 Agent đang làm gì?",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=T.SECONDARY,
        ).pack(anchor="w", padx=14, pady=(14, 8))
        ctk.CTkLabel(
            steps_shell,
            text="ReAct: Perceive → Plan → Act (Tools) → Reflect",
            font=ctk.CTkFont(size=10), text_color=T.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 8))

        self.steps_scroll = ctk.CTkScrollableFrame(steps_shell, fg_color="transparent")
        self.steps_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        self._add_welcome()
        self._add_step_placeholder()

    def _add_welcome(self):
        self._add_ai_bubble(
            "Xin chào! Tôi là **AgriSmart Agent** (Agentic AI).\n\n"
            "Khác với chatbot thường, tôi **tự quyết định** gọi công cụ để lấy dữ liệu:\n"
            "• 📦 Tồn kho (kg)\n"
            "• 📈 Giá thị trường 7 ngày (VNĐ/kg)\n"
            "• 📋 Giao dịch & công nợ (VNĐ)\n"
            "• 💡 Khuyến nghị mua/bán\n\n"
            "Xem panel bên phải để theo dõi từng bước suy luận.",
        )

    def _add_step_placeholder(self):
        self._render_step({
            "type": "info",
            "message": "Chờ câu hỏi của bạn...",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })

    def _clear_steps_ui(self):
        for w in self.steps_scroll.winfo_children():
            w.destroy()

    def _on_agent_step(self, step: dict):
        """Callback từ thread nền → cập nhật UI an toàn."""
        self.after(0, lambda s=step.copy(): self._render_step(s))

    def _render_step(self, step: dict):
        if not self.steps_scroll.winfo_exists():
            return

        stype = step.get("type", "info")
        colors = {
            "perceive": T.INFO,
            "plan": T.SECONDARY,
            "act": T.ACCENT,
            "tool": T.PRIMARY,
            "reflect": T.PRIMARY,
            "info": T.TEXT_MUTED,
        }
        icons = {
            "perceive": "👁",
            "plan": "📝",
            "act": "⚡",
            "tool": "🔧",
            "reflect": "✅",
            "info": "ℹ️",
        }
        color = colors.get(stype, T.TEXT_MUTED)
        icon = icons.get(stype, "•")

        row = ctk.CTkFrame(
            self.steps_scroll, corner_radius=8,
            fg_color=("#f8f9fa", "#2a2a2a"),
        )
        row.pack(fill="x", pady=3)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6, 0))
        ctk.CTkLabel(
            top, text=f"{icon} {stype.upper()}",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=color,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=step.get("timestamp", ""),
            font=ctk.CTkFont(size=9), text_color=T.TEXT_MUTED,
        ).pack(side="right")

        msg = step.get("message") or step.get("summary", "")
        if step.get("tool"):
            msg = f"🔧 {step['tool']}\n{msg}"
            if step.get("args"):
                msg += f"\n↳ args: {step['args']}"

        ctk.CTkLabel(
            row, text=msg, font=ctk.CTkFont(size=10),
            text_color=T.TEXT_DARK, justify="left", wraplength=220,
        ).pack(anchor="w", padx=8, pady=(2, 6))

        self.steps_scroll._parent_canvas.yview_moveto(1.0)

    def _use_suggestion(self, text):
        self.question_entry.delete(0, "end")
        self.question_entry.insert(0, text)
        self.send_question()

    def _add_user_bubble(self, text):
        row = ctk.CTkFrame(self.messages_area, fg_color="transparent")
        row.pack(fill="x", pady=6, padx=12)
        bubble = ctk.CTkFrame(
            row, corner_radius=T.CORNER_RADIUS,
            fg_color=("#ffffff", "#3a3a3a"),
            border_width=1, border_color=("#e0e0e0", "#505050"),
        )
        bubble.pack(side="right", anchor="e", padx=(60, 0))
        ctk.CTkLabel(bubble, text="Bạn", font=ctk.CTkFont(size=10, weight="bold"), text_color=T.SECONDARY).pack(
            anchor="e", padx=14, pady=(8, 0))
        ctk.CTkLabel(
            bubble, text=text, font=ctk.CTkFont(size=13),
            text_color=T.TEXT_DARK, justify="left", wraplength=420,
        ).pack(anchor="e", padx=14, pady=(4, 8))
        self._scroll_chat()

    def _add_ai_bubble(self, text, footer: str = ""):
        row = ctk.CTkFrame(self.messages_area, fg_color="transparent")
        row.pack(fill="x", pady=6, padx=12)
        bubble = ctk.CTkFrame(
            row, corner_radius=T.CORNER_RADIUS,
            fg_color=(T.PRIMARY_LIGHT, "#1e3d28"),
            border_width=1, border_color=(T.PRIMARY, "#2d5a3d"),
        )
        bubble.pack(side="left", anchor="w", padx=(0, 60))
        ctk.CTkLabel(
            bubble, text="🤖 AgriSmart Agent",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=T.PRIMARY,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        body = text.strip()
        if footer:
            body = f"{body}\n\n—\n{footer}"
        ctk.CTkLabel(
            bubble, text=body, font=ctk.CTkFont(size=13),
            text_color=T.TEXT_DARK, justify="left", wraplength=480,
        ).pack(anchor="w", padx=14, pady=(4, 8))
        self._scroll_chat()

    def _scroll_chat(self):
        try:
            self.messages_area._parent_canvas.yview_moveto(1.0)
            self.update_idletasks()
        except Exception:
            pass
        
        # Also schedule a delayed scroll to ensure it happens after UI updates
        self.after(50, self._do_delayed_scroll)
    
    def _do_delayed_scroll(self):
        try:
            self.messages_area._parent_canvas.yview_moveto(1.0)
            # Force update and scroll again after a short delay
            self.after(100, self._force_scroll)
        except Exception:
            pass
    
    def _force_scroll(self):
        """Force scroll to bottom"""
        try:
            self.messages_area._parent_canvas.yview_moveto(1.0)
            self.update_idletasks()
        except Exception:
            pass

    def send_question(self, question=None):
        if self.is_loading:
            return
        question = (question or self.question_entry.get()).strip()
        if not question:
            messagebox.showwarning("Chú ý", "Vui lòng nhập câu hỏi!")
            return

        self._add_user_bubble(question)
        self.question_entry.delete(0, "end")
        self.is_loading = True
        self.send_btn.configure(state="disabled", text="...")
        self._clear_steps_ui()
        self._add_step_placeholder()

        self.agri_agent = create_agri_agent(
            self.db, self.user_id, on_step=self._on_agent_step,
        )

        thread = threading.Thread(target=self._run_agent, args=(question,), daemon=True)
        thread.start()

    def _run_agent(self, question: str):
        try:
            result = self.agri_agent.run(question)
            self.after(0, lambda: self._show_agent_result(result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _show_agent_result(self, result: dict):
        self.is_loading = False
        self.send_btn.configure(state="normal", text="Gửi ➤")

        if result.get("success"):
            tools = result.get("tools_used") or []
            footer = "🧠 Agentic AI"
            if tools:
                footer += f" · Tools: {', '.join(tools)}"
            footer += f" · {result.get('model_used', 'gemini')}"
            self._add_ai_bubble(result["response"], footer=footer)
        else:
            self._add_ai_bubble(
                f"❌ {result.get('error', 'Lỗi không xác định')}\n\n"
                "Kiểm tra GEMINI_API_KEY trong file .env.",
            )

    def _show_error(self, err: str):
        self.is_loading = False
        self.send_btn.configure(state="normal", text="Gửi ➤")
        self._add_ai_bubble(f"❌ Lỗi hệ thống: {err}")

    def clear_chat(self):
        if self.agri_agent:
            self.agri_agent.clear_session()
        for w in self.messages_area.winfo_children():
            w.destroy()
        self._clear_steps_ui()
        self._add_welcome()
        self._add_step_placeholder()
