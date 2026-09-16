from fastapi import APIRouter, status
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import ping_db

router = APIRouter()

class HealthCheckResponse(BaseModel):
    status: str
    project: str
    version: str
    environment: str
    database_connected: bool

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Vérification de la santé de l'API et de la Base de Données",
    tags=["Système & Santé"]
)
async def health_check():
    db_ok = await ping_db()
    return HealthCheckResponse(
        status="healthy" if db_ok else "degraded",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_ok,
    )
