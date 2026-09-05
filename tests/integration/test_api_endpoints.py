# tests/integration/test_api_endpoints.py

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext
from jose import jwt

from api.main import app
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal, Base
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id
from identity_context.infrastructure.persistence.models import UserModel
from democracy_context.infrastructure.persistence.models import ElectionModel
from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    VerificationStatus,
)
from democracy_context.domain.entities import ElectionStatus

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ---------------------------------------------------------------------------
# Fixtures locales pour préparer les données
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def seed_users(async_db_session: AsyncSession):
    """
    Insère un admin (enseignant vérifié) et un étudiant certifié dans la base.
    Retourne leurs identifiants.
    """
    tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

    admin_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    student_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    admin = UserModel(
        id=admin_id,
        tenant_id=tenant_id,
        email="admin@test.com",
        hashed_password=pwd_context.hash("Admin123!"),
        first_name="Admin",
        last_name="Test",
        matricule="ADMIN001",
        faculty="Administration",
        filiere="N/A",
        academic_year="2026-2027",
        account_status=AccountStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        academic_status=AcademicStatus.TEACHER,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    student = UserModel(
        id=student_id,
        tenant_id=tenant_id,
        email="student@test.com",
        hashed_password=pwd_context.hash("Student123!"),
        first_name="Alice",
        last_name="Student",
        matricule="STU001",
        faculty="Génie Logiciel",
        filiere="Informatique",
        academic_year="2026-2027",
        account_status=AccountStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        academic_status=AcademicStatus.STUDENT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    async_db_session.add_all([admin, student])
    await async_db_session.commit()

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "student_id": student_id,
        "admin_email": "admin@test.com",
        "student_email": "student@test.com",
    }


def make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestIdentityFlow:
    async def test_register_login_and_get_me(self, async_client: AsyncClient):
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        headers = {"X-Tenant-ID": str(tenant_id)}

        # Inscription
        register_payload = {
            "email": "newuser@test.com",
            "password": "NewUser123!",
            "first_name": "New",
            "last_name": "User",
            "matricule": "NEW001",
            "faculty": "Génie",
            "filiere": "Informatique",
            "academic_year": "2026-2027",
        }
        resp = await async_client.post("/api/v1/identity/register", json=register_payload, headers=headers)
        assert resp.status_code == 201, resp.text

        # Connexion
        login_payload = {"email": "newuser@test.com", "password": "NewUser123!"}
        resp = await async_client.post("/api/v1/identity/login", json=login_payload, headers=headers)
        assert resp.status_code == 200, resp.text
        token_data = resp.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        # Récupération du profil
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        }
        resp = await async_client.get("/api/v1/identity/me", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        profile = resp.json()
        assert profile["email"] == "newuser@test.com"
        assert profile["campus_status_display"] == "Non certifié"


    async def test_missing_tenant_header_returns_400(self, async_client: AsyncClient):
        # Appeler une route protégée sans header X-Tenant-ID
        resp = await async_client.get("/api/v1/identity/me")
        assert resp.status_code == 400
        assert "X-Tenant-ID" in resp.text


@pytest.mark.asyncio
class TestDemocracyVoting:
    async def test_vote_emission_and_double_vote_conflict(
        self,
        async_client: AsyncClient,
        seed_users: dict,
    ):
        tenant_id = seed_users["tenant_id"]
        admin_id = seed_users["admin_id"]
        student_id = seed_users["student_id"]

        # Générer des tokens pour admin et étudiant
        admin_token = make_token(admin_id, tenant_id)
        student_token = make_token(student_id, tenant_id)

        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "X-Tenant-ID": str(tenant_id),
        }
        student_headers = {
            "Authorization": f"Bearer {student_token}",
            "X-Tenant-ID": str(tenant_id),
        }

        # 1. Créer une élection (admin)
        election_payload = {
            "title": "Élection Test",
            "election_type": "BDE",
            "eligibility_rules": {"level": "L3", "certified": True},
            "voting_start_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "voting_end_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
        resp = await async_client.post(
            "/api/v1/democracy/elections", json=election_payload, headers=admin_headers
        )
        assert resp.status_code == 201, resp.text
        election_id = resp.json()["id"]

        # 2. Voter une première fois (étudiant)
        vote_payload = {"election_id": election_id, "choice_id": "candidate-1"}
        resp = await async_client.post(
            f"/api/v1/democracy/elections/{election_id}/vote",
            json=vote_payload,
            headers=student_headers,
        )
        assert resp.status_code == 202, resp.text

        # 3. Tenter un second vote → 409 Conflict
        resp = await async_client.post(
            f"/api/v1/democracy/elections/{election_id}/vote",
            json=vote_payload,
            headers=student_headers,
        )
        assert resp.status_code == 409
        assert "already voted" in resp.text.lower()