import os
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tải cấu hình
load_dotenv()

class GeminiConfig:
    """Lớp cấu hình cho Gemini API"""

    # Alias → model ID (cập nhật 2026 — gemini-1.5-* đã ngừng trên v1beta)
    MODELS = {
        "flash": "gemini-2.5-flash",
        "pro": "gemini-2.5-pro",
        "flash_lite": "gemini-2.0-flash-lite",
        "flash_latest": "gemini-flash-latest",
        "pro_latest": "gemini-pro-latest",
        # alias cũ (tương thích .env / tài liệu cũ)
        "flash_8b": "gemini-2.0-flash-lite",
        "pro_002": "gemini-2.5-pro",
    }

    # Thử lần lượt nếu model chính trả 404
    FALLBACK_MODEL_IDS = (
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    )

    # Model 1.5 đã gỡ khỏi API v1beta (2025+)
    DEPRECATED_MODEL_MAP = {
        "gemini-1.5-flash": "gemini-2.5-flash",
        "gemini-1.5-flash-8b": "gemini-2.0-flash-lite",
        "gemini-1.5-pro": "gemini-2.5-pro",
        "gemini-1.5-pro-002": "gemini-2.5-pro",
    }
    
    # Cấu hình mặc định
    DEFAULT_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }

    ADVISOR_CONFIG = {
        "temperature": 0.35,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 4096,
    }
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model_name = os.environ.get("GEMINI_MODEL", "flash")
        self.configured = False
        
        if self.api_key:
            self._configure_api()
        else:
            logger.warning("GEMINI_API_KEY chưa được cấu hình trong file .env")
    
    def _configure_api(self):
        """Cấu hình Gemini API"""
        try:
            genai.configure(api_key=self.api_key)
            self.configured = True
            logger.info("Gemini API đã được cấu hình thành công")
        except Exception as e:
            logger.error(f"Lỗi cấu hình Gemini API: {e}")
            self.configured = False
    
    def resolve_model_id(self, model_type: Optional[str] = None) -> str:
        """Chuyển alias / tên đầy đủ thành model ID."""
        key = (model_type or self.model_name or "flash").strip()
        if key.startswith("models/"):
            key = key[7:]
        if key in self.MODELS:
            return self.MODELS[key]
        # Cho phép GEMINI_MODEL=gemini-2.5-flash trực tiếp
        if key in self.DEPRECATED_MODEL_MAP:
            mapped = self.DEPRECATED_MODEL_MAP[key]
            logger.info("Model cũ '%s' → '%s'", key, mapped)
            return mapped
        if key.startswith("gemini-") or key.startswith("gemma-"):
            return key
        return self.MODELS["flash"]

    def get_model(
        self,
        model_type: Optional[str] = None,
        generation_config: Optional[Dict] = None,
    ) -> Optional[genai.GenerativeModel]:
        """Lấy model Gemini với cấu hình; thử fallback nếu model không tồn tại."""
        if not self.configured:
            return None

        gen_cfg = generation_config or self.DEFAULT_CONFIG
        primary = self.resolve_model_id(model_type)
        candidates = [primary]
        for mid in self.FALLBACK_MODEL_IDS:
            if mid not in candidates:
                candidates.append(mid)

        last_error = None
        for model_id in candidates:
            try:
                model = genai.GenerativeModel(
                    model_id,
                    generation_config=gen_cfg,
                )
                if model_id != primary:
                    logger.warning(
                        "Model '%s' không khả dụng, dùng fallback: %s",
                        primary, model_id,
                    )
                else:
                    logger.info("Đã khởi tạo model: %s", model_id)
                self._active_model_id = model_id
                return model
            except Exception as e:
                last_error = e
                logger.debug("Không khởi tạo được %s: %s", model_id, e)

        logger.error("Không khởi tạo được model Gemini: %s", last_error)
        return None

# === LAZY GEMINI CONFIG ===
# Không khởi tạo GeminiConfig ở module level — tránh genai.configure() khi import
gemini_config = None


