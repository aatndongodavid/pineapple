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
from shared_kernel.infrastructure.security import create_access_token
from identity_context.infrastructure.persistence.models import (
    UserModel,
    TenantModel,
    MembershipModel,
    RosterEntryModel,
)
from identity_context.domain.value_objects import (
    AccountStatus,
    MembershipRole,
    MembershipStatus,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@pytest_asyncio.fixture
async def seed_school_and_users(session_factory):
    """
    Insère un tenant, un admin et un étudiant membres dans la base.
    """
    async with session_factory() as db:
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        admin_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        student_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

        existing_tenant = (await db.execute(select(TenantModel).where((TenantModel.id == tenant_id) | (TenantModel.code == "ENSPD")))).scalars().first()
        if not existing_tenant:
            tenant = TenantModel(
                id=tenant_id,
                name="École Test",
                code="ENSPD",
                is_active=True,
            )
            db.add(tenant)

        admin_user = (await db.execute(select(UserModel).where(UserModel.id == admin_id))).scalars().first()
        if not admin_user:
            admin_user = UserModel(
                id=admin_id,
                email="admin@test.com",
                hashed_password=pwd_context.hash("Admin123!"),
                first_name="Admin",
                last_name="Test",
                account_status=AccountStatus.ACTIVE.value,
            )
            db.add(admin_user)

        student_user = (await db.execute(select(UserModel).where(UserModel.id == student_id))).scalars().first()
        if not student_user:
            student_user = UserModel(
                id=student_id,
                email="student@test.com",
                hashed_password=pwd_context.hash("Student123!"),
                first_name="Alice",
                last_name="Student",
                account_status=AccountStatus.ACTIVE.value,
            )
            db.add(student_user)

        admin_membership = (await db.execute(select(MembershipModel).where(MembershipModel.user_id == admin_id))).scalars().first()
        if not admin_membership:
            admin_membership = MembershipModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=admin_id,
                role=MembershipRole.TENANT_ADMIN.value,
                status=MembershipStatus.ACTIVE.value,
                joined_via="ADMIN",
                joined_at=datetime.utcnow(),
                academic_year="2026-2027",
            )
            db.add(admin_membership)

        student_membership = (await db.execute(select(MembershipModel).where(MembershipModel.user_id == student_id))).scalars().first()
        if not student_membership:
            student_membership = MembershipModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=student_id,
                role=MembershipRole.STUDENT.value,
                status=MembershipStatus.ACTIVE.value,
                joined_via="CLAIM",
                joined_at=datetime.utcnow(),
                academic_year="2026-2027",
            )
            db.add(student_membership)

        await db.commit()

        return {
            "tenant_id": tenant_id,
            "admin_id": admin_id,
            "student_id": student_id,
            "admin_membership_id": admin_membership.id,
            "student_membership_id": student_membership.id,
            "admin_email": "admin@test.com",
            "student_email": "student@test.com",
        }


def make_school_token(user_id: uuid.UUID, tenant_id: uuid.UUID = None, membership_id: uuid.UUID = None, role: str = "VISITOR") -> str:
    return create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        membership_id=membership_id,
        role=role,
    )


@pytest.mark.asyncio
class TestIdentityFlow:
    async def test_register_login_and_get_me(self, async_client: AsyncClient):
        # 1. Inscription publique (Visitor)
        unique_email = f"visitor_{uuid.uuid4().hex[:8]}@test.com"
        register_payload = {
            "email": unique_email,
            "password": "Password123!",
            "first_name": "Jean",
            "last_name": "Dupont",
        }
        resp = await async_client.post("/api/v1/identity/register", json=register_payload)
        assert resp.status_code == 201, resp.text
        token_data = resp.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        # 2. Connexion
        login_payload = {"email": unique_email, "password": "Password123!"}
        resp = await async_client.post("/api/v1/identity/login", json=login_payload)
        assert resp.status_code == 200, resp.text
        token_data = resp.json()
        assert "access_token" in token_data

        # 3. Récupération du profil /me (Visitor)
        auth_headers = {"Authorization": f"Bearer {token}"}
        resp = await async_client.get("/api/v1/identity/me", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        profile = resp.json()
        assert profile["user"]["email"] == unique_email
        assert profile["membership"]["id"] is None or profile["membership"]["role"] == "VISITOR"
        assert profile["membership"]["role"] == "VISITOR"
        assert profile["campus_status_display"] == "Visiteur"

    async def test_unauthenticated_me_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/identity/me")
        assert resp.status_code == 401

    async def test_tenant_mismatch_returns_403(self, async_client: AsyncClient, seed_school_and_users: dict):
        tenant_id = seed_school_and_users["tenant_id"]
        user_id = seed_school_and_users["student_id"]
        token = make_school_token(user_id, tenant_id=tenant_id, membership_id=seed_school_and_users["student_membership_id"], role="STUDENT")

        # Header X-Tenant-ID est différent du tid dans le JWT -> 403 Forbidden
        wrong_tenant_id = uuid.uuid4()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(wrong_tenant_id),
        }
        resp = await async_client.get("/api/v1/identity/me", headers=headers)
        assert resp.status_code == 403
        assert "X-Tenant-ID" in resp.text or "correspond pas" in resp.text