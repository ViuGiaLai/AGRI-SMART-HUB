# -*- coding: utf-8 -*-
"""
AgriSmartAgent — Agentic AI cho GASH (Gia Lai Agri-Smart Hub).

Kiến trúc ReAct + Function Calling (Gemini):
  Perceive (câu hỏi) → Plan → Act (gọi tools) → Observe (kết quả) → Reflect → Trả lời

Mỗi bước được ghi vào `steps` để hiển thị minh bạch trên UI (phục vụ demo NCKH).
"""
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.ai_engine import GeminiConfig
from core.agent.tools import AgriAgentToolkit
from database.db_manager import DatabaseManager
from core.llm_provider import get_llm_router, LLMMessage, _is_rate_limit_error

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Bạn là AgriSmart Agent — trợ lý AI cho đại lý thu mua nông sản tại Gia Lai, Việt Nam.

NGUYÊN TẮC #1 — TRẢ LỜI ĐÚNG TRỌNG TÂM:
- Chỉ trả lời ĐÚNG những gì người dùng hỏi, không thêm phân tích hay khuyến nghị nếu họ không yêu cầu.
- Nếu hỏi "tồn kho bao nhiêu" → chỉ đưa số kg. Nếu hỏi "giá bao nhiêu" → chỉ đưa số tiền + nguồn.
- Chỉ đưa công cụ đã dùng nếu người dùng hỏi về quy trình. Mặc định: im lặng về tools.
- Giữ câu trả lời ngắn nhất có thể. Văn phong: lịch sự, chuyên nghiệp, đi thẳng vào vấn đề.

NGUYÊN TẮC #2 — PHÂN BIỆT CHẤT LƯỢNG NGUỒN:
Luôn gắn nhãn độ tin cậy cho mỗi số liệu thị trường. Phân loại:
  ✅ CAO: thoibaotaichinhvietnam.vn (Thời báo Tài chính VN — báo nhà nước, chính xác nhất)
  ⚠️ TRUNG BÌNH: nongdanviet.vn, congthuong.vn, asemconnectvietnam.gov.vn
  ❌ THẤP: giacaphe.com (có thể sai lệch, VD: giá cà phê hiện ~86.000-87.000 nhưng site này từng hiện ~20.000)
Nếu nguồn có độ tin cậy THẤP hoặc TRUNG BÌNH, hãy nói rõ ví dụ:
  "Giá cà phê 20.000 VNĐ/kg (⚠️ nguồn giacaphe.com — có thể sai lệch, không khớp thị trường thực tế)"

NGUYÊN TẮC #3 — CHỈ GỌI TOOL CẦN THIẾT:
- Chỉ gọi tool cần thiết để trả lời câu hỏi — không gọi tool dư thừa.
- Dùng đúng tool: research_market_news() cho giá thị trường, get_inventory() cho tồn kho.
- Nếu câu hỏi chỉ cần 1 tool → chỉ gọi 1 tool, không kéo thêm tool khác.
- Không tự ý suy luận số liệu — phải có kết quả từ tool.

VÍ DỤ TRẢ LỜI TỐT:
Q: "Tồn kho cà phê bao nhiêu?"
A: "Tồn kho cà phê hiện tại: 1.250 kg."

Q: "Giá cà phê hôm nay?"
A: "Giá cà phê tại Gia Lai ngày 03/06: 86.700 VNĐ/kg (✅ nguồn: thoibaotaichinhvietnam.vn)."