def get_gemini_config():
    """Lazy singleton GeminiConfig — chỉ khởi tạo khi thực sự cần."""
    global gemini_config
    if gemini_config is None:
        gemini_config = GeminiConfig()
    return gemini_config


# =============================================================================
# MULTI-PROVIDER INTEGRATION
# =============================================================================

def get_provider_names() -> list:
    """Lấy danh sách provider có API key."""
    try:
        from core.llm_provider import get_llm_router
        router = get_llm_router()
        return router.available_providers
    except Exception:
        return []


def ask_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.35,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Hỏi LLM với auto-fallback giữa các provider.
    Tự động thử Gemini → OpenRouter → Groq → DeepSeek → Cloudflare
    khi gặp rate limit.

    Returns:
        Dict với success, response, model_used, provider, error, latency_ms
    """
    from core.llm_provider import get_llm_router, LLMMessage

    router = get_llm_router()
    messages = []
    if system_prompt:
        messages.append(LLMMessage(role="system", content=system_prompt))
    messages.append(LLMMessage(role="user", content=prompt))

    response = router.chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return {
        "success": response.success,
        "response": response.content,
        "model_used": response.model_used,
        "provider": response.provider,
        "error": response.error,
        "latency_ms": response.latency_ms,
        "timestamp": datetime.now().isoformat(),
    }


def refresh_llm_providers():
    """Refresh provider list (gọi sau khi user thay đổi API key)."""
    from core.llm_provider import reset_llm_router
    reset_llm_router()


class GeminiAgent:
    """AI Agent sử dụng Gemini API cho phân tích thị trường"""
    
    def __init__(self):
        self.config = get_gemini_config()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Giới hạn lịch sử hội thoại
    
    def _build_market_analysis_prompt(self, query: str, context: Optional[Dict] = None) -> str:
        """Xây dựng prompt chuyên cho phân tích thị trường nông sản"""
        base_prompt = f"""Bạn là chuyên gia phân tích thị trường nông sản với kiến thức sâu rộng về cà phê, hồ tiêu và các mặt hàng nông nghiệp.

Nhiệm vụ: {query}

Yêu cầu:
1. Phân tích dựa trên dữ liệu thực tế và xu hướng thị trường
2. Đưa ra nhận định khách quan, có căn cứ
3. Nếu có số liệu cụ thể, hãy trích dẫn nguồn (nếu biết)
4. Gợi ý các chiến lược kinh doanh phù hợp
5. Cảnh báo rủi ro nếu có

Định dạng trả lời:
- Sử dụng markdown để định dạng
- Phân chia rõ ràng các phần: Phân tích, Dự báo, Khuyến nghị
- Sử dụng emoji để trực quan hóa (📈, 📉, ⚠️, 💡)

"""
        
        if context:
            context_str = f"\nThông tin bổ sung:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"
            base_prompt += context_str
        
        return base_prompt
    
    def _build_general_prompt(self, prompt: str) -> str:
        """Xây dựng prompt cho câu hỏi thông thường"""
        return f"""Trả lời câu hỏi sau một cách chính xác, chi tiết và hữu ích:

{prompt}

