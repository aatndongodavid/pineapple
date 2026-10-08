# tests/integration/test_token_revocation.py
import pytest
import uuid
from identity_context.infrastructure.persistence.models import UserModel
from shared_kernel.infrastructure.security import create_jwt_token, is_jti_blacklisted

@pytest.mark.asyncio
async def test_sec_001_revoke_token_blacklists_jwt(async_db_session, async_client):
    """SEC-001: La révocation de jeton doit invalider la session et bloquer tout appel ultérieur avec le même token."""
    email_str = f"revocation_test_{uuid.uuid4().hex[:8]}@test.com"
    user = UserModel(
        id=uuid.uuid4(),
        email=email_str,
        hashed_password="hash",
        first_name="Jean",
        last_name="Test",
        account_status="ACTIVE",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    
    token = create_jwt_token(user_id=user.id, role="VISITOR")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Vérifier que /me fonctionne avec le token valide
    resp_before = await async_client.get("/api/v1/identity/me", headers=headers)
    assert resp_before.status_code == 200
    
    # 2. Appeler /revoke-token pour révoquer le token
    resp_revoke = await async_client.post("/api/v1/identity/revoke-token", headers=headers)
    assert resp_revoke.status_code == 200
    assert resp_revoke.json()["status"] == "ok"
    
    # 3. Vérifier que /me renvoie maintenant 401 Unauthorized
    resp_after = await async_client.get("/api/v1/identity/me", headers=headers)
    assert resp_after.status_code == 401
    assert "révoqué" in resp_after.json()["detail"].lower() or "revoked" in resp_after.json()["detail"].lower()
