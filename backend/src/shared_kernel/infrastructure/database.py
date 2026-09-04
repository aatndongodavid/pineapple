from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from shared_kernel.config import settings

# Configuration du moteur asynchrone avec pool de connexions
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Fabrique de sessions asynchrones
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe de base déclarative pour tous les modèles ORM."""
    pass


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    Générateur de dépendance FastAPI fournissant une session de base de données.
    La session est automatiquement fermée après usage.
    """
    async with AsyncSessionLocal() as session:
        yield session