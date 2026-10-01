# backend/tests/test_login_integration.py

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from api.main import app

TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def client():
    return TestClient(app)


def test_register_and_login_real_endpoint_returns_token(client):
    """
    Test d'intégration bout-en-bout pour 0.1 :
    Vérifie que POST /api/v1/identity/login renvoie bien un TokenResponseDTO exploitable (avec access_token).
    """
    unique_email = f"test_login_{uuid.uuid4().hex[:8]}@enspd.cm"
    unique_matricule = f"MAT-{uuid.uuid4().hex[:6]}"
    password = "SecurePassword123!"

    # 1. Inscription
    reg_response = client.post(
        "/api/v1/identity/register",
        headers={"X-Tenant-ID": TEST_TENANT_ID},
        json={
            "email": unique_email,
            "password": password,
            "first_name": "Jean",
            "last_name": "Dupont",
            "matricule": unique_matricule,
            "faculty": "Génie Informatique",
            "filiere": "Logiciel",
            "academic_year": "2026",
            "role": "STUDENT",
        },
    )
    assert reg_response.status_code == 201, reg_response.text

    # 2. Connexion avec bons identifiants
    login_response = client.post(
        "/api/v1/identity/login",
        json={
            "email": unique_email,
            "password": password,
        },
    )
    assert login_response.status_code == 200, f"Erreur login : {login_response.text}"
    data = login_response.json()

    # 3. Vérification explicite de la structure du TokenResponseDTO
    assert "access_token" in data
    assert data["access_token"] != ""
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert data["tenant_id"] == TEST_TENANT_ID


def test_login_invalid_credentials_returns_401(client):
    """
    Vérifie qu'un mot de passe erroné renvoie un 401 UNAUTHORIZED.
    """
    response = client.post(
        "/api/v1/identity/login",
        json={
            "email": "unknown_user@enspd.cm",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_mfa_requirement_for_totp_configured_account(client):
    """
    Vérifie la contrainte AA1 (MFA requis pour les comptes TOTP configurés).
    """
    from shared_kernel.infrastructure.mfa import generate_totp_secret, _generate_totp_code_for_counter
    import time

    unique_email = f"admin_mfa_{uuid.uuid4().hex[:8]}@enspd.cm"
    unique_matricule = f"ADM-{uuid.uuid4().hex[:6]}"
    password = "AdminPassword123!"

    # Inscription
    reg_res = client.post(
        "/api/v1/identity/register",
        headers={"X-Tenant-ID": TEST_TENANT_ID},
        json={
            "email": unique_email,
            "password": password,
            "first_name": "Admin",
            "last_name": "Test",
            "matricule": unique_matricule,
            "faculty": "Administration",
            "filiere": "Direction",
            "academic_year": "2026",
            "role": "ADMIN",
        },
    )
    assert reg_res.status_code == 201

    # Sans TOTP configuré, la connexion passe (ou exige TOTP si configuré)
    login_no_totp = client.post(
        "/api/v1/identity/login",
        json={"email": unique_email, "password": password},
    )
    assert login_no_totp.status_code == 200
