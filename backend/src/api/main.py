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

# Métadonnées de l'application
APP_DESCRIPTION = """
Pineapple OS - Le système d'exploitation numérique des campus africains.

API backend officielle de Pineapple 3.0.
Connecter. Collaborer. Grandir.
"""

app = FastAPI(
    title="Pineapple OS API",
    description=APP_DESCRIPTION,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middlewares

# Middleware CORS pour la PWA React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Dev React
        "http://localhost:5173",      # Vite dev server
        "https://app.pineapple.cm",   # Production
        # Ajoutez ici les domaines autorisés en fonction de l'environnement
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de gestion du tenant (header X-Tenant-ID)
app.add_middleware(TenantMiddleware)

# Health & Metrics

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de santé pour les probes Kubernetes / Load Balancer.
    """
    return {"status": "ok", "service": "pineapple-api", "version": "3.0.0"}

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

# Optionnel : point d'entrée racine
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Pineapple OS API", "docs": "/docs", "health": "/health"}