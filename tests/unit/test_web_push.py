# tests/unit/test_web_push.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel, TenantModel
from identity_context.domain.value_objects import AccountStatus
from notification_context.infrastructure.persistence.models import PushSubscriptionModel
from notification_context.infrastructure.adapters.web_push_channel import WebPushChannelAdapter


@pytest.mark.asyncio
async def test_gate_m7_web_push_410_gone_auto_revokes_subscription(
    session_factory,
    tenant_id_fixture,
):
    """
    Gate M7: Abonnement push expiré (HTTP 410 Gone).
    Vérifie la désactivation automatique de l'abonnement en BDD sans erreur répétée.
    """
    user_id = uuid.uuid4()
    endpoint_uri = f"https://updates.push.services.mozilla.com/wpush/v2/{uuid.uuid4().hex}"

    async with session_factory() as db:
        user = UserModel(
            id=user_id,
            email=f"push_user_{uuid.uuid4().hex[:6]}@test.com",
            first_name="Push",
            last_name="Tester",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(user)

        sub = PushSubscriptionModel(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id_fixture,
            endpoint=endpoint_uri,
            p256dh="mock_p256dh_key",
            auth="mock_auth_token",
            user_agent="Mozilla/5.0 (Android; Mobile)",
            is_active=True,
        )
        db.add(sub)
        await db.commit()

    # Deliver push with mock HTTP 410 Gone status
    async with session_factory() as db:
        adapter = WebPushChannelAdapter(db)
        sent, revoked, errors = await adapter.deliver_push(
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            title="Avis de cours",
            body="Le cours commence dans 15 min",
            mock_http_status=410,
        )
        await db.commit()

        assert sent == 0
        assert revoked == 1
        assert any("410 Gone" in err for err in errors)

        # Check DB status
        db_sub = (await db.execute(select(PushSubscriptionModel).where(PushSubscriptionModel.endpoint == endpoint_uri))).scalars().first()
        assert db_sub.is_active is False
        assert db_sub.revoked_at is not None

    # Subsequent push call should immediately skip deactivated subscription
    async with session_factory() as db:
        adapter = WebPushChannelAdapter(db)
        sent2, revoked2, errors2 = await adapter.deliver_push(
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            title="Seconde alerte",
            body="Test",
        )
        assert sent2 == 0
        assert revoked2 == 0
        assert errors2 == ["NO_ACTIVE_PUSH_SUBSCRIPTION"]
