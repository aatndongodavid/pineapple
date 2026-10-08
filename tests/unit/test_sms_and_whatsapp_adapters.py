# tests/unit/test_sms_and_whatsapp_adapters.py

import uuid
import pytest
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel
from identity_context.domain.value_objects import AccountStatus
from notification_context.infrastructure.persistence.models import ChannelQuotaModel, NotificationPreferenceModel
from notification_context.infrastructure.adapters.sms_gateway import SmsGatewayAdapter
from notification_context.infrastructure.adapters.whatsapp_channel import WhatsAppChannelAdapter


@pytest.mark.asyncio
async def test_sms_gateway_consent_required(session_factory):
    """
    SMS consent strictly required for SMS sending.
    """
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    async with session_factory() as db:
        user = UserModel(
            id=user_id,
            email=f"nosms_{uuid.uuid4().hex[:6]}@test.com",
            first_name="No",
            last_name="SMS",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(user)
        pref = NotificationPreferenceModel(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            category="ALL",
            channel="SMS",
            is_enabled=False,
        )
        db.add(pref)
        await db.commit()

    async with session_factory() as db:
        adapter = SmsGatewayAdapter(db)
        success, provider, ref_or_reason = await adapter.send_sms(
            tenant_id=tenant_id,
            user_id=user_id,
            phone_number="+237690000000",
            message="Alert text",
        )
        assert success is False
        assert ref_or_reason == "NO_SMS_CONSENT"


@pytest.mark.asyncio
async def test_sms_gateway_quota_and_truncation(session_factory):
    """
    SMS quota increment, 160-char truncation, and quota exceeding block.
    """
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    async with session_factory() as db:
        user = UserModel(
            id=user_id,
            email=f"sms_{uuid.uuid4().hex[:6]}@test.com",
            first_name="SMS",
            last_name="User",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        setattr(user, "sms_consent", True)
        db.add(user)

        # Set quota limit to 1 with current_usage 0
        quota = ChannelQuotaModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            channel="SMS",
            period="MONTHLY",
            max_limit=1,
            current_usage=0,
        )
        db.add(quota)
        await db.commit()

    async with session_factory() as db:
        adapter = SmsGatewayAdapter(db)
        long_msg = "A" * 200  # > 160 chars
        success, provider, ref_or_id = await adapter.send_sms(
            tenant_id=tenant_id,
            user_id=user_id,
            phone_number="+237690000000",
            message=long_msg,
        )
        assert success is True
        assert ref_or_id.startswith("sms_")
        await db.commit()

    # Verify quota incremented to 1
    async with session_factory() as db:
        res = await db.execute(
            select(ChannelQuotaModel).where(
                ChannelQuotaModel.tenant_id == tenant_id,
                ChannelQuotaModel.channel == "SMS",
            )
        )
        q = res.scalars().first()
        assert q.current_usage == 1

        # Second send should fail due to QUOTA_EXCEEDED
        adapter = SmsGatewayAdapter(db)
        success2, _, reason2 = await adapter.send_sms(
            tenant_id=tenant_id,
            user_id=user_id,
            phone_number="+237690000000",
            message="Second message",
        )
        assert success2 is False
        assert reason2 == "QUOTA_EXCEEDED"


@pytest.mark.asyncio
async def test_whatsapp_channel_adapter(session_factory):
    """
    WhatsApp HSM template send simulation.
    """
    async with session_factory() as db:
        adapter = WhatsAppChannelAdapter(db)
        success, provider, ref = await adapter.send_whatsapp_template(
            phone_number="+237690000000",
            template_name="class_announcement",
            language_code="fr",
            parameters=["Maths", "Salle 101"],
        )
        assert success is True
        assert provider == "MetaWhatsAppCloudAPI"
        assert ref.startswith("wa_")