Q: "Phân tích thị trường giúp tôi"
A: (Lúc này mới đưa phân tích chi tiết + khuyến nghị)
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
        """Kiểm tra có ít nhất 1 LLM provider khả dụng."""
        router = get_llm_router()
        if router.all_configured:
            logger.info("✅ LLM providers sẵn sàng: %s", ", ".join(router.available_providers))
            return True
        logger.warning("❌ Không có LLM provider nào được cấu hình")
        return False

    def _get_chat(self):
        # Không cần chat session cũ — mỗi request tạo mới qua router
        return None

    def clear_session(self):
        self.steps.clear()
        self._history_messages.clear()

    def run(self, question: str) -> Dict[str, Any]:
        """
        Chạy agent xử lý một câu hỏi với auto-fallback giữa các provider.

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

        router = get_llm_router()
        if not router.all_configured:
            result["error"] = "Chưa cấu hình API key cho bất kỳ LLM provider nào. Vào Settings → AI & API để thêm."
            return result

        result["model_used"] = router.active_provider_name

        self._record("perceive", f"Nhận câu hỏi: {question[:120]}")
        self._record("plan", "Lập kế hoạch: chọn tools → thu thập dữ liệu → tổng hợp")

        # Xây dựng messages
        messages = [
            LLMMessage(role="system", content=SYSTEM_INSTRUCTION),
            LLMMessage(role="user", content=question),
        ]

        tools_used = []
        rounds = 0
        last_response = None

        try:
            while rounds <= self.MAX_TOOL_ROUNDS:
                rounds += 1
                self._record("act", f"Gửi yêu cầu tới LLM (vòng {rounds}, provider: {router.active_provider_name})...")

                # Gọi LLM với auto-fallback
                llm_response = router.chat_completion(
                    messages=messages,
                    tools=self.toolkit.get_callables(),
                    temperature=GeminiConfig.ADVISOR_CONFIG.get("temperature", 0.35),
                    max_tokens=GeminiConfig.ADVISOR_CONFIG.get("max_output_tokens", 4096),
                )

                last_response = llm_response

                if not llm_response.success:
                    # Fallback đã tự động xử lý bởi router
                    if llm_response.error and "rate limit" in llm_response.error.lower():
                        result["error"] = "Tất cả LLM providers đều bị rate limit. Vui lòng đợi và thử lại sau."
                    elif llm_response.error and "api key" in llm_response.error.lower():
                        result["error"] = "API Key không hợp lệ cho tất cả providers đã cấu hình. Kiểm tra trong Settings."
                    else:
                        result["error"] = f"LLM error: {llm_response.error}"
                    return result

                # Cập nhật model_used
                if llm_response.provider:
                    result["model_used"] = f"{llm_response.provider}/{llm_response.model_used}"

                # Kiểm tra tool calls
                tool_calls = llm_response.tool_calls
                if not tool_calls:
                    # Không có tool call → hoàn tất
                    # Thu thập tools đã dùng (từ AFC steps hoặc manual loop)
                    tools_used = self._collect_tools_from_steps()
                    self._record("reflect", "Hoàn tất tổng hợp câu trả lời")
                    result["success"] = True
                    result["response"] = llm_response.content
                    result["tools_used"] = list(dict.fromkeys(tools_used))
                    return result

                # Có tool calls → thực thi
                self._record("act", f"🔧 Thực thi {len(tool_calls)} tool(s)...")

                # Thêm assistant message với tool calls
                messages.append(LLMMessage(
                    role="assistant",
                    content=llm_response.content or "",
                    tool_calls=tool_calls,
                ))

                for tc in tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    tc_id = tc.get("id", "")

                    tools_used.append(name)
                    result["tools_used"].append(name)

                    try:
                        out = self.toolkit.execute(name, args)
                    except Exception as tool_err:
                        out = {"error": str(tool_err)}

                    # Tool result message (toolkit._emit() đã ghi step riêng)
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps(out, ensure_ascii=False) if isinstance(out, dict) else str(out),
                        tool_call_id=tc_id or name,
                    ))

            # Hết vòng lặp MAX_TOOL_ROUNDS
            result["error"] = f"Vượt quá số vòng tool tối đa ({self.MAX_TOOL_ROUNDS})"

        except Exception as e:
            logger.exception("AgriSmartAgent.run failed")
            err_str = str(e)
            result["error"] = err_str
            if _is_rate_limit_error(e):
                result["error"] = "Rate limit exceeded trên tất cả providers. Vui lòng đợi và thử lại."
            elif "api key" in err_str.lower():   
                result["error"] = "API Key không hợp lệ. Kiểm tra trong Settings → AI & API."

        result["steps"] = self.steps
        result["tools_used"] = list(dict.fromkeys(tools_used))
        return result

    def _extract_function_calls(self, response) -> list:
        # Không cần dùng nữa — xử lý qua LLMResponse.tool_calls
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
