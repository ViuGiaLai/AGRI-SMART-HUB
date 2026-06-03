# -*- coding: utf-8 -*-
"""
Redis Cache Manager cho GASH — Tối ưu tốc độ, giảm request lặp.

Cấu trúc key:
  gash:{group}:{subgroup}:{key}

Nhóm (group)        | Subgroup (subgroup)  | Ví dụ key
--------------------|---------------------|--------------------------
mp                  | product_name        | gash:mp:ca-phe:today
mp                  | product_name        | gash:mp:ca-phe:7d
inv                 | user_id             | gash:inv:user_abc
stats               | user_id             | gash:stats:user_abc:dashboard
web                 | source              | gash:web:thoibaotaichinh:coffee
web                 | source              | gash:web:nongdanviet:gia-nong-san
session             | user_id             | gash:session:user_abc
pref                | key                 | gash:pref:theme

Xóa theo nhóm: cache.delete_group("mp") → xóa tất cả gash:mp:*
Xóa toàn bộ:   cache.flush() → xóa tất cả gash:*
"""

import inspect
import json
import logging
import os
import threading
import time
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ==================== CẤU HÌNH ====================

# TTL mặc định cho từng nhóm (giây)
DEFAULT_TTL: Dict[str, int] = {
    "mp": 600,       # Giá thị trường: 10 phút
    "inv": 60,       # Tồn kho: 1 phút
    "stats": 30,     # Thống kê dashboard: 30 giây
    "web": 900,      # Kết quả scrape web: 15 phút
    "session": 3600, # Session: 1 giờ
    "pref": 86400,   # Preferences: 1 ngày
    "default": 300,  # Mặc định: 5 phút
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


# ==================== CACHE MANAGER ====================

class CacheManager:
    """
    Quản lý cache Redis với key namespace 'gash:'.
    Graceful fallback: nếu Redis không khả dụng → tự động dùng Dict cache (in-memory).
    """

    def __init__(self, url: str = REDIS_URL):
        self._redis = None
        self._fallback: Dict[str, Any] = {}  # In-memory fallback
        self._fallback_ttl: Dict[str, float] = {}  # TTL tracking
        self._connected = False
        self._connect(url)

    def _connect(self, url: str):
        """Kết nối Redis, fallback về in-memory nếu lỗi."""
        try:
            import redis as redis_lib
            self._redis = redis_lib.from_url(url, decode_responses=True, socket_timeout=2)
            self._redis.ping()
            self._connected = True
            logger.info(f"✅ Redis connected: {url}")
        except Exception as e:
            self._connected = False
            self._redis = None
            logger.warning(f"⚠️ Redis unavailable ({e}) — using in-memory fallback")

    # ──────────────────────────────────────────────
    # KEY MANAGEMENT
    # ──────────────────────────────────────────────

    @staticmethod
    def _make_key(group: str, *parts: str) -> str:
        """Tạo key chuẩn: gash:{group}:{part1}:{part2}..."""
        key = f"gash:{group}"
        for p in parts:
            if p:
                # Chuẩn hóa: lowercase, thay space/dấu bằng -
                clean = p.lower().replace(" ", "-").replace("_", "-")
                clean = clean.replace("đ", "d").replace("à", "a").replace("á", "a")
                clean = clean.replace("ả", "a").replace("ã", "a").replace("ạ", "a")
                clean = clean.replace("è", "e").replace("é", "e").replace("ẻ", "e")
                clean = clean.replace("ẽ", "e").replace("ẹ", "e").replace("ì", "i")
                clean = clean.replace("í", "i").replace("ỉ", "i").replace("ĩ", "i")
                clean = clean.replace("ị", "i").replace("ò", "o").replace("ó", "o")
                clean = clean.replace("ổ", "o").replace("õ", "o").replace("ọ", "o")
                clean = clean.replace("ù", "u").replace("ú", "u").replace("ủ", "u")
                clean = clean.replace("ũ", "u").replace("ụ", "u").replace("ô", "o")
                clean = clean.replace("ơ", "o").replace("ê", "e").replace("ă", "a")
                clean = clean.replace("â", "a")
                key += f":{clean}"
        return key

    @staticmethod
    def _group_pattern(group: str) -> str:
        """Pattern để scan keys theo nhóm: gash:{group}:*"""
        return f"gash:{group}:*"

    @staticmethod
    def _all_pattern() -> str:
        """Pattern để scan tất cả keys GASH: gash:*"""
        return "gash:*"

    # ──────────────────────────────────────────────
    # GET / SET
    # ──────────────────────────────────────────────

    def get(self, group: str, *parts: str) -> Optional[Any]:
        """
        Lấy giá trị từ cache.
        Returns: parsed Python object hoặc None nếu miss.
        """
        key = self._make_key(group, *parts)
        return self._get(key)

    def _get(self, key: str) -> Optional[Any]:
        """Internal get — dùng key đã format."""
        if self._connected and self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"⚠️ Redis get error: {e}")
                self._connected = False

        # Fallback: in-memory
        val = self._fallback.get(key)
        if val is not None:
            expiry = self._fallback_ttl.get(key)
            if expiry and expiry >= time.time():
                return val
            else:
                self._fallback.pop(key, None)
                self._fallback_ttl.pop(key, None)
        return None

    def set(self, group: str, value: Any, *parts: str, ttl: Optional[int] = None):
        """
        Lưu giá trị vào cache.
        
        Args:
            group: Nhóm (mp, inv, stats, web, ...)
            value: Dữ liệu (sẽ JSON serialize)
            *parts: Các thành phần key (product_name, user_id, ...)
            ttl: Time-to-live (giây). None = dùng TTL mặc định của nhóm.
        """
        key = self._make_key(group, *parts)
        ttl = ttl or DEFAULT_TTL.get(group, DEFAULT_TTL["default"])
        return self._set(key, value, ttl)

    def _set(self, key: str, value: Any, ttl: int):
        """Internal set."""
        serialized = json.dumps(value, ensure_ascii=False, default=str)

        if self._connected and self._redis:
            try:
                self._redis.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"⚠️ Redis set error: {e}")
                self._connected = False

        # Fallback: in-memory
        self._fallback[key] = value
        self._fallback_ttl[key] = time.time() + ttl
        return True

    # ──────────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────────

    def delete(self, group: str, *parts: str) -> int:
        """
        Xóa một key cụ thể.
        Returns: số lượng key đã xóa.
        """
        key = self._make_key(group, *parts)
        return self._delete_key(key)

    def delete_group(self, group: str) -> int:
        """
        Xóa TOÀN BỘ keys trong một nhóm.
        Ví dụ: cache.delete_group("mp") → xóa hết gash:mp:*
        """
        count = 0
        pattern = self._group_pattern(group)

        if self._connected and self._redis:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    count = self._redis.delete(*keys)
                    logger.info(f"🗑️ Redis: deleted {count} keys matching '{pattern}'")
            except Exception as e:
                logger.warning(f"⚠️ Redis delete_group error: {e}")
                self._connected = False

        # Fallback in-memory
        fallback_keys = [k for k in self._fallback if k.startswith(f"gash:{group}:")]
        for k in fallback_keys:
            self._fallback.pop(k, None)
            self._fallback_ttl.pop(k, None)
        count += len(fallback_keys)

        return count

    def flush(self) -> int:
        """Xóa TẤT CẢ cache GASH (gash:*)."""
        count = 0

        if self._connected and self._redis:
            try:
                keys = self._redis.keys(self._all_pattern())
                if keys:
                    count = self._redis.delete(*keys)
                    logger.info(f"🗑️ Redis: flushed all GASH cache ({count} keys)")
            except Exception as e:
                logger.warning(f"⚠️ Redis flush error: {e}")
                self._connected = False

        # Fallback in-memory
        gash_keys = [k for k in self._fallback if k.startswith("gash:")]
        for k in gash_keys:
            self._fallback.pop(k, None)
            self._fallback_ttl.pop(k, None)
        count += len(gash_keys)

        return count

    def _delete_key(self, key: str) -> int:
        """Xóa một key."""
        count = 0
        if self._connected and self._redis:
            try:
                count = self._redis.delete(key)
            except Exception as e:
                logger.warning(f"⚠️ Redis delete error: {e}")
                self._connected = False

        # Fallback in-memory — count BEFORE pop
        had_key = key in self._fallback
        self._fallback.pop(key, None)
        self._fallback_ttl.pop(key, None)
        count += 1 if had_key else 0

        return count

    # ──────────────────────────────────────────────
    # UTILITY
    # ──────────────────────────────────────────────

    def exists(self, group: str, *parts: str) -> bool:
        """Kiểm tra key có tồn tại trong cache không."""
        key = self._make_key(group, *parts)
        if self._connected and self._redis:
            try:
                return bool(self._redis.exists(key))
            except Exception:
                pass
        return key in self._fallback

    def stats(self) -> Dict[str, Any]:
        """Lấy thống kê cache."""
        info = {
            "connected": self._connected,
            "backend": "redis" if self._connected else "in-memory",
            "groups": {},
        }

        # Đếm keys trong từng nhóm
        for group in DEFAULT_TTL:
            pattern = self._group_pattern(group)
            group_keys = set()

            if self._connected and self._redis:
                try:
                    group_keys.update(self._redis.keys(pattern) or [])
                except Exception:
                    pass

            fallback_keys = {
                k for k in self._fallback
                if k.startswith(f"gash:{group}:")
            }
            group_keys.update(fallback_keys)
            info["groups"][group] = len(group_keys)

        info["total_keys"] = sum(info["groups"].values())
        return info

    def keys(self, group: Optional[str] = None) -> List[str]:
        """Liệt kê keys theo nhóm (hoặc tất cả nếu None)."""
        pattern = self._group_pattern(group) if group else self._all_pattern()
        all_keys = set()

        if self._connected and self._redis:
            try:
                all_keys.update(self._redis.keys(pattern) or [])
            except Exception:
                pass

        all_keys.update(k for k in self._fallback if "gash:" in k)
        if group:
            all_keys = {k for k in all_keys if k.startswith(f"gash:{group}:")}
        else:
            all_keys = {k for k in all_keys if k.startswith("gash:")}

        return sorted(all_keys)


