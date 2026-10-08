# tests/unit/test_affiliation_and_subscription_flow.py

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException

from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    enforce_demo_tenant_safety_lock,
    require_membership,
    require_permission,
    ROLE_PERMISSIONS_MAP,
)


def test_ac1_ac2_student_free_registration_unaffiliated_has_visitor_role():
    """Critère 1 & 2 : Un étudiant peut s'inscrire librement. Sans affiliation, il est Visiteur sans accès aux contenus universitaires."""
    user_id = uuid.uuid4()
    context = AuthenticatedUserContext(
        user_id=user_id,
        user_type="STUDENT",
        email="unaffiliated@student.cm",
        first_name="Jean",
        last_name="Eboa",
        tenant_id=None,
        membership_id=None,
        class_group_id=None,
        role="VISITOR",
        permissions=ROLE_PERMISSIONS_MAP["VISITOR"],
        delegate_of=[],
        subscription_status="NONE",
    )

    assert context.role == "VISITOR"
    assert context.tenant_id is None
    assert context.can("room.view") is False
    assert context.can("feed.view_school") is False
    assert context.can("feed.view_ads") is True  # Fil visiteur uniquement


@pytest.mark.asyncio
async def test_ac3_ac4_unaffiliated_student_cannot_access_university_resources():
    """Critère 3 & 4 : Tentative d'accès d'un étudiant non affilié rejetée avec code SCHOOL_MEMBERSHIP_REQUIRED."""
    unaffiliated_ctx = AuthenticatedUserContext(
        user_id=uuid.uuid4(),
        user_type="STUDENT",
        email="unaffiliated@student.cm",
        first_name="Jean",
        last_name="Eboa",
        tenant_id=None,
        membership_id=None,
        class_group_id=None,
        role="VISITOR",
        permissions=ROLE_PERMISSIONS_MAP["VISITOR"],
        delegate_of=[],
        subscription_status="NONE",
    )

    dependency = require_membership()
    with pytest.raises(HTTPException) as exc_info:
        await dependency(unaffiliated_ctx)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "SCHOOL_MEMBERSHIP_REQUIRED"


def test_ac6_ac7_approved_affiliation_grants_access_to_university_services():
    """Critère 6 & 7 : Dès qu'une affiliation est validée, l'étudiant accède aux actualités et services de l'université."""
    tenant_id = uuid.uuid4()
    student_ctx = AuthenticatedUserContext(
        user_id=uuid.uuid4(),
        user_type="STUDENT",
        email="approved@enspd.cm",
        first_name="Marie",
        last_name="Mbida",
        tenant_id=tenant_id,
        membership_id=uuid.uuid4(),
        class_group_id=uuid.uuid4(),
        role="STUDENT",
        permissions=ROLE_PERMISSIONS_MAP["STUDENT"],
        delegate_of=[],
        subscription_status="ACTIVE",
    )

    assert student_ctx.role == "STUDENT"
    assert student_ctx.tenant_id == tenant_id
    assert student_ctx.can("room.view") is True
    assert student_ctx.can("feed.view_school") is True
    assert student_ctx.can("democracy.vote") is True


@pytest.mark.asyncio
async def test_ac9_expired_subscription_forces_read_only_mode():
    """Critère 9 : Si l'abonnement de l'université expire, les actions de modification sont bloquées (lecture seule)."""
    expired_ctx = AuthenticatedUserContext(
        user_id=uuid.uuid4(),
        user_type="STUDENT",
        email="student@expired.cm",
        first_name="Paul",
        last_name="Bassi",
        tenant_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        class_group_id=uuid.uuid4(),
        role="STUDENT",
        permissions=ROLE_PERMISSIONS_MAP["STUDENT"],
        delegate_of=[],
        subscription_status="EXPIRED",
    )

    # La lecture (room.view) est autorisée
    read_dep = require_permission("room.view")
    res_ctx = await read_dep(expired_ctx)
    assert res_ctx.user_id == expired_ctx.user_id

    # La modification/action (feed.post) est bloquée
    post_dep = require_permission("feed.post")
    with pytest.raises(HTTPException) as exc_info:
        await post_dep(expired_ctx)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "SUBSCRIPTION_INACTIVE"


def test_ac10_super_admin_has_full_platform_governance():
    """Critère 10 : Le super-admin gère les universités, abonnements et accès globaux sur toute la plateforme."""
    super_admin_ctx = AuthenticatedUserContext(
        user_id=uuid.uuid4(),
        user_type="PLATFORM_ADMIN",
        email="superadmin@pineapple.cm",
        first_name="Super",
        last_name="Admin",
        tenant_id=None,
        membership_id=None,
        class_group_id=None,
        role="PLATFORM_SUPER_ADMIN",
        permissions=ROLE_PERMISSIONS_MAP["PLATFORM_SUPER_ADMIN"],
        delegate_of=[],
        subscription_status="ACTIVE",
    )

    assert super_admin_ctx.can("platform.tenant.manage") is True
    assert super_admin_ctx.can("admin.settings.manage") is True
    assert super_admin_ctx.can("anything") is True  # Super admin a tous les droits


def test_demo_tenant_safety_lock_prevents_sensitive_mutations():
    """Sécurité bac à sable : Vérification du verrou de sécurité sur l'établissement démo."""
    demo_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    with pytest.raises(HTTPException) as exc_info:
        enforce_demo_tenant_safety_lock(demo_tenant_id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "DEMO_SAFETY_LOCK"
