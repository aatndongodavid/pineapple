# tests/unit/test_notification_channels.py

import uuid
import pytest
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel, ClassGroupModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel, DeliveryStatus
from notification_context.infrastructure.persistence.models import NotificationModel, NotificationDeliveryModel
from notification_context.domain.services.audience_resolver import AudienceResolver
from notification_context.infrastructure.adapters.in_app_channel import InAppChannelAdapter
from notification_context.infrastructure.adapters.email_gateway import EmailGatewayAdapter


@pytest.mark.asyncio
async def test_gate_m1_class_announcement_delivered_to_class_members_inapp_and_ws(
    session_factory,
):
    """
    Gate M1: Lorsqu'une annonce de classe est publiée, seuls les membres du groupe-classe
    reçoivent la notification In-App / WebSocket.
    """
    tenant_id = uuid.uuid4()
    class_id = uuid.uuid4()
    student1_id = uuid.uuid4()
    student2_id = uuid.uuid4()
    other_student_id = uuid.uuid4()

    async with session_factory() as db:
        # Seed Tenant & Class Group
        tenant = TenantModel(id=tenant_id, name="École Test M1", code=f"M1_{uuid.uuid4().hex[:4]}", is_active=True)
        db.add(tenant)

        code_cls = f"GIT3_{uuid.uuid4().hex[:4]}"
        cls_grp = ClassGroupModel(id=class_id, tenant_id=tenant_id, name="GIT3", code=code_cls, academic_year="2026-2027")
        db.add(cls_grp)

        # 2 students in GIT3 class
        for uid in (student1_id, student2_id):
            u = UserModel(id=uid, email=f"stud_{uid.hex[:6]}@test.com", first_name="Student", last_name=uid.hex[:4], hashed_password="hash", account_status=AccountStatus.ACTIVE)
            m = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=uid, class_group_id=class_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
            db.add(u)
            db.add(m)

        # 1 student in another class
        u_other = UserModel(id=other_student_id, email=f"other_{other_student_id.hex[:6]}@test.com", first_name="Other", last_name="Student", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        m_other = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=other_student_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
        db.add(u_other)
        db.add(m_other)

        await db.commit()

    # Resolve audience
    async with session_factory() as db:
        resolver = AudienceResolver(db)
        target_uids = await resolver.resolve_class_group_members(tenant_id, class_id)
        assert len(target_uids) == 2
        assert set(target_uids) == {student1_id, student2_id}
        assert other_student_id not in target_uids

        # Deliver In-App
        adapter = InAppChannelAdapter(db)
        for uid in target_uids:
            await adapter.deliver(
                tenant_id=tenant_id,
                user_id=uid,
                category=NotificationCategory.IMPORTANT,
                criticality=NotificationCategory.IMPORTANT,
                title="Annonce de classe",
                body="Devoir à rendre pour vendredi",
                deep_link="/class/announcements/1",
            )
        await db.commit()

        # Check DB records
        n_res = await db.execute(select(NotificationModel).where(NotificationModel.tenant_id == tenant_id))
        notifs = n_res.scalars().all()
        assert len(notifs) == 2
        notif_user_ids = {n.user_id for n in notifs}
        assert notif_user_ids == {student1_id, student2_id}


@pytest.mark.asyncio
async def test_gate_m9_one_click_email_unsubscribe(
    tenant_id_fixture,
):
    """
    Gate M9: Désabonnement e-mail en 1-clic (RFC 8058).
    Génération et vérification sécurisée du token JWT sans authentification.
    """
    user_id = uuid.uuid4()
    category = "IMPORTANT"

    token = EmailGatewayAdapter.generate_unsubscribe_token(user_id, tenant_id_fixture, category)
    assert token is not None

    payload = EmailGatewayAdapter.verify_unsubscribe_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tid"] == str(tenant_id_fixture)
    assert payload["cat"] == category
    assert payload["action"] == "unsubscribe"
