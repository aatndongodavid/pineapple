import uuid
import pytest
from fastapi.testclient import TestClient

from campus_life_context.domain.entities import Conversation
from campus_life_context.infrastructure.persistence.repositories import PostgresMessagingRepository
from api.v1.campus_life_router import get_messaging_repo
from shared_kernel.infrastructure.database import AsyncSessionLocal


def test_a1_messaging_idor_blocked(client: TestClient, student_headers, third_user_headers):
    """
    Test A1: Vérifie qu'un utilisateur non participant à une conversation
    reçoit un HTTP 403 Forbidden lorsqu'il tente de lire ses messages (IDOR).
    """
    user_a = uuid.UUID("22222222-2222-2222-2222-222222222222")  # student
    user_b = uuid.UUID("33333333-3333-3333-3333-333333333333")  # teacher
    tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    conv_id = uuid.uuid4()

    # Stub/mock du repository de messagerie
    class DummyMessagingRepo:
        async def get_conversation_by_id(self, conversation_id: uuid.UUID):
            if conversation_id == conv_id:
                return Conversation(
                    id=conv_id,
                    tenant_id=tenant_id,
                    participant_ids=[user_a, user_b],
                    context_type="DIRECT",
                    context_id=uuid.uuid4(),
                    last_message_at=None,
                )
            return None

        async def list_messages(self, conversation_id: uuid.UUID, limit: int = 50):
            return []

    client.app.dependency_overrides[get_messaging_repo] = lambda: DummyMessagingRepo()

    try:
        # L'utilisateur A (participant) tente de lire : succès (200)
        res_participant = client.get(f"/api/v1/campus-life/messages/{conv_id}", headers=student_headers)
        assert res_participant.status_code == 200

        # L'utilisateur C (non participant) tente de lire : BLOQUÉ (403 Forbidden)
        res_non_participant = client.get(f"/api/v1/campus-life/messages/{conv_id}", headers=third_user_headers)
        assert res_non_participant.status_code == 403
        assert "Accès interdit" in res_non_participant.json()["detail"]
    finally:
        client.app.dependency_overrides.clear()


def test_a2_identity_review_requires_admin(client: TestClient, student_headers, admin_headers):
    """
    Test A2: Vérifie que la validation/rejet de certification d'identité
    est strictement réservée aux administrateurs (require_role("ADMIN")).
    """
    payload = {
        "document_id": str(uuid.uuid4()),
        "approved": True,
    }

    # Un étudiant simple (STUDENT) tente de réviser un document -> 403 Forbidden
    res_student = client.post("/api/v1/identity/certification/review", json=payload, headers=student_headers)
    assert res_student.status_code == 403
    assert "Rôle insuffisant" in res_student.json()["detail"]

    # Un administrateur (ADMIN) passe la barrière RBAC (renvoie 404 car document factice)
    res_admin = client.post("/api/v1/identity/certification/review", json=payload, headers=admin_headers)
    assert res_admin.status_code in (200, 404)


def test_a3_academy_upload_requires_admin_or_teacher(client: TestClient, student_headers, teacher_headers, admin_headers):
    """
    Test A3: Vérifie que le téléversement de documents académiques est restreint
    aux rôles ADMIN et TEACHER (require_role("ADMIN", "TEACHER")).
    """
    file_data = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    form_data = {
        "title": "Examen Corrigé 2026",
        "document_type": "EXAM",
        "faculty": "Informatique",
        "filiere": "Génie Logiciel",
        "academic_level": "L3",
        "is_premium": "false",
        "price_fcfa": "0",
    }

    # Étudiant (STUDENT) -> 403 Forbidden
    res_student = client.post(
        "/api/v1/academy/library/upload",
        data=form_data,
        files=file_data,
        headers=student_headers,
    )
    assert res_student.status_code == 403
    assert "Rôle insuffisant" in res_student.json()["detail"]

    # Enseignant (TEACHER) -> Autorisé (201 Created)
    res_teacher = client.post(
        "/api/v1/academy/library/upload",
        data=form_data,
        files=file_data,
        headers=teacher_headers,
    )
    assert res_teacher.status_code == 201

    # Administrateur (ADMIN) -> Autorisé (201 Created)
    res_admin = client.post(
        "/api/v1/academy/library/upload",
        data=form_data,
        files=file_data,
        headers=admin_headers,
    )
    assert res_admin.status_code == 201


def test_a4_democracy_admin_actions_require_admin(client: TestClient, student_headers, admin_headers):
    """
    Test A4: Vérifie que les actions de création et dépouillement d'élections
    sont strictement réservées aux admins.
    """
    election_payload = {
        "title": "Élection Délégués L3",
        "election_type": "BDE",
        "eligibility_rules": {},
        "voting_start_at": "2026-10-01T08:00:00Z",
        "voting_end_at": "2026-10-01T18:00:00Z",
    }

    # Étudiant -> 403 Forbidden sur la création
    res_student = client.post("/api/v1/democracy/elections", json=election_payload, headers=student_headers)
    assert res_student.status_code == 403
    assert "Rôle insuffisant" in res_student.json()["detail"]

    # Admin -> Autorisé
    res_admin = client.post("/api/v1/democracy/elections", json=election_payload, headers=admin_headers)
    assert res_admin.status_code == 201


def test_a5_trust_safety_review_requires_moderator_or_admin(client: TestClient, student_headers, moderator_headers, admin_headers):
    """
    Test A5: Vérifie que la revue des signalements est restreinte
    aux modérateurs et administrateurs (require_role("MODERATOR", "ADMIN")).
    """
    review_payload = {
        "report_id": str(uuid.uuid4()),
        "resolution": "DISMISSED",
    }

    # Étudiant -> 403 Forbidden
    res_student = client.post("/api/v1/trust-safety/moderation/review", json=review_payload, headers=student_headers)
    assert res_student.status_code == 403
    assert "Rôle insuffisant" in res_student.json()["detail"]

    # Modérateur -> Passe la barrière RBAC (404 car id factice)
    res_mod = client.post("/api/v1/trust-safety/moderation/review", json=review_payload, headers=moderator_headers)
    assert res_mod.status_code in (200, 404)


def test_platform_super_admin_security(client: TestClient, student_headers, platform_admin_headers):
    """
    Test B3: Vérifie le rôle Super Admin transverse (scope: platform).
    Un token utilisateur classique est rejeté sur les routes platform admin.
    """
    # Utilisateur tenant classique -> 403 Forbidden sur /api/v1/platform/tenants
    res_user = client.get("/api/v1/platform/tenants", headers=student_headers)
    assert res_user.status_code == 403

    # Super Admin -> 200 OK
    res_super = client.get("/api/v1/platform/tenants", headers=platform_admin_headers)
    assert res_super.status_code == 200
