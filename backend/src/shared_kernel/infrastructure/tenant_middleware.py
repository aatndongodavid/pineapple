import uuid
from contextvars import ContextVar
from typing import Callable, Awaitable, Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from shared_kernel.config import settings

# ContextVar pour stocker le tenant_id de la requête courante
tenant_id_ctx: ContextVar[Optional[uuid.UUID]] = ContextVar("tenant_id", default=None)

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/identity/register",
    "/api/v1/identity/login",
    "/api/v1/schools/public",
    "/api/v1/ads/feed",
}


def get_current_tenant_id() -> Optional[uuid.UUID]:
    """Récupère le tenant_id depuis le ContextVar de la requête courante."""
    return tenant_id_ctx.get()


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'isolation tenant (Décision D4).
    Le tenant provient des claims du JWT (claim `tid`), et non d'un header client.
    Si le header X-Tenant-ID est présent et diffère de tid, la requête est rejetée (403).
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        tenant_header = request.headers.get("X-Tenant-ID")
        jwt_tid: Optional[uuid.UUID] = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                tid_str = payload.get("tid")
                if tid_str:
                    jwt_tid = uuid.UUID(tid_str)
            except Exception:
                pass  # La validation formelle du JWT sera faite par les dépendances de sécurité

        # Décision D4 : Vérification de concordance si le header X-Tenant-ID est transmis
        if tenant_header and jwt_tid:
            try:
                header_tid = uuid.UUID(tenant_header)
                if header_tid != jwt_tid:
                    return JSONResponse(
                        status_code=403,
                        content={"code": "TENANT_MISMATCH", "detail": "Le header X-Tenant-ID ne correspond pas à l'établissement identifié dans le jeton JWT"},
                    )
            except ValueError:
                return JSONResponse(status_code=400, content={"code": "INVALID_TENANT_ID", "detail": "X-Tenant-ID doit être un UUID valide"})

        token_ref = tenant_id_ctx.set(jwt_tid)
        try:
            response = await call_next(request)
            return response
        finally:
            tenant_id_ctx.reset(token_ref)