Hãy đảm bảo:
- Thông tin chính xác và cập nhật
- Dễ hiểu, có cấu trúc rõ ràng
- Thêm ví dụ minh họa nếu có thể
"""
    
    def _add_to_history(self, role: str, content: str):
        """Thêm tin nhắn vào lịch sử hội thoại"""
        self.conversation_history.append({"role": role, "content": content})
        # Giới hạn lịch sử
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    @staticmethod
    def _extract_response_text(response) -> str:
        try:
            return (response.text or "").strip()
        except ValueError:
            pass
        parts = []
        for cand in getattr(response, "candidates", []) or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                t = getattr(part, "text", None)
                if t:
                    parts.append(t)
        if parts:
            return "\n".join(parts).strip()
        return "Không nhận được nội dung từ AI. Vui lòng thử lại."

    def _build_advisor_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """Prompt chuyên biệt — bắt buộc trích số từ JSON, không bịa."""
        quality = context.get("chat_luong_du_lieu", {})
        missing = []
        if not quality.get("co_gia_ca_phe") and "cà phê" in question.lower():
            missing.append("giá cà phê 7 ngày")
        if not quality.get("co_gia_tieu") and "tiêu" in question.lower():
            missing.append("giá hồ tiêu 7 ngày")

        missing_note = ""
        if missing:
            missing_note = (
                f"\nTHIẾU DỮ LIỆU: {', '.join(missing)}. "
                "Phải nói rõ 'chưa có dữ liệu giá trong hệ thống' — KHÔNG được đoán giá."
            )

        return f"""Bạn là cố vấn thị trường nông sản cho đại lý thu mua tại Gia Lai (GASH).

QUY TẮC BẮT BUỘC:
1. Mọi con số PHẢI lấy từ JSON bên dưới; ghi rõ đơn vị (kg, VNĐ, VNĐ/kg).
2. KHÔNG gọi kg là "đơn vị" chung chung; KHÔNG bịa doanh thu hay giá.
3. Nếu thiếu dữ liệu giá → nói thẳng, chỉ phân tích tồn kho/giao dịch có sẵn.
4. Hoàn thành ĐỦ 4 mục, không dừng giữa chừng.
5. Mức độ tin cậy: Cao / Trung bình / Thấp (giải thích 1 câu).

ĐỊNH DẠNG TRẢ LỜI (tiếng Việt):
📌 Tóm tắt (2-3 câu)

📊 Số liệu từ hệ thống
- Liệt kê số cụ thể từ JSON (giá, tồn, giao dịch…)

📈 Phân tích xu hướng
- Dựa trên xu_huong / bien_dong_pct nếu có; nếu không có giá → ghi "chưa đủ dữ liệu giá"

💡 Khuyến nghị
- Hành động cụ thể cho đại lý (mua/bán/giữ, thu nợ…)

⚠️ Rủi ro & độ tin cậy
{missing_note}

DỮ LIỆU JSON (nguồn: {context.get('nguon', 'GASH')}, lúc {context.get('thoi_diem', '')}):
{json.dumps(context, ensure_ascii=False, indent=2)}

