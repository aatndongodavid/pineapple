# backend/src/shared_kernel/infrastructure/redis_cache.py

import json
import logging
from typing import Any, Optional

from shared_kernel.config import settings

logger = logging.getLogger("pineapple.redis")

# In-memory fallback dictionary for test/dev environments without Redis running
_memory_cache: dict[str, tuple[Any, float]] = {}

try:
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis initialization warning: {e}. Using in-memory fallback cache.")
    redis_client = None


class CacheService:
    """Service de mise en cache Redis hautement disponible avec fallback en mémoire."""

    @staticmethod
    async def get_json(key: str) -> Optional[Any]:
        if redis_client:
            try:
                data = await redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as err:
                logger.error(f"Redis GET failed for key '{key}': {err}")

        # Fallback en mémoire
        if key in _memory_cache:
            val, _ = _memory_cache[key]
            return val
        return None

    @staticmethod
    async def set_json(key: str, value: Any, ttl_seconds: int = 300) -> None:
        if redis_client:
            try:
                await redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
                return
            except Exception as err:
                logger.error(f"Redis SET failed for key '{key}': {err}")

        # Fallback en mémoire
        _memory_cache[key] = (value, 0.0)

    @staticmethod
    async def delete(key: str) -> None:
        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as err:
                logger.error(f"Redis DELETE failed for key '{key}': {err}")
        _memory_cache.pop(key, None)

    @staticmethod
    async def invalidate_pattern(pattern: str) -> None:
        if redis_client:
            try:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as err:
                logger.error(f"Redis invalidate_pattern failed for '{pattern}': {err}")
        
        # En mémoire
        to_delete = [k for k in _memory_cache if pattern.replace('*', '') in k]
        for k in to_delete:
            _memory_cache.pop(k, None)
