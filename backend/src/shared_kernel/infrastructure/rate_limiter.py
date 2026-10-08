# backend/src/shared_kernel/infrastructure/rate_limiter.py

import logging
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from redis.asyncio import Redis, RedisError

from shared_kernel.config import settings

logger = logging.getLogger("RateLimiter")

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Optional[Redis]:
    """
    Récupère le client Redis ou None si Redis est inaccessible.
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.error(f"Redis connection initialization failed: {e}")
            return None
    return _redis_client


def rate_limit_sensitive_endpoint(max_requests: int = 5, window_seconds: int = 60):
    """
    Dépendance de Rate Limiting pour endpoints sensibles (Login, Paiement, Mots de passe).
    Gate O-4: En cas de panne de Redis, les endpoints sensibles ÉCHOUENT FERMÉ (Fail-Closed, HTTP 503/429).
    Ils ne s'exécutent JAMAIS sans rate limiting en production !
    """

    async def _dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint_key = f"rate_limit:{request.url.path}:{client_ip}"

        try:
            redis = await get_redis_client()
            if not redis:
                raise RedisError("Redis instance non disponible")

            current = await redis.incr(endpoint_key)
            if current == 1:
                await redis.expire(endpoint_key, window_seconds)

            if current > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Trop de requêtes. Veuillez réespacer vos tentatives."},
                )

        except (RedisError, ConnectionError, OSError) as exc:
            logger.error(f"Gate O-4: Panne Redis détectée lors du rate limiting de {request.url.path}: {exc}")

            # En production, échec fermé impératif pour la sécurité
            if settings.ENVIRONMENT.lower() in ("production", "prod"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "code": "REDIS_UNAVAILABLE_FAIL_CLOSED",
                        "message": "Service de sécurité temporairement indisponible (Gate O-4 Fail-Closed). Veuillez réessayer dans un instant.",
                    },
                )
            # En environnement dev/test, avertir mais poursuivre si Redis absent
            logger.warning("Environnement dev/test: dégradation tolérée pour Redis absent.")

        return True

    return _dependency
