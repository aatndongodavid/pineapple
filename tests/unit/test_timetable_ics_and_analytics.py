# tests/unit/test_timetable_ics_and_analytics.py

import uuid
from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from shared_kernel.infrastructure.security import create_jwt_token
from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus


@pytest.mark.asyncio
async def test_gate_e8_e9_ics_token_and_calendar_export(
    async_client: AsyncClient,
    session_factory,
    tenant_id_fixture,
):
    """
    Gate E8 & E9: Flux d'export iCal avec timezone Africa/Douala et jeton d'accès.
    """
    user_id = uuid.uuid4()

    async with session_factory() as db:
        tenant = (await db.execute(select(TenantModel).where(TenantModel.id == tenant_id_fixture))).scalars().first()
        if not tenant:
            tenant = TenantModel(id=tenant_id_fixture, name="École Test", code="ENSPD", is_active=True)
            db.add(tenant)

        unique_email = f"student_ics_{uuid.uuid4().hex[:6]}@test.com"
        user = UserModel(
            id=user_id,
            email=unique_email,
            first_name="Étudiant",
            last_name="ICS",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(user)

        membership = MembershipModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            role=MembershipRole.STUDENT,
            status=MembershipStatus.ACTIVE,
            academic_year="2026-2027",
        )
        db.add(membership)
        await db.commit()

    token = create_jwt_token(user_id=user_id, tenant_id=tenant_id_fixture, membership_id=membership.id, role="STUDENT")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id_fixture),
    }

    # 1. Generate ICS token
    tok_resp = await async_client.post("/api/v1/timetable/ics/token", headers=headers)
    assert tok_resp.status_code == 201
    tok_data = tok_resp.json()
    ics_token_str = tok_data["token"]
    assert ics_token_str.startswith("ics_")

    # 2. Download .ics calendar
    ics_resp = await async_client.get(f"/api/v1/timetable/ics/{ics_token_str}.ics")
    assert ics_resp.status_code == 200
    assert "text/calendar" in ics_resp.headers["content-type"]
    cal_text = ics_resp.text
    assert "BEGIN:VCALENDAR" in cal_text
    assert "X-WR-TIMEZONE:Africa/Douala" in cal_text
    assert "END:VCALENDAR" in cal_text


@pytest.mark.asyncio
async def test_gate_e10_multitenant_isolation_and_analytics(
    async_client: AsyncClient,
    session_factory,
    tenant_id_fixture,
):
    """
    Gate E10: Vérification du cloisonnement strict multi-tenant et des statistiques admin.
    """
    user_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()

    async with session_factory() as db:
        # Seed Tenant A and Admin
        tenant_a = (await db.execute(select(TenantModel).where(TenantModel.id == tenant_id_fixture))).scalars().first()
        if not tenant_a:
            tenant_a = TenantModel(id=tenant_id_fixture, name="École A", code="ECA", is_active=True)
            db.add(tenant_a)

        # Seed Tenant B if not present
        code_b = f"ECB_{uuid.uuid4().hex[:4]}"
        tenant_b = TenantModel(id=tenant_b_id, name="École B", code=code_b, is_active=True)
        db.add(tenant_b)

        unique_email = f"admin_analytics_{uuid.uuid4().hex[:6]}@test.com"
        user = UserModel(
            id=user_id,
            email=unique_email,
            first_name="Admin",
            last_name="Analytics",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(user)

        membership_a = MembershipModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            role=MembershipRole.TENANT_ADMIN,
            status=MembershipStatus.ACTIVE,
            academic_year="2026-2027",
        )
        db.add(membership_a)

        await db.commit()

    token_a = create_jwt_token(user_id=user_id, tenant_id=tenant_id_fixture, membership_id=membership_a.id, role="TENANT_ADMIN")
    headers_a = {
        "Authorization": f"Bearer {token_a}",
        "X-Tenant-ID": str(tenant_id_fixture),
    }

    # Query analytics for Tenant A
    analytics_resp = await async_client.get("/api/v1/timetable/analytics/occupancy", headers=headers_a)
    assert analytics_resp.status_code == 200
    an_data = analytics_resp.json()
    assert "total_rooms" in an_data
    assert "underutilized_rooms" in an_data

    # Attempt cross-tenant header tampering with Tenant B ID should be rejected or isolated
    headers_b_tampered = {
        "Authorization": f"Bearer {token_a}",
        "X-Tenant-ID": str(tenant_b_id),
    }
    cross_resp = await async_client.get("/api/v1/timetable/analytics/occupancy", headers=headers_b_tampered)
    # Require tenant check matching JWT claim `tid`
    assert cross_resp.status_code in (401, 403)
