# backend/src/api/main.py

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from shared_kernel.infrastructure.tenant_middleware import TenantMiddleware

# Import des routeurs v1
from api.v1.identity_router import router as identity_router
from api.v1.community_router import router as community_router
from api.v1.democracy_router import router as democracy_router
from api.v1.academy_router import router as academy_router
from api.v1.campus_life_router import router as campus_life_router
from api.v1.opportunities_router import router as opportunities_router
from api.v1.monetization_router import router as monetization_router
from api.v1.trust_safety_router import router as trust_safety_router
from api.v1.platform_admin_router import router as platform_admin_router
from api.v1.search_router import router as search_router

# Métadonnées de l'application
APP_DESCRIPTION = """
Pineapple OS - Le système d'exploitation numérique des campus africains.

API backend officielle de Pineapple 3.0.
Connecter. Collaborer. Grandir.
"""

from contextlib import asynccontextmanager
from shared_kernel.infrastructure.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="Pineapple OS API",
    description=APP_DESCRIPTION,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text

from shared_kernel.infrastructure.rate_limiter import RateLimiterMiddleware
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.redis_cache import redis_client

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; img-src 'self' data: https:;"
        return response

# Middlewares (Ordre d'exécution)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware)

# Middleware CORS pour la PWA React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Dev React
        "http://localhost:5173",      # Vite dev server
        "https://app.pineapple.cm",   # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de gestion du tenant (header X-Tenant-ID)
app.add_middleware(TenantMiddleware)

# Health & Metrics

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de santé approfondi pour Load Balancer & Kubernetes.
    Teste la connectivité effective à PostgreSQL et à Redis.
    """
    health_status = {"status": "ok", "db": "unknown", "redis": "unknown", "service": "pineapple-api"}
    
    # 1. Vérification PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            health_status["db"] = "connected"
    except Exception as e:
        health_status["db"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 2. Vérification Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["redis"] = "in_memory_fallback"

    status_code = status.HTTP_200_OK if health_status["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/metrics", tags=["Observability"])
async def metrics():
    """
    Endpoint de métriques (placeholder).
    À remplacer par une intégration Prometheus / OpenTelemetry.
    """
    return {
        "requests_total": 0,
        "latency_p95_ms": 0,
        "error_rate": 0,
    }

# Enregistrement des routeurs 

app.include_router(identity_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(democracy_router, prefix="/api/v1")
app.include_router(academy_router, prefix="/api/v1")
app.include_router(campus_life_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(monetization_router, prefix="/api/v1")
app.include_router(trust_safety_router, prefix="/api/v1")
app.include_router(platform_admin_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")

# Optionnel : point d'entrée racine
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Pineapple OS API", "docs": "/docs", "health": "/health"}