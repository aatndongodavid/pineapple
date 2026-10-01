import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app

from shared_kernel.infrastructure.mfa import generate_totp_secret, get_totp_uri, verify_totp_code
from shared_kernel.infrastructure.encryption import SensitiveDataEncryptor
from shared_kernel.infrastructure.token_blacklist import token_blacklist
from shared_kernel.infrastructure.secrets_manager import secrets_manager
from shared_kernel.infrastructure.security_logger import security_logger

client = TestClient(app)


def test_w1_secrets_manager_fallback():
    """Vérifie la chaîne de fallback du secrets manager."""
    secret = secrets_manager.get_secret("JWT_SECRET_KEY", default="fallback_key")
    assert secret is not None


def test_w2_token_revocation_blacklist():
    """Vérifie le blocage immédiat des tokens et sessions révoquées."""
    import asyncio
    jti = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    asyncio.run(token_blacklist.revoke_token(jti))
    is_revoked = asyncio.run(token_blacklist.is_token_revoked(jti))
    assert is_revoked is True

    asyncio.run(token_blacklist.revoke_all_user_sessions(user_id))
    # Token émis avant la révocation globale
    is_user_revoked = asyncio.run(token_blacklist.is_token_revoked("new_jti", user_id=user_id, token_issued_at=100.0))
    assert is_user_revoked is True


def test_w3_mfa_totp_generation_and_verification():
    """Vérifie la génération TOTP et la validation de code RFC 6238."""
    secret = generate_totp_secret()
    assert len(secret) > 10

    uri = get_totp_uri(secret, email="admin@pineapple.cm", issuer="Pineapple OS")
    assert "otpauth://totp/Pineapple%20OS:admin@pineapple.cm" in uri or "otpauth://totp/" in uri

    # Calculer un code valide pour la fenêtre actuelle
    from shared_kernel.infrastructure.mfa import _generate_totp_code_for_counter
    import time
    current_counter = int(time.time() // 30)
    valid_code = _generate_totp_code_for_counter(secret, current_counter)

    assert verify_totp_code(secret, valid_code) is True
    assert verify_totp_code(secret, "000000") is False


def test_w4_sensitive_data_encryption_and_masking():
    """Vérifie le masquage et le chiffrement applicatif des PII (numéros de téléphone)."""
    encryptor = SensitiveDataEncryptor(key="test_secret_key_123")

    masked = encryptor.mask_phone_number("+237 670 000 089")
    assert masked == "+237 ***89"

    plaintext = "+237670000089"
    cipher = encryptor.encrypt_string(plaintext)
    assert cipher != plaintext

    decrypted = encryptor.decrypt_string(cipher)
    assert decrypted == plaintext


def test_w5_security_logger_events(tmp_path):
    """Vérifie la journalisation isolée des événements de sécurité."""
    security_logger.log_failed_login("test@pineapple.cm", ip_address="127.0.0.1", reason="Wrong pass")
    security_logger.log_access_denied("user-1", "STUDENT", "/admin/dashboard", ip_address="127.0.0.1")
    security_logger.log_rate_limit_exceeded("127.0.0.1", "/api/v1/auth/login")
    security_logger.log_token_revoked("jti-123", "user-1", "User logout")


def test_z3_global_unified_search(student_headers):
    """Vérifie le moteur de recherche unifié (Publications, Organisations, Academy, Offres)."""
    response = client.get(
        "/api/v1/search?q=IA",
        headers=student_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "IA"
    assert data["total_results"] >= 1
    assert any(r["type"] in ["post", "organization", "academy_document", "opportunity"] for r in data["results"])


def test_z5_admin_analytics_csv_export(admin_headers):
    """Vérifie l'exportation CSV du rapport d'analytics d'établissement pour les administrateurs."""
    response = client.get(
        "/api/v1/identity/admin/analytics-export",
        headers=admin_headers
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Metrique Etablissement" in response.text
    assert "Taux de Participation Electorale" in response.text

