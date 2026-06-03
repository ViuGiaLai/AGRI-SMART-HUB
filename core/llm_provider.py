# -*- coding: utf-8 -*-
"""
core/llm_provider.py — Unified LLM Provider abstraction.

Hỗ trợ nhiều provider với auto-fallback khi gặp rate limit / quota exhausted.

Các provider hiện tại:
  - Gemini (google-generativeai SDK)
  - OpenRouter (OpenAI-compatible)
  - Groq (OpenAI-compatible)
  - DeepSeek (OpenAI-compatible)
  - Cloudflare Workers AI (REST API)

Cấu hình qua .env:
  LLM_PRIMARY_PROVIDER=gemini        # Provider ưu tiên
  LLM_FALLBACK_ORDER=openrouter,groq # Fallback chain
  GEMINI_API_KEY=...
  OPENROUTER_API_KEY=...
  GROQ_API_KEY=...
  DEEPSEEK_API_KEY=...
  CLOUDFLARE_API_TOKEN=...
  CLOUDFLARE_ACCOUNT_ID=...
"""
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


# =============================================================================
# Data models
# =============================================================================

@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: Optional[List[Dict]] = None
    model_used: str = ""
    provider: str = ""
    success: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class ProviderConfig:
    """Cấu hình một provider."""
    name: str
    api_key_env: str
    model_env: str
    default_model: str
    base_url: Optional[str] = None
    priority: int = 10  # Thấp hơn = ưu tiên cao hơn
    enabled: bool = True


# =============================================================================
# Rate-limit detection helpers
# =============================================================================

def _is_rate_limit_error(error: Exception) -> bool:
    """Kiểm tra xem lỗi có phải rate limit / quota exhausted không."""
    err_str = str(error).lower()
    triggers = [
        "429", "rate limit", "rate_limit", "quota", "resource exhausted",
        "too many requests", "retry_delay", "retry in", "please retry in",
        "insufficient_quota", "free tier", "generate_content_free_tier",
        "daily limit", "token limit",
    ]
    return any(t in err_str for t in triggers)


# =============================================================================
# Base provider
# =============================================================================

class BaseLLMProvider(ABC):
    """Base class cho tất cả LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._last_error: Optional[str] = None
        self._cooldown_until: float = 0  # Cooldown timestamp

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_available(self) -> bool:
        """Kiểm tra provider có sẵn sàng (API key + không trong cooldown)."""
        if time.time() < self._cooldown_until:
            return False
        return bool(os.environ.get(self.config.api_key_env))

    def mark_cooldown(self, seconds: int = 60):
        """Đánh dấu provider cần cooldown sau khi lỗi."""
        self._cooldown_until = time.time() + seconds
        logger.warning("⚠️ %s: cooldown %ds after error", self.name, seconds)

    def get_model_name(self, model_override: Optional[str] = None) -> str:
        return model_override or os.environ.get(self.config.model_env) or self.config.default_model

    @abstractmethod
    def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Callable]] = None,
        model: Optional[str] = None,
        temperature: float = 0.35,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Gửi chat completion request."""
        ...


# =============================================================================
# Gemini provider
# =============================================================================

