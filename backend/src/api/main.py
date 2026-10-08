# backend/src/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_kernel.config import settings
from shared_kernel.infrastructure.tenant_middleware import TenantMiddleware

# Valider la sécurité au chargement des configurations
settings.validate_production_security()


# Import des routeurs v1
from api.v1.identity_router import router as identity_router
from api.v1.schools_router import router as schools_router
from api.v1.enrollment_router import router as enrollment_router
from api.v1.ads_router import router as ads_router
from api.v1.community_router import router as community_router
from api.v1.class_delegate_router import router as class_delegate_router
from api.v1.admin_router import router as admin_router
from api.v1.platform_router import router as platform_router
from api.v1.democracy_router import router as democracy_router
from api.v1.academy_router import router as academy_router
from api.v1.campus_life_router import router as campus_life_router
from api.v1.opportunities_router import router as opportunities_router
from api.v1.monetization_router import router as monetization_router
from api.v1.trust_safety_router import router as trust_safety_router

APP_DESCRIPTION = """
Pineapple OS — Le système d'exploitation numérique des établissements scolaires.
Refonte Établissement d'abord (School-First).
"""

app = FastAPI(
    title="Pineapple OS API",
    description=APP_DESCRIPTION,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Piloté en dev/prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de gestion du tenant
app.add_middleware(TenantMiddleware)


from shared_kernel.infrastructure.metrics import prometheus_metrics_middleware, get_prometheus_metrics_response
from shared_kernel.infrastructure.logging_config import correlation_id_middleware

# Middleware de correlation ID & Métriques Prometheus
app.middleware("http")(correlation_id_middleware)
app.middleware("http")(prometheus_metrics_middleware)

# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "pineapple-api", "version": "3.0.0"}


# Metrics Prometheus (Gate O-5)
@app.get("/metrics", tags=["Observability"])
async def get_metrics():
    return get_prometheus_metrics_response()


from api.v1.timetable_router import router as timetable_router
from api.v1.notification_router import router as notification_router

from api.v1.advertiser_router import router as advertiser_router

# Enregistrement des routeurs
from api.v1.demo_request_router import public_router as demo_public_router, admin_router as demo_admin_router

app.include_router(identity_router, prefix="/api/v1")
app.include_router(schools_router, prefix="/api/v1")
app.include_router(enrollment_router, prefix="/api/v1")
app.include_router(ads_router, prefix="/api/v1")
app.include_router(advertiser_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(class_delegate_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(platform_router, prefix="/api/v1")
app.include_router(democracy_router, prefix="/api/v1")
app.include_router(academy_router, prefix="/api/v1")
app.include_router(timetable_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(campus_life_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(monetization_router, prefix="/api/v1")
app.include_router(trust_safety_router, prefix="/api/v1")
app.include_router(demo_public_router, prefix="/api/v1")
app.include_router(demo_admin_router, prefix="/api/v1")



@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Pineapple OS API", "docs": "/docs", "health": "/health"}