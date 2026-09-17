import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.database import ping_db
from app.api.v1.api import api_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pineapple.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Démarrage de {settings.PROJECT_NAME} v{settings.VERSION} ({settings.ENVIRONMENT})")
    db_status = await ping_db()
    if db_status:
        logger.info("Connexion à la base de données PostgreSQL établie avec succès.")
    else:
        logger.warning("Attention : Impossible de contacter la base de données au démarrage.")
    yield
    logger.info("Arrêt de l'application Pineapple Backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Pineapple - L'OS Numérique Universitaire (API Backend MVP)",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