CÂU HỎI: {question}
"""

    def _get_chat_context(self) -> str:
        """Lấy context từ lịch sử hội thoại"""
        if not self.conversation_history:
            return ""
        
        context = "\nLịch sử hội thoại gần đây:\n"
        for msg in self.conversation_history[-5:]:  # Lấy 5 tin nhắn gần nhất
            role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
            context += f"{role}: {msg['content'][:100]}...\n"
        return context
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def ask_with_retry(self, model, prompt: str, model_type: Optional[str] = None) -> str:
        """Gửi yêu cầu với retry; tự đổi model nếu gặp 404."""
        active = getattr(self.config, "_active_model_id", None)
        tried = {active} if active else set()

        try:
            response = model.generate_content(prompt)
            return GeminiAgent._extract_response_text(response)
        except Exception as e:
            err = str(e)
            if "404" not in err or "not found" not in err.lower():
                logger.error("Lỗi khi gọi Gemini API (attempt): %s", e)
                raise

            for model_id in self.config.FALLBACK_MODEL_IDS:
                if model_id in tried:
                    continue
                tried.add(model_id)
                try:
                    fb = genai.GenerativeModel(
                        model_id,
                        generation_config=self.config.DEFAULT_CONFIG,
                    )
                    response = fb.generate_content(prompt)
                    self.config._active_model_id = model_id
                    logger.warning("Model lỗi 404 — đã chuyển sang: %s", model_id)
                    return GeminiAgent._extract_response_text(response)
                except Exception as fb_err:
                    logger.debug("Fallback %s thất bại: %s", model_id, fb_err)

            logger.error("Lỗi khi gọi Gemini API (attempt): %s", e)
            raise
    
    def ask_gemini(
        self, 
        prompt: str, 
        context: Optional[Dict] = None,
        model_type: Optional[str] = None,
        use_history: bool = False,
        is_market_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Hàm gửi câu hỏi đến Gemini và nhận phản hồi
        
        Args:
            prompt: Câu hỏi hoặc yêu cầu
            context: Ngữ cảnh bổ sung (dict)
            model_type: Loại model ('flash', 'pro', 'flash_8b')
            use_history: Có sử dụng lịch sử hội thoại không
            is_market_analysis: Có phải phân tích thị trường không
        
        Returns:
            Dict chứa kết quả và metadata
        """
        result = {
            "success": False,
            "response": "",
            "error": None,
            "model_used": None,
            "timestamp": datetime.now().isoformat(),
            "tokens_used": None
        }
        
        # Kiểm tra cấu hình
        if not self.config.configured:
            result["error"] = "Chưa cấu hình GEMINI_API_KEY trong file .env"
            logger.error(result["error"])
            return result
        
        # Lấy model
        model = self.config.get_model(model_type)
        if not model:
            result["error"] = "Không thể khởi tạo model Gemini"
            return result
        
        result["model_used"] = getattr(
            self.config, "_active_model_id", None
        ) or self.config.resolve_model_id(model_type)
        
        # Xây dựng prompt hoàn chỉnh
        if is_market_analysis:
            final_prompt = self._build_market_analysis_prompt(prompt, context)
        else:
            final_prompt = self._build_general_prompt(prompt)
        
        # Thêm lịch sử hội thoại nếu cần
        if use_history:
            history_context = self._get_chat_context()
            if history_context:
                final_prompt = history_context + "\n" + final_prompt
        
        # Thêm vào lịch sử (câu hỏi của user)
        if use_history:
            self._add_to_history("user", prompt)
        
        try:
            # Gọi API với retry mechanism
            response_text = self.ask_with_retry(model, final_prompt, model_type)
            
            result["success"] = True
            result["response"] = response_text
            
            # Thêm phản hồi vào lịch sử
            if use_history:
                self._add_to_history("assistant", response_text)
            
            logger.info(f"Gemini response successful - Model: {result['model_used']}")
            
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"Lỗi khi gọi Gemini API: {error_msg}")
            
            # Xử lý các lỗi đặc biệt
            if "API key not valid" in error_msg:
                result["error"] = "API Key không hợp lệ. Vui lòng kiểm tra lại."
            elif "404" in error_msg and "not found" in error_msg.lower():
                result["error"] = (
                    "Model Gemini không còn hỗ trợ. Đặt GEMINI_MODEL=flash trong .env "
                    "(dùng gemini-2.5-flash) và khởi động lại ứng dụng."
                )
            elif "quota" in error_msg.lower():
                result["error"] = "Đã vượt quá giới hạn sử dụng API. Vui lòng thử lại sau."
            elif "safety" in error_msg.lower():
                result["error"] = "Nội dung bị chặn do vi phạm chính sách bảo mật."
        
        return result

    def ask_advisor(
        self,
        question: str,
        context: Dict[str, Any],
        model_type: Optional[str] = None,
        use_history: bool = True,
    ) -> Dict[str, Any]:
        """Hỏi AI Advisor với ngữ cảnh có cấu trúc — không bọc prompt kép."""
        result = {
            "success": False,
            "response": "",
            "error": None,
            "model_used": None,
            "timestamp": datetime.now().isoformat(),
        }
        if not self.config.configured:
            result["error"] = "Chưa cấu hình GEMINI_API_KEY"
            return result

        model = self.config.get_model(
            model_type, generation_config=GeminiConfig.ADVISOR_CONFIG,
        )
        if not model:
            result["error"] = "Không thể khởi tạo model Gemini"
            return result

        result["model_used"] = getattr(self.config, "_active_model_id", None)
        final_prompt = self._build_advisor_prompt(question, context)

        if use_history:
            history_context = self._get_chat_context()
            if history_context:
                final_prompt = history_context + "\n" + final_prompt
            self._add_to_history("user", question)

        try:
            text = self.ask_with_retry(model, final_prompt, model_type)
            result["success"] = True
            result["response"] = text
            if use_history:
                self._add_to_history("assistant", text)
        except Exception as e:
            result["error"] = str(e)

        return result
    
    def analyze_market_price(
        self, 
        product: str, 
        region: str = "Việt Nam",
        additional_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """Phân tích giá thị trường cho sản phẩm cụ thể"""
        prompt = f"""Phân tích giá {product} tại khu vực {region} trong thời gian gần đây.
        
Yêu cầu phân tích:
1. Xu hướng giá hiện tại (tăng/giảm/ổn định)
2. Các yếu tố ảnh hưởng đến giá
3. Dự báo giá trong 1-3 tháng tới
4. Khuyến nghị cho người mua/bán
"""
        if additional_info:
            prompt += f"\nThông tin bổ sung: {additional_info}"
        
        return self.ask_gemini(prompt, is_market_analysis=True)
    
    def compare_products(
        self, 
        products: List[str], 
        aspects: List[str] = ["giá", "chất lượng", "thị trường"]
    ) -> Dict[str, Any]:
        """So sánh các sản phẩm nông sản"""
        prompt = f"""So sánh các sản phẩm sau: {', '.join(products)}
        
Các khía cạnh cần so sánh: {', '.join(aspects)}

Đưa ra bảng so sánh chi tiết và kết luận."""
        
        return self.ask_gemini(prompt, is_market_analysis=True)
    
    def clear_history(self):
        """Xóa lịch sử hội thoại"""
        self.conversation_history.clear()
        logger.info("Đã xóa lịch sử hội thoại")
    
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê sử dụng"""
        return {
            "configured": self.config.configured,
            "model": self.config.model_name,
            "history_length": len(self.conversation_history),
            "max_history": self.max_history
        }

# Singleton instance
_gemini_agent = None

def get_gemini_agent() -> GeminiAgent:
    """Lấy instance của GeminiAgent (Singleton)"""
    global _gemini_agent
    if _gemini_agent is None:
        _gemini_agent = GeminiAgent()
    return _gemini_agent

# Hàm tương thích ngược với code cũ
def ask_gemini(prompt: str) -> str:
    """
    Hàm gửi câu hỏi đến Gemini và nhận phản hồi (Tương thích ngược)
    """
    agent = get_gemini_agent()
    result = agent.ask_gemini(prompt, is_market_analysis=False)
    
    if result["success"]:
        return result["response"]
    else:
        return f"Lỗi: {result['error']}"

# Các hàm mở rộng
def ask_market_analysis(prompt: str, context: Optional[Dict] = None) -> str:
    """Hàm chuyên cho phân tích thị trường"""
    agent = get_gemini_agent()
    result = agent.ask_gemini(prompt, context, is_market_analysis=True)
    return result["response"] if result["success"] else f"Lỗi: {result['error']}"

def analyze_price(product: str, region: str = "Việt Nam") -> str:
    """Phân tích giá sản phẩm"""
    agent = get_gemini_agent()
    result = agent.analyze_market_price(product, region)
    return result["response"] if result["success"] else f"Lỗi: {result['error']}"

# Ví dụ sử dụng
if __name__ == "__main__":
    # Kiểm tra cấu hình
    agent = get_gemini_agent()
    print(f"Trạng thái: {agent.get_stats()}")
    
    # Test câu hỏi đơn giản
    response = ask_gemini("Chào bạn, bạn có thể làm gì?")
    print(f"Response: {response[:200]}...")
    
    # Test phân tích thị trường
    price_analysis = analyze_price("cà phê", "Tây Nguyên")
    print(f"\nPhân tích giá: {price_analysis[:300]}...")