# ==================== DECORATOR ====================

def cached(group: str, ttl: Optional[int] = None, key_parts: Optional[List[str]] = None):
    """
    Decorator để tự động cache kết quả hàm.
    TODO: Áp dụng cho các method được gọi nhiều (ví dụ get_market_prices).

    Args:
        group: Nhóm cache (mp, inv, stats, web, ...)
        ttl: TTL override (giây)
        key_parts: Danh sách tên tham số dùng làm key (VD: ["product_name"])

    Usage:
        @cached("mp", ttl=300, key_parts=["product_name", "days"])
        def get_market_prices(product_name, days=7):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            parts = []
            if key_parts:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for kp in key_parts:
                    val = bound.arguments.get(kp, "")
                    parts.append(str(val) if val else "")

            cache_key = tuple(parts) if parts else None
            if cache_key:
                cached_val = cache.get(group, *parts)
                if cached_val is not None:
                    return cached_val

            result = func(*args, **kwargs)

            if cache_key and result is not None:
                cache.set(group, result, *parts, ttl=ttl)

            return result
        return wrapper
    return decorator


# ==================== SINGLETON (thread-safe) ====================

_cache_instance: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_cache() -> CacheManager:
    """Lấy instance CacheManager (singleton, thread-safe)."""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = CacheManager()
    return _cache_instance


def reset_cache():
    """Reset cache instance (dùng cho testing)."""
    global _cache_instance
    if _cache_instance:
        _cache_instance.flush()
    _cache_instance = None
