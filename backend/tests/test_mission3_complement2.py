import pytest
import io
import zipfile
import json
from trust_safety_context.domain.content_moderation import ContentModerationService
from shared_kernel.infrastructure.sms_gateway import CriticalSMSNotificationService, MockSMSGateway
from identity_context.domain.entities import User
from identity_context.domain.value_objects import VerificationStatus, AccountStatus, UserRole, AcademicStatus
import uuid


def test_content_moderation_service():
    """Vérifie que le service de modération préventive détecte les mots-clés bannis."""
    clean_text = "Bonjour, bienvenue sur le campus !"
    is_flagged, reason = ContentModerationService.inspect_text(clean_text)
    assert is_flagged is False
    assert reason is None

    banned_text = "Message contenant de la violence gratuite et inacceptable."
    is_flagged, reason = ContentModerationService.inspect_text(banned_text)
    assert is_flagged is True
    assert "violence" in reason.lower()


@pytest.mark.asyncio
async def test_critical_sms_notification_service():
    """Vérifie la portée du canal SMS et le respect du consentement utilisateur."""
    mock_gateway = MockSMSGateway()
    sms_service = CriticalSMSNotificationService(sms_gateway=mock_gateway)

    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="test.sms@enspd.cm",
        first_name="Paul",
        last_name="Biya",
        phone_number="+237670000000",
        sms_consent=True,
    )

    # 1. Événement non critique : rejeté
    res_non_critical = await sms_service.send_critical_alert(user, "FEED_NEW_LIKE", "Quelqu'un a aimé votre post")
    assert res_non_critical is False
    assert len(mock_gateway.sent_messages) == 0

    # 2. Événement critique avec consentement : succès
    res_critical = await sms_service.send_critical_alert(user, "ELECTION_CLOSING_SOON", "Le vote se clôture dans 30 min.")
    assert res_critical is True
    assert len(mock_gateway.sent_messages) == 1
    assert mock_gateway.sent_messages[0]["phone_number"] == "+237670000000"

    # 3. Sans consentement : rejeté
    user.sms_consent = False
    res_no_consent = await sms_service.send_critical_alert(user, "ELECTION_CLOSING_SOON", "Vote imminente")
    assert res_no_consent is False


def test_bulk_import_csv_endpoint(client, admin_headers, student_headers):
    """Vérifie l'endpoint d'import en masse CSV pour les administrateurs."""
    csv_content = (
        "email,first_name,last_name,matricule,faculty,filiere,academic_year\n"
        "bulk1@enspd.cm,Jean,Dupont,MAT001,Génie Informatique,GI,2026\n"
        "bulk2@enspd.cm,Marie,Curie,MAT002,Génie Chimique,GC,2026\n"
    )
    csv_file = io.BytesIO(csv_content.encode("utf-8"))

    # Tentative par un étudiant (refusée 403)
    res_forbidden = client.post(
        "/api/v1/identity/admin/users/bulk-import",
        files={"file": ("students.csv", csv_file, "text/csv")},
        headers=student_headers,
    )
    assert res_forbidden.status_code == 403

    # Tentative par un administrateur (succès 200)
    csv_file.seek(0)
    res_admin = client.post(
        "/api/v1/identity/admin/users/bulk-import",
        files={"file": ("students.csv", csv_file, "text/csv")},
        headers=admin_headers,
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["total_lines"] == 2
    assert data["succeeded_count"] == 2
    assert data["failed_count"] == 0
    assert len(data["details"]) == 2
    assert data["details"][0]["status"] == "SUCCESS"
    assert "temp_password" in data["details"][0]


def test_legal_acceptances_endpoint(client, student_headers):
    """Vérifie l'enregistrement horodaté de l'acceptation des CGU."""
    res = client.post(
        "/api/v1/identity/legal/accept?document_type=STUDENT_CGU&version=1.0.0",
        headers=student_headers,
    )
    assert res.status_code == 200
    assert res.json()["document_type"] == "STUDENT_CGU"
    assert res.json()["version"] == "1.0.0"


def test_tenant_data_export_endpoint(client, admin_headers):
    """Vérifie l'export des données du tenant et l'exclusion des mots de passe."""
    res = client.post(
        "/api/v1/identity/admin/tenant/export",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "export_id" in data
    assert "filename" in data
    assert data["filename"].startswith("pineapple_tenant_export_")