class GeminiProvider(BaseLLMProvider):
    """Provider cho Google Gemini API (google-generativeai SDK).

    Dùng Automatic Function Calling (AFC) khi có tools — Gemini tự xử lý tool loop.
    """

    def __init__(self):
        super().__init__(ProviderConfig(
            name="gemini",
            api_key_env="GEMINI_API_KEY",
            model_env="GEMINI_MODEL",
            default_model="gemini-2.5-flash",
            priority=1,
        ))
        self._model_instance = None
        self._model_id: Optional[str] = None

    def _resolve_gemini_model(self, model: Optional[str] = None) -> str:
        """
        Resolve model alias → full model ID, tái sử dụng logic từ GeminiConfig.
        Ví dụ: 'flash' → 'gemini-2.5-flash', 'pro' → 'gemini-2.5-pro'
        """
        raw = self.get_model_name(model)
        try:
            from core.ai_engine import GeminiConfig
            return GeminiConfig().resolve_model_id(raw)
        except Exception:
            alias_map = {
                "flash": "gemini-2.5-flash",
                "pro": "gemini-2.5-pro",
                "flash_lite": "gemini-2.0-flash-lite",
            }
            return alias_map.get(raw, raw)

    def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Callable]] = None,
        model: Optional[str] = None,
        temperature: float = 0.35,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        start = time.time()
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get(self.config.api_key_env))

            model_id = self._resolve_gemini_model(model)
            gen_cfg = {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }

            # Tách system prompt và user content
            system_parts = []
            user_contents = []
            for m in messages:
                if m.role == "system":
                    system_parts.append(m.content)
                elif m.role == "user" and m.content:
                    user_contents.append(m.content)

            system_text = "\n".join(system_parts).strip()

            model_instance = genai.GenerativeModel(
                model_id,
                tools=tools or None,
                system_instruction=system_text or None,
                generation_config=gen_cfg,
            )
            self._model_id = model_id
            self._model_instance = model_instance

            # Nếu có tools → dùng AFC (Gemini tự xử lý tool loop)
            if tools:
                chat = model_instance.start_chat(
                    enable_automatic_function_calling=True,
                )
                # Gửi user message cuối cùng (hoặc tất cả user messages)
                user_text = user_contents[-1] if user_contents else "Hello"
                if not user_text.strip():
                    user_text = "Hello"
                response = chat.send_message(user_text)
            else:
                # Không có tools → gửi trực tiếp, lưu response cuối
                chat = model_instance.start_chat(enable_automatic_function_calling=False)
                last_response = None
                for text in user_contents:
                    if text.strip():
                        last_response = chat.send_message(text)
                response = last_response or model_instance.generate_content("Hello")

            # Xử lý response
            try:
                text = response.text or ""
            except (ValueError, AttributeError):
                text = ""

            # Kiểm tra function calls từ AFC
            tool_calls = []
            try:
                for cand in (response.candidates or []):
                    for part in (cand.content.parts or []):
                        fc = getattr(part, "function_call", None)
                        if fc:
                            tool_calls.append({
                                "name": fc.name,
                                "args": dict(fc.args) if fc.args else {},
                            })
            except Exception:
                pass

            elapsed = (time.time() - start) * 1000
            return LLMResponse(
                content=text,
                tool_calls=tool_calls if tool_calls else None,
                model_used=model_id,
                provider="gemini",
                success=True,
                latency_ms=round(elapsed, 1),
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            err_str = str(e)
            if _is_rate_limit_error(e):
                self.mark_cooldown(120)
                logger.warning("⚠️ Gemini rate limited: %s", err_str[:120])
            return LLMResponse(
                error=err_str,
                model_used=self.get_model_name(model),
                provider="gemini",
                success=False,
                latency_ms=round(elapsed, 1),
            )


# =============================================================================
# OpenAI-compatible provider (OpenRouter, Groq, DeepSeek)
# =============================================================================

class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider dùng OpenAI-compatible API (OpenRouter, Groq, DeepSeek)."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def _get_client(self):
        """Lazy init OpenAI client với base_url phù hợp."""
        from openai import OpenAI
        return OpenAI(
            api_key=os.environ.get(self.config.api_key_env),
            base_url=self.config.base_url,
        )

    def _convert_to_openai_messages(self, messages: List[LLMMessage]) -> List[Dict]:
        """Chuyển LLMMessage sang OpenAI message format."""
        result = []
        for m in messages:
            entry = {"role": m.role, "content": m.content}
            if m.tool_calls:
                entry["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id
            result.append(entry)
        return result

    def _convert_to_openai_tools(self, tools: Optional[List[Callable]]) -> Optional[List[Dict]]:
        """Chuyển Python functions sang OpenAI tools format."""
        if not tools:
            return None
        openai_tools = []
        for fn in tools:
            try:
                import inspect
                sig = inspect.signature(fn)
                parameters = {"type": "object", "properties": {}, "required": []}
                for name, param in sig.parameters.items():
                    param_type = "string"
                    if param.annotation is not inspect.Parameter.empty:
                        a = str(param.annotation)
                        if "int" in a:
                            param_type = "integer"
                        elif "float" in a:
                            param_type = "number"
                        elif "bool" in a:
                            param_type = "boolean"
                    parameters["properties"][name] = {"type": param_type, "description": ""}
                    if param.default is inspect.Parameter.empty:
                        parameters["required"].append(name)

                # Lấy docstring làm description
                desc = (fn.__doc__ or "").strip().split("\n")[0]

                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": fn.__name__,
                        "description": desc,
                        "parameters": parameters,
                    },
                })
            except Exception as e:
                logger.debug("Skip tool %s: %s", fn.__name__, e)
        return openai_tools if openai_tools else None

    def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Callable]] = None,
        model: Optional[str] = None,
        temperature: float = 0.35,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        start = time.time()
        try:
            client = self._get_client()
            model_id = self.get_model_name(model)
            openai_messages = self._convert_to_openai_messages(messages)
            openai_tools = self._convert_to_openai_tools(tools)

            kwargs = {
                "model": model_id,
                "messages": openai_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message

            content = msg.content or ""
            tool_calls = None
            if msg.tool_calls:
                tool_calls = []
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": args,
                    })

            elapsed = (time.time() - start) * 1000
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                model_used=f"{self.name}/{model_id}",
                provider=self.name,
                success=True,
                latency_ms=round(elapsed, 1),
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            err_str = str(e)
            if _is_rate_limit_error(e):
                self.mark_cooldown(60)
                logger.warning("⚠️ %s rate limited: %s", self.name, err_str[:120])
            return LLMResponse(
                error=err_str,
                model_used=self.get_model_name(model),
                provider=self.name,
                success=False,
                latency_ms=round(elapsed, 1),
            )


