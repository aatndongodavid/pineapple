import os
import sys
import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Ajouter src au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from api.main import app
from shared_kernel.config import settings

TEST_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_USER_ID_STUDENT = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_USER_ID_TEACHER = uuid.UUID("33333333-3333-3333-3333-333333333333")
TEST_USER_ID_MODERATOR = uuid.UUID("44444444-4444-4444-4444-444444444444")
TEST_USER_ID_ADMIN = uuid.UUID("55555555-5555-5555-5555-555555555555")
TEST_USER_ID_THIRD = uuid.UUID("66666666-6666-6666-6666-666666666666")


def make_jwt(user_id: uuid.UUID, tenant_id: uuid.UUID, role: str) -> str:
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def make_platform_admin_jwt(admin_id: uuid.UUID) -> str:
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "sub": str(admin_id),
        "email": "admin@gemula.cm",
        "scope": "platform",
        "exp": expiration,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


import asyncio
from shared_kernel.infrastructure.database import Base, engine

# Importer les modèles ORM pour s'assurer qu'ils sont déclarés sur Base.metadata
import shared_kernel.infrastructure.platform_models
import identity_context.infrastructure.persistence.models
import community_context.infrastructure.persistence.models
import democracy_context.infrastructure.persistence.models
import academy_context.infrastructure.persistence.models
import campus_life_context.infrastructure.persistence.models
import opportunities_context.infrastructure.persistence.models
import monetization_context.infrastructure.persistence.models
import trust_safety_context.infrastructure.persistence.models


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_headers():
    token = make_jwt(TEST_USER_ID_STUDENT, TEST_TENANT_ID, "STUDENT")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TEST_TENANT_ID),
    }


@pytest.fixture
def teacher_headers():
    token = make_jwt(TEST_USER_ID_TEACHER, TEST_TENANT_ID, "TEACHER")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TEST_TENANT_ID),
    }


@pytest.fixture
def moderator_headers():
    token = make_jwt(TEST_USER_ID_MODERATOR, TEST_TENANT_ID, "MODERATOR")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TEST_TENANT_ID),
    }


@pytest.fixture
def admin_headers():
    token = make_jwt(TEST_USER_ID_ADMIN, TEST_TENANT_ID, "ADMIN")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TEST_TENANT_ID),
    }


@pytest.fixture
def third_user_headers():
    token = make_jwt(TEST_USER_ID_THIRD, TEST_TENANT_ID, "STUDENT")
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(TEST_TENANT_ID),
    }


@pytest.fixture
def platform_admin_headers():
    token = make_platform_admin_jwt(uuid.uuid4())
    return {
        "Authorization": f"Bearer {token}",
    }
