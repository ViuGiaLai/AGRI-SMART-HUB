# -*- coding: utf-8 -*-
"""
AgriSmartAgent — Agentic AI cho GASH (Gia Lai Agri-Smart Hub).

Kiến trúc ReAct + Function Calling (Gemini):
  Perceive (câu hỏi) → Plan → Act (gọi tools) → Observe (kết quả) → Reflect → Trả lời

Mỗi bước được ghi vào `steps` để hiển thị minh bạch trên UI (phục vụ demo NCKH).
"""
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import google.generativeai as genai

from core.ai_engine import GeminiConfig, GeminiAgent
from core.agent.tools import AgriAgentToolkit
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Bạn là AgriSmart Agent — trợ lý AI tác tử (agentic) cho đại lý thu mua nông sản tại Gia Lai, Việt Nam.

VAI TRÒ:
- Tư vấn thị trường cà phê, hồ tiêu và chiến lược kinh doanh cho chủ đại lý.
- Bạn có QUYỀN gọi các công cụ (tools) để lấy dữ liệu THẬT từ hệ thống GASH.

QUY TRÌNH BẮT BUỘC (Agentic):
1. Phân tích câu hỏi → xác định cần dữ liệu gì.
2. Gọi ĐÚNG tool(s) — không đoán số trước khi có kết quả tool.
3. Tổng hợp từ kết quả tool → trả lời có cấu trúc.

QUY TẮC SỐ LIỆU:
- Mọi con số PHẢI từ kết quả tool (kg, VNĐ, VNĐ/kg).
- Không bịa giá hay tồn kho. Thiếu dữ liệu → nói rõ.

ĐỊNH DẠNG TRẢ LỜI CUỐI (tiếng Việt):
📌 Tóm tắt (2-3 câu)

🔧 Công cụ đã dùng
- Liệt kê tool và mục đích

📊 Phân tích (số liệu cụ thể)

💡 Khuyến nghị hành động

⚠️ Rủi ro & độ tin cậy (Cao / Trung bình / Thấp)
"""

StepCallback = Optional[Callable[[Dict[str, Any]], None]]


class AgriSmartAgent:
    """Agent tác tử với Gemini Function Calling + lịch sử hội thoại."""

    MAX_TOOL_ROUNDS = 8

    def __init__(
        self,
        db: DatabaseManager,
        user_id: str,
        on_step: StepCallback = None,
    ):
        self.db = db
        self.user_id = user_id
        self.on_step = on_step
        self.steps: List[Dict[str, Any]] = []
        self.toolkit = AgriAgentToolkit(db, user_id, on_step=self._tool_step)
        self._chat = None
        self._model = None
        self._history_messages: List[str] = []

    def _record(self, step_type: str, message: str, **extra):
        entry = {
            "type": step_type,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            **extra,
        }
        self.steps.append(entry)
        if self.on_step:
            self.on_step(entry)

    def _tool_step(self, data: dict):
        self.steps.append(data)
        if self.on_step:
            self.on_step(data)

    def _ensure_model(self) -> bool:
        if not GeminiConfig().configured:
            return False
        if self._model is not None:
            return True
        config = GeminiConfig()
        model_id = config.resolve_model_id()
        try:
            self._model = genai.GenerativeModel(
                model_id,
                tools=self.toolkit.get_callables(),
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config=GeminiConfig.ADVISOR_CONFIG,
            )
            logger.info("AgriSmartAgent model: %s", model_id)
            return True
        except Exception as e:
            logger.error("Không khởi tạo agent model: %s", e)
            return False

    def _get_chat(self):
        if self._chat is None:
            self._chat = self._model.start_chat(
                enable_automatic_function_calling=True,
            )
        return self._chat

    def clear_session(self):
        self._chat = None
        self.steps.clear()
        self._history_messages.clear()

    def run(self, question: str) -> Dict[str, Any]:
        """
        Chạy agent xử lý một câu hỏi.

        Returns:
            success, response, steps, tools_used, model_used, error
        """
        self.steps = []
        result = {
            "success": False,
            "response": "",
            "steps": self.steps,
            "tools_used": [],
            "model_used": None,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        if not self._ensure_model():
            result["error"] = "Chưa cấu hình GEMINI_API_KEY"
            return result

        result["model_used"] = getattr(GeminiConfig(), "_active_model_id", None)

        self._record("perceive", f"Nhận câu hỏi: {question[:120]}")
        self._record("plan", "Lập kế hoạch: chọn tools → thu thập dữ liệu → tổng hợp")

        try:
            chat = self._get_chat()
            self._record("act", "Gửi yêu cầu tới Gemini Agent (function calling)...")

            response = chat.send_message(question)
            tools_used = self._collect_tools_from_steps()

            # Vòng bổ sung nếu AFC không xử lết hết (manual fallback)
            rounds = 0
            while rounds < self.MAX_TOOL_ROUNDS:
                fcalls = self._extract_function_calls(response)
                if not fcalls:
                    break
                rounds += 1
                self._record("act", f"Vòng tool #{rounds}: {len(fcalls)} lệnh gọi")
                fr_parts = []
                for fc in fcalls:
                    name = fc.name
                    args = dict(fc.args) if fc.args else {}
                    tools_used.append(name)
                    out = self.toolkit.execute(name, args)
                    fr_parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=name,
                                response={"result": out},
                            )
                        )
                    )
                response = chat.send_message(
                    genai.protos.Content(role="user", parts=fr_parts)
                )

            text = GeminiAgent._extract_response_text(response)
            self._record("reflect", "Hoàn tất tổng hợp câu trả lời")

            result["success"] = True
            result["response"] = text
            result["tools_used"] = list(dict.fromkeys(tools_used))

        except Exception as e:
            logger.exception("AgriSmartAgent.run failed")
            result["error"] = str(e)
            err_lower = str(e).lower()
            if "api key" in err_lower:
                result["error"] = "API Key không hợp lệ"
            elif "quota" in err_lower:
                result["error"] = "Vượt quota API Gemini"

        result["steps"] = self.steps
        return result

    def _extract_function_calls(self, response) -> list:
        try:
            if not response.candidates:
                return []
            parts = response.candidates[0].content.parts
            return [p.function_call for p in parts if p and getattr(p, "function_call", None)]
        except Exception:
            return []

    def _collect_tools_from_steps(self) -> List[str]:
        return [
            s.get("tool", "")
            for s in self.steps
            if s.get("type") == "tool" and s.get("tool")
        ]


def create_agri_agent(
    db: DatabaseManager,
    user_id: str,
    on_step: StepCallback = None,
) -> AgriSmartAgent:
    """Factory tạo agent theo phiên đăng nhập."""
    return AgriSmartAgent(db, user_id, on_step=on_step)
