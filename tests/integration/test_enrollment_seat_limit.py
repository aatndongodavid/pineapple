# tests/integration/test_enrollment_seat_limit.py
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from identity_context.infrastructure.persistence.models import (
    TenantModel,
    TenantSubscriptionModel,
    RosterEntryModel,
    MembershipModel,
    UserModel,
)
from shared_kernel.infrastructure.encryption import normalize_matricule, normalize_text

@pytest.mark.asyncio
async def test_sec_002_claim_fails_when_seats_limit_exceeded(async_db_session, async_client):
    """SEC-002: Le rattachement doit être refusé avec 403 SEAT_LIMIT_EXCEEDED si le quota de sièges est atteint."""
    tenant_id = uuid.uuid4()
    code_suffix = uuid.uuid4().hex[:6]
    
    # 1. Créer l'établissement avec 1 seul siège autorisé
    tenant = TenantModel(
        id=tenant_id,
        name="École Test Quota",
        code=f"ETQ-{code_suffix}",
        enrollment_mode="BOTH",
        auto_approve_claims=True,
        current_academic_year="2026-2027",
        is_active=True,
    )
    async_db_session.add(tenant)
    
    sub = TenantSubscriptionModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        plan="STANDARD",
        status="ACTIVE",
        seats_limit=1,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    async_db_session.add(sub)
    
    # 2. Créer 1 membre déjà actif (quota atteint : 1 / 1)
    user_1 = UserModel(
        id=uuid.uuid4(),
        email=f"existing_{code_suffix}@test.com",
        hashed_password="hash",
        first_name="Jean",
        last_name="Dupont",
        account_status="ACTIVE",
    )
    async_db_session.add(user_1)
    
    member_1 = MembershipModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_1.id,
        role="STUDENT",
        status="ACTIVE",
        joined_via="CLAIM",
        academic_year="2026-2027",
    )
    async_db_session.add(member_1)
    
    # 3. Créer un nouvel étudiant dans le registre
    matricule_raw = f"24X{code_suffix}"
    roster_2 = RosterEntryModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        matricule=matricule_raw,
        last_name="KOUAM",
        first_name="Paul",
        birth_date="2003-05-12",
        birth_place="Douala",
        norm_matricule=normalize_matricule(matricule_raw),
        norm_last_name=normalize_text("KOUAM"),
        norm_first_name=normalize_text("Paul"),
        norm_birth_date="2003-05-12",
        norm_birth_place=normalize_text("Douala"),
        academic_year="2026-2027",
        status="NOT_CLAIMED",
    )
    async_db_session.add(roster_2)
    
    # Créer le compte utilisateur du 2ème étudiant
    user_2 = UserModel(
        id=uuid.uuid4(),
        email=f"paul_{code_suffix}@test.com",
        hashed_password="hash",
        first_name="Paul",
        last_name="Kouam",
        account_status="ACTIVE",
    )
    async_db_session.add(user_2)
    await async_db_session.commit()
    
    # Générer le token pour user_2
    from shared_kernel.infrastructure.security import create_jwt_token
    token_2 = create_jwt_token(user_id=user_2.id, role="VISITOR")
    
    headers = {"Authorization": f"Bearer {token_2}"}
    payload = {
        "tenant_id": str(tenant_id),
        "matricule": matricule_raw,
        "first_name": "Paul",
        "last_name": "Kouam",
        "birth_date": "2003-05-12",
        "birth_place": "Douala",
    }
    
    response = await async_client.post("/api/v1/enrollment/claim", json=payload, headers=headers)
    
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SEAT_LIMIT_EXCEEDED"
