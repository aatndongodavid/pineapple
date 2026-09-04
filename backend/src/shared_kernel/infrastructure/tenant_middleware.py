import uuid
from contextvars import ContextVar
from typing import Callable, Awaitable

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar pour stocker le tenant_id de la requête courante
tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("tenant_id", default=None)

# Routes publiques qui ne nécessitent pas le header X-Tenant-ID
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


def get_current_tenant_id() -> uuid.UUID:
    """
    Récupère le tenant_id depuis le ContextVar.
    Lève une exception HTTP 400 s'il est absent.
    """
    tenant_id = tenant_id_ctx.get()
    if tenant_id is None:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required for this request",
        )
    return tenant_id


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui extrait et valide le header X-Tenant-ID,
    puis le stocke dans un ContextVar pour la durée de la requête.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        # Autoriser les routes publiques sans header
        if path in PUBLIC_PATHS:
            return await call_next(request)

        tenant_header = request.headers.get("X-Tenant-ID")
        if not tenant_header:
            raise HTTPException(status_code=400, detail="X-Tenant-ID header is missing")

        try:
            tenant_id = uuid.UUID(tenant_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="X-Tenant-ID must be a valid UUID")

        # Stocker dans le ContextVar
        token = tenant_id_ctx.set(tenant_id)
        try:
            response = await call_next(request)
            return response
        finally:
            # Réinitialiser le ContextVar à la fin de la requête
            tenant_id_ctx.reset(token)