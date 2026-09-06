# tests/conftest.py

import asyncio
import os
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from jose import jwt

from api.main import app
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import Base, get_db_session

# ---------------------------------------------------------------------------
# Configuration de la base de test
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://pineapple:pineapple_dev_password@localhost:5432/pineapple_test",
)

# ---------------------------------------------------------------------------
# Fixture de boucle d'événements (scope session)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    """Crée une boucle d'événements pour toute la session de test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Moteur de base de données et session factory de test
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Crée un moteur asynchrone de test et initialise le schéma."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    # Création des tables (en développement, utilisez Alembic pour les migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(db_engine):
    """Fournit une async_sessionmaker liée au moteur de test."""
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return factory


# ---------------------------------------------------------------------------
# Override de la dépendance FastAPI get_db_session pour les tests
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_client(session_factory):
    """Retourne un client HTTP asynchrone configuré sur l'application FastAPI."""
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Nettoyage
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Session de base de données directe (pour les tests unitaires internes)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def async_db_session(session_factory):
    """Fournit une session SQLAlchemy avec rollback automatique après le test."""
    async with session_factory() as session:
        async with session.begin():
            yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Fixtures de données utiles
# ---------------------------------------------------------------------------
@pytest.fixture
def tenant_id_fixture():
    """Renvoie un UUID de tenant fixe pour les tests."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_headers_fixture(tenant_id_fixture):
    """
    Construit des headers HTTP incluant X-Tenant-ID et un token JWT valide.
    Le token est signé avec la clé de settings et contient sub + tenant_id.
    """
    user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id_fixture),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id_fixture),
    }
    return headers


@pytest.fixture
def clean_tables(session_factory):
    """
    Nettoie toutes les tables entre les tests.
    Utiliser avec parcimonie (lent) ou en combinaison avec des transactions.
    """
    async def _clean():
        async with session_factory() as session:
            # Exécute TRUNCATE sur toutes les tables
            from sqlalchemy import text
            await session.execute(text("TRUNCATE TABLE users CASCADE"))
            await session.execute(text("TRUNCATE TABLE publications CASCADE"))
            await session.execute(text("TRUNCATE TABLE organizations CASCADE"))
            await session.execute(text("TRUNCATE TABLE rooms CASCADE"))
            await session.execute(text("TRUNCATE TABLE elections CASCADE"))
            await session.execute(text("TRUNCATE TABLE movements CASCADE"))
            await session.execute(text("TRUNCATE TABLE ballots CASCADE"))
            await session.execute(text("TRUNCATE TABLE audit_logs CASCADE"))
            await session.execute(text("TRUNCATE TABLE library_documents CASCADE"))
            await session.execute(text("TRUNCATE TABLE purchases CASCADE"))
            await session.execute(text("TRUNCATE TABLE courses CASCADE"))
            await session.execute(text("TRUNCATE TABLE marketplace_listings CASCADE"))
            await session.execute(text("TRUNCATE TABLE rideshares CASCADE"))
            await session.execute(text("TRUNCATE TABLE conversations CASCADE"))
            await session.execute(text("TRUNCATE TABLE messages CASCADE"))
            await session.execute(text("TRUNCATE TABLE opportunities CASCADE"))
            await session.execute(text("TRUNCATE TABLE opportunity_applications CASCADE"))
            await session.execute(text("TRUNCATE TABLE sponsorships CASCADE"))
            await session.execute(text("TRUNCATE TABLE campus_licenses CASCADE"))
            await session.execute(text("TRUNCATE TABLE reports CASCADE"))
            await session.execute(text("TRUNCATE TABLE trust_safety_audit_logs CASCADE"))
            await session.commit()
    return _clean