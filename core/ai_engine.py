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
    
    # Các model có sẵn
    MODELS = {
        "flash": "gemini-1.5-flash",
        "pro": "gemini-1.5-pro",
        "flash_8b": "gemini-1.5-flash-8b",
        "pro_002": "gemini-1.5-pro-002"
    }
    
    # Cấu hình mặc định
    DEFAULT_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
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
    
    def get_model(self, model_type: Optional[str] = None) -> Optional[genai.GenerativeModel]:
        """Lấy model Gemini với cấu hình"""
        if not self.configured:
            return None
        
        model_key = model_type or self.model_name
        model_id = self.MODELS.get(model_key, self.MODELS["flash"])
        
        try:
            model = genai.GenerativeModel(
                model_id,
                generation_config=self.DEFAULT_CONFIG
            )
            logger.info(f"Đã khởi tạo model: {model_id}")
            return model
        except Exception as e:
            logger.error(f"Lỗi khởi tạo model {model_id}: {e}")
            return None

# Khởi tạo cấu hình toàn cục
gemini_config = GeminiConfig()

class GeminiAgent:
    """AI Agent sử dụng Gemini API cho phân tích thị trường"""
    
    def __init__(self):
        self.config = gemini_config
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
    def ask_with_retry(self, model, prompt: str) -> str:
        """Gửi yêu cầu với cơ chế retry khi lỗi"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini API (attempt): {e}")
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
        
        result["model_used"] = model_type or self.config.model_name
        
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
            response_text = self.ask_with_retry(model, final_prompt)
            
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
            elif "quota" in error_msg.lower():
                result["error"] = "Đã vượt quá giới hạn sử dụng API. Vui lòng thử lại sau."
            elif "safety" in error_msg.lower():
                result["error"] = "Nội dung bị chặn do vi phạm chính sách bảo mật."
        
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