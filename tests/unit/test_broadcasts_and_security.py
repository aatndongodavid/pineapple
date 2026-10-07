# tests/unit/test_broadcasts_and_security.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, func

from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel, ClassGroupModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel
from notification_context.infrastructure.persistence.models import OutboxEventModel, NotificationModel
from notification_context.domain.services.broadcast_service import BroadcastService


@pytest.mark.asyncio
async def test_gate_m8_class_broadcast_and_delegate_daily_quota(session_factory):
    """
    Gate M8: Un délégué peut diffuser une annonce à son groupe-classe (max 5/jour).
    """
    tenant_id = uuid.uuid4()
    class_id = uuid.uuid4()
    delegate_id = uuid.uuid4()
    student1_id = uuid.uuid4()
    student2_id = uuid.uuid4()

    async with session_factory() as db:
        tenant = TenantModel(id=tenant_id, name="Test School M8", code=f"M8_{uuid.uuid4().hex[:4]}", is_active=True)
        db.add(tenant)

        cls = ClassGroupModel(id=class_id, tenant_id=tenant_id, name="INFO3", code=f"I3_{uuid.uuid4().hex[:4]}", academic_year="2026-2027")
        db.add(cls)

        # Delegate
        u_del = UserModel(id=delegate_id, email=f"del_{delegate_id.hex[:6]}@test.com", first_name="Del", last_name="Egated", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        m_del = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=delegate_id, class_group_id=class_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
        db.add(u_del)
        db.add(m_del)

        # 2 Students
        for uid in (student1_id, student2_id):
            u = UserModel(id=uid, email=f"s_{uid.hex[:6]}@test.com", first_name="Student", last_name=uid.hex[:4], hashed_password="hash", account_status=AccountStatus.ACTIVE)
            m = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=uid, class_group_id=class_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
            db.add(u)
            db.add(m)

        await db.commit()

    # 1. Successful Broadcast
    async with session_factory() as db:
        service = BroadcastService(db)
        success, count, ref = await service.broadcast_to_class_group(
            tenant_id=tenant_id,
            author_id=delegate_id,
            class_group_id=class_id,
            title="Changement de salle",
            body="Le cours de Maths est déplacé en S102",
        )
        assert success is True
        assert count == 3  # Delegate + 2 students in class
        assert ref.startswith("bcast_")
        await db.commit()

    # Check outbox records
    async with session_factory() as db:
        res = await db.execute(select(OutboxEventModel).where(OutboxEventModel.tenant_id == tenant_id))
        outbox_items = res.scalars().all()
        assert len(outbox_items) > 0


@pytest.mark.asyncio
async def test_gate_m8_tenant_broadcast_admin_only(session_factory):
    """
    Gate M8: Diffusion à tout l'établissement réservée aux administrateurs.
    """
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()

    async with session_factory() as db:
        tenant = TenantModel(id=tenant_id, name="Test School Admin", code=f"ADM_{uuid.uuid4().hex[:4]}", is_active=True)
        db.add(tenant)

        u_admin = UserModel(id=admin_id, email=f"admin_{admin_id.hex[:6]}@test.com", first_name="Admin", last_name="User", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        m_admin = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=admin_id, role=MembershipRole.TENANT_ADMIN, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
        db.add(u_admin)
        db.add(m_admin)

        u_stud = UserModel(id=student_id, email=f"stud_{student_id.hex[:6]}@test.com", first_name="Stud", last_name="Ent", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        m_stud = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=student_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
        db.add(u_stud)
        db.add(m_stud)

        await db.commit()

    async with session_factory() as db:
        service = BroadcastService(db)
        success, count, ref = await service.broadcast_to_tenant(
            tenant_id=tenant_id,
            author_id=admin_id,
            title="Avis Général",
            body="La rentrée des classes aura lieu lundi",
        )
        assert success is True
        assert count == 2
        assert ref.startswith("admin_bcast_")
        await db.commit()
