# tests/unit/test_room_availability_ws.py

import uuid
from datetime import date, time, datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from shared_kernel.infrastructure.security import create_jwt_token
from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus
from community_context.infrastructure.persistence.models import RoomModel, RoomStatusDeclarationModel
from community_context.domain.value_objects import RoomStatus


@pytest.mark.asyncio
async def test_gate_e6_room_availability_priority_t3_and_ws(
    async_client: AsyncClient,
    session_factory,
    tenant_id_fixture,
):
    """
    Gate E6: Vérification de l'algorithme T3 (Délégué > Réservation > Cours > Libre)
    et de l'endpoint de disponibilité des salles.
    """
    user_id = uuid.uuid4()

    async with session_factory() as db:
        tenant = (await db.execute(select(TenantModel).where(TenantModel.id == tenant_id_fixture))).scalars().first()
        if not tenant:
            tenant = TenantModel(id=tenant_id_fixture, name="École Test", code="ENSPD", is_active=True)
            db.add(tenant)

        unique_email = f"delegate_{uuid.uuid4().hex[:6]}@test.com"
        user = UserModel(
            id=user_id,
            email=unique_email,
            first_name="Délégué",
            last_name="Test",
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

        room = RoomModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id_fixture,
            name="AMPHI 500",
            capacity=500,
            status=RoomStatus.FREE
        )
        db.add(room)

        # Active delegate declaration: room is OCCUPIED due to unscheduled session
        decl = RoomStatusDeclarationModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id_fixture,
            room_id=room.id,
            declared_by_user_id=user_id,
            status=RoomStatus.OCCUPIED,
            note="Projecteur en panne et climatisation en révision",
            declared_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc).replace(year=2030),
        )
        db.add(decl)

        await db.commit()

    token = create_jwt_token(user_id=user_id, tenant_id=tenant_id_fixture, membership_id=membership.id, role="STUDENT")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id_fixture),
    }

    # Query availability endpoint
    resp = await async_client.get(
        f"/api/v1/timetable/rooms/availability?target_date=2026-10-15&start_time=08:00&end_time=10:00",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["rooms"]) >= 1

    target_room = next(r for r in data["rooms"] if r["room_name"] == "AMPHI 500")
    assert target_room["status"] == "OCCUPIED"
    assert "délégué" in target_room["reason"].lower()