# =============================================================================
# Cloudflare Workers AI provider
# =============================================================================

class CloudflareProvider(BaseLLMProvider):
    """Provider cho Cloudflare Workers AI (REST API)."""

    def __init__(self):
        super().__init__(ProviderConfig(
            name="cloudflare",
            api_key_env="CLOUDFLARE_API_TOKEN",
            model_env="CLOUDFLARE_MODEL",
            default_model="@cf/meta/llama-3.1-8b-instruct",
            priority=50,
        ))
        self._account_id: Optional[str] = None

    def _get_account_id(self) -> Optional[str]:
        if not self._account_id:
            self._account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        return self._account_id

    def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Callable]] = None,
        model: Optional[str] = None,
        temperature: float = 0.35,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        start = time.time()
        account_id = self._get_account_id()
        if not account_id:
            return LLMResponse(error="CLOUDFLARE_ACCOUNT_ID not set", provider="cloudflare", success=False)

        try:
            import requests
            model_id = self.get_model_name(model)
            api_token = os.environ.get(self.config.api_key_env)
            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_id}"

            cf_messages = [{"role": m.role, "content": m.content} for m in messages]

            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
                json={"messages": cf_messages, "max_tokens": max_tokens, "temperature": temperature},
                timeout=60,
            )
            data = response.json()

            elapsed = (time.time() - start) * 1000

            if not data.get("success"):
                err = str(data.get("errors", "Unknown error"))
                if _is_rate_limit_error(Exception(err)):
                    self.mark_cooldown(60)
                return LLMResponse(error=err, model_used=model_id, provider="cloudflare", success=False, latency_ms=round(elapsed, 1))

            result = data.get("result", {})
            content = result.get("response", "")

            return LLMResponse(
                content=content,
                model_used=model_id,
                provider="cloudflare",
                success=True,
                latency_ms=round(elapsed, 1),
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            if _is_rate_limit_error(e):
                self.mark_cooldown(60)
            return LLMResponse(error=str(e), provider="cloudflare", success=False, latency_ms=round(elapsed, 1))


# =============================================================================
# Provider Router (Fallback Chain)
# =============================================================================

class LLMRouter:
    """Router quản lý nhiều provider và tự động fallback khi rate limit."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._fallback_order: List[str] = []
        self._active_provider: Optional[str] = None
        self._setup_providers()

    def _setup_providers(self):
        """Khởi tạo các provider dựa trên .env config."""
        # Luôn tạo Gemini
        gemini = GeminiProvider()
        self._providers["gemini"] = gemini

        # OpenAI-compatible providers
        provider_configs = [
            ProviderConfig("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_MODEL",
                          "deepseek/deepseek-chat", "https://openrouter.ai/api/v1", priority=10),
            ProviderConfig("groq", "GROQ_API_KEY", "GROQ_MODEL",
                          "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1", priority=20),
            ProviderConfig("deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL",
                          "deepseek-chat", "https://api.deepseek.com", priority=30),
        ]

        for cfg in provider_configs:
            self._providers[cfg.name] = OpenAICompatibleProvider(cfg)

        # Cloudflare
        self._providers["cloudflare"] = CloudflareProvider()

        # Xác định fallback order
        primary = os.environ.get("LLM_PRIMARY_PROVIDER", "gemini").lower()
        fallback_str = os.environ.get("LLM_FALLBACK_ORDER", "")

        if fallback_str:
            order = [primary] + [p.strip().lower() for p in fallback_str.split(",") if p.strip()]
        else:
            # Mặc định: gemini → openrouter → groq → deepseek → cloudflare
            default_order = ["gemini", "openrouter", "groq", "deepseek", "cloudflare"]
            order = [primary] + [p for p in default_order if p != primary]

        # Chỉ giữ provider có API key
        self._fallback_order = [p for p in order if p in self._providers and self._providers[p].is_available]

        if self._fallback_order:
            self._active_provider = self._fallback_order[0]
            logger.info("🔀 LLM providers ready: %s (active: %s)",
                       ", ".join(self._fallback_order), self._active_provider)

    def refresh(self):
        """Refresh provider list (gọi lại khi user thay đổi API key trong Settings)."""
        self._setup_providers()

    @property
    def active_provider_name(self) -> str:
        return self._active_provider or "none"

    @property
    def available_providers(self) -> List[str]:
        return list(self._fallback_order)

    @property
    def all_configured(self) -> bool:
        """Có ít nhất 1 provider khả dụng."""
        return len(self._fallback_order) > 0

    def chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Callable]] = None,
        model: Optional[str] = None,
        temperature: float = 0.35,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Gửi request với auto-fallback khi rate limit."""
        if not self._fallback_order:
            return LLMResponse(
                error="Không có LLM provider nào được cấu hình. Thêm API key trong Settings.",
                success=False,
            )

        last_error = None
        attempted = []

        for provider_name in self._fallback_order:
            provider = self._providers.get(provider_name)
            if not provider or not provider.is_available:
                continue

            attempted.append(provider_name)
            logger.info("📡 Trying provider: %s", provider_name)

            try:
                response = provider.chat_completion(
                    messages=messages,
                    tools=tools,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.success:
                    self._active_provider = provider_name
                    if len(attempted) > 1:
                        logger.info("✅ Fallback thành công: %s (sau %s)", provider_name, " → ".join(attempted))
                    return response

                # Không thành công
                last_error = response.error
                if _is_rate_limit_error(Exception(response.error or "")):
                    logger.warning("⚠️ %s rate limited, thử provider tiếp theo...", provider_name)
                    continue
                else:
                    # Lỗi không phải rate limit → thử provider khác
                    if "api key" in (response.error or "").lower() or "auth" in (response.error or "").lower():
                        logger.warning("⚠️ %s auth error, bỏ qua provider này", provider_name)
                        continue
                    # Các lỗi khác (model not found, etc.) cũng thử fallback
                    logger.warning("⚠️ %s error: %s, thử fallback...", provider_name, str(response.error)[:80])
                    continue

            except Exception as e:
                last_error = str(e)
                logger.warning("⚠️ %s exception: %s, thử fallback...", provider_name, str(e)[:80])
                if _is_rate_limit_error(e):
                    continue
                continue

        # Tất cả đều thất bại
        final_error = last_error or "Tất cả LLM providers đều không khả dụng"
        logger.error("❌ All %d providers failed: %s", len(attempted), final_error[:120])
        return LLMResponse(
            error=final_error,
            success=False,
            model_used=",".join(attempted),
        )


# =============================================================================
# Singleton
# =============================================================================

_router_instance: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance


def reset_llm_router():
    """Reset router (khi user thay đổi API key)."""
    global _router_instance
    _router_instance = None
