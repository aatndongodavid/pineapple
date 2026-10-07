# tests/unit/test_notification_preferences_and_digest.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel, TenantModel
from identity_context.domain.value_objects import AccountStatus
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel
from notification_context.infrastructure.persistence.models import (
    NotificationPreferenceModel, QuietHoursModel, ChannelQuotaModel
)
from notification_context.domain.services.preference_engine import PreferenceEngine
from notification_context.domain.services.deduplication_engine import DeduplicationEngine


@pytest.mark.asyncio
async def test_gate_m2_disabled_preference_skips_delivery(
    session_factory,
    tenant_id_fixture,
):
    """
    Gate M2: Si un utilisateur désactive un canal pour une catégorie,
    should_deliver renvoie (False, "DISABLED_BY_USER").
    """
    user_id = uuid.uuid4()
    async with session_factory() as db:
        pref = NotificationPreferenceModel(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id_fixture,
            category="IMPORTANT",
            channel="PUSH",
            is_enabled=False,
        )
        db.add(pref)
        await db.commit()

        engine = PreferenceEngine(db)
        allowed, reason = await engine.should_deliver(
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            category=NotificationCategory.IMPORTANT,
            criticality=NotificationCategory.IMPORTANT,
            channel=NotificationChannel.PUSH,
        )
        assert allowed is False
        assert reason == "DISABLED_BY_USER"


@pytest.mark.asyncio
async def test_gate_m3_quiet_hours_defers_important_and_allows_critical(
    session_factory,
    tenant_id_fixture,
):
    """
    Gate M3: Les heures calmes (ex: 21h-6h) bloquent les notifications IMPORTANT/INFO
    mais laissent passer les notifications CRITICAL.
    """
    user_id = uuid.uuid4()
    async with session_factory() as db:
        qh = QuietHoursModel(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id_fixture,
            start_hour=21,
            end_hour=6,
            is_enabled=True,
        )
        db.add(qh)
        await db.commit()

        engine = PreferenceEngine(db)
        # Test à 23h00 (pendant les heures calmes)
        dt_23h = datetime(2026, 10, 8, 23, 0, tzinfo=timezone.utc)

        # IMPORTANT -> bloqué
        allowed_imp, reason_imp = await engine.should_deliver(
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            category=NotificationCategory.IMPORTANT,
            criticality=NotificationCategory.IMPORTANT,
            channel=NotificationChannel.IN_APP,
            current_dt=dt_23h,
        )
        assert allowed_imp is False
        assert reason_imp == "QUIET_HOURS"

        # CRITICAL -> autorisé malgré les heures calmes
        allowed_crit, reason_crit = await engine.should_deliver(
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            category=NotificationCategory.CRITICAL,
            criticality=NotificationCategory.CRITICAL,
            channel=NotificationChannel.IN_APP,
            current_dt=dt_23h,
        )
        assert allowed_crit is True
        assert reason_crit is None


@pytest.mark.asyncio
async def test_gate_m6_sms_quota_exceeded_skips_sms(
    session_factory,
):
    """
    Gate M6: Si le quota SMS de l'établissement est dépassé, should_deliver renvoie (False, "QUOTA_EXCEEDED").
    """
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    async with session_factory() as db:
        user = UserModel(
            id=user_id,
            email=f"quota_user_{uuid.uuid4().hex[:6]}@test.com",
            first_name="Test",
            last_name="Quota",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(user)

        quota = ChannelQuotaModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            channel="SMS",
            period="MONTHLY",
            max_limit=10,
            current_usage=10,  # Quota atteint
        )
        db.add(quota)
        await db.commit()

        engine = PreferenceEngine(db)
        allowed, reason = await engine.should_deliver(
            tenant_id=tenant_id,
            user_id=user_id,
            category=NotificationCategory.CRITICAL,
            criticality=NotificationCategory.CRITICAL,
            channel=NotificationChannel.SMS,
        )
        assert allowed is False
        assert reason == "QUOTA_EXCEEDED"


@pytest.mark.asyncio
async def test_gate_m10_deduplication_and_digest(
    session_factory,
    tenant_id_fixture,
):
    """
    Gate M10: Clé de déduplication et regroupement digest pour notifications répétitives.
    """
    user_id = uuid.uuid4()
    dedup_key = DeduplicationEngine.compute_dedup_key("CLASS_ANNOUNCEMENT_PUBLISHED", user_id, NotificationChannel.IN_APP)
    assert f"CLASS_ANNOUNCEMENT_PUBLISHED:{user_id}:IN_APP" in dedup_key

    title, body = DeduplicationEngine.digest_messages("CLASS_ANNOUNCEMENT_PUBLISHED", 10, "Examen de maths")
    assert "10 nouvelles annonces" in title
    assert "Examen de maths" in body
