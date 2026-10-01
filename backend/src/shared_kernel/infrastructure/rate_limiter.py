# backend/src/shared_kernel/infrastructure/rate_limiter.py

import time
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Simple in-memory sliding window rate limiter
_request_counts: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # 1 minute
MAX_REQUESTS_PER_WINDOW = 120  # 120 requêtes par minute par IP


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware anti-DDoS et protection contre le scraping excessif.
    Bloque les clients dépassant 120 requêtes/minute avec un HTTP 429.
    Exempte les routes de métriques et de santé.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json", "/metrics") or path.startswith("/api/v1/platform"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Nettoyage des anciennes requêtes de la fenêtre
        timestamps = _request_counts[client_ip]
        _request_counts[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

        if len(_request_counts[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Trop de requêtes. Veuillez patienter avant d'essayer à nouveau.",
                    "error": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": "60"},
            )

        _request_counts[client_ip].append(now)
        return await call_next(request)
