# tests/unit/test_timetable_import.py

import uuid
from datetime import date
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
from shared_kernel.config import settings
from jose import jwt


from sqlalchemy import select
from shared_kernel.infrastructure.security import create_jwt_token
from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel, ClassGroupModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus


@pytest.mark.asyncio
async def test_gate_e4_csv_import_dry_run_lists_conflicts_and_valid_rows(
    async_client: AsyncClient,
    session_factory,
    tenant_id_fixture,
    auth_headers_fixture,
):
    """
    Gate E4: Import CSV avec dry-run.
    Le dry-run liste les erreurs sans insérer; puis l'importation filtre les lignes valides.
    """
    user_id = uuid.uuid4()

    # Seed Tenant, Admin User & Membership in DB
    async with session_factory() as db:
        tenant = (await db.execute(select(TenantModel).where(TenantModel.id == tenant_id_fixture))).scalars().first()
        if not tenant:
            tenant = TenantModel(id=tenant_id_fixture, name="École Test", code="ENSPD", is_active=True)
            db.add(tenant)

        unique_email = f"admin.timetable_{uuid.uuid4().hex[:6]}@test.com"
        admin_user = UserModel(
            id=user_id,
            email=unique_email,
            first_name="Admin",
            last_name="Test",
            hashed_password="hash",
            account_status=AccountStatus.ACTIVE,
        )
        db.add(admin_user)

        membership = MembershipModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id_fixture,
            user_id=user_id,
            role=MembershipRole.TENANT_ADMIN,
            status=MembershipStatus.ACTIVE,
            academic_year="2026-2027",
        )
        db.add(membership)

        # Also seed class GIT3 and room AMPHI A for CSV matching
        existing_cls = (await db.execute(select(ClassGroupModel).where(ClassGroupModel.code == "GIT3"))).scalars().first()
        if not existing_cls:
            cls_grp = ClassGroupModel(id=uuid.uuid4(), tenant_id=tenant_id_fixture, name="Génie Informatique 3", code="GIT3", academic_year="2026-2027")
            db.add(cls_grp)

        from community_context.infrastructure.persistence.models import RoomModel
        existing_room = (await db.execute(select(RoomModel).where(RoomModel.name == "AMPHI A"))).scalars().first()
        if not existing_room:
            room = RoomModel(id=uuid.uuid4(), tenant_id=tenant_id_fixture, name="AMPHI A", capacity=100)
            db.add(room)

        await db.commit()

    token = create_jwt_token(user_id=user_id, tenant_id=tenant_id_fixture, membership_id=membership.id, role="TENANT_ADMIN")
    admin_headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id_fixture),
    }

    # 2. Créer un semestre
    term_resp = await async_client.post(
        "/api/v1/timetable/terms",
        headers=admin_headers,
        json={
            "name": "Semestre 1 2026-2027",
            "academic_year": "2026-2027",
            "start_date": "2026-10-01",
            "end_date": "2027-02-28",
            "is_active": True,
        },
    )
    assert term_resp.status_code == 210 or term_resp.status_code == 201
    term_id = term_resp.json()["id"]

    # 3. Créer des entités préalables (Matière, Classe, Salle)
    sub_resp = await async_client.post(
        "/api/v1/timetable/subjects",
        headers=admin_headers,
        json={"code": "INF301", "name": "Algorithmique", "credits": 4},
    )
    assert sub_resp.status_code == 201

    # Test download CSV template
    tmpl_resp = await async_client.get("/api/v1/timetable/import/template", headers=admin_headers)
    assert tmpl_resp.status_code == 200
    assert "code_matiere,code_classe" in tmpl_resp.text

    # CSV Payload avec 1 ligne valide (INF301/GIT3/Amphi A) et 2 lignes erronées (Matière inconnue INEXISTANTE, Salle inconnue INEXISTANTE)
    csv_content = """code_matiere,code_classe,jour,heure_debut,heure_fin,salle,prof_email
INF301,GIT3,0,08:00,10:00,AMPHI A,prof@test.com
INEXISTANTE,GIT3,1,10:00,12:00,AMPHI A,prof@test.com
INF301,GIT3,2,14:00,16:00,SALLE_FANTOME,prof@test.com
"""

    files = {"file": ("timetable.csv", csv_content.encode("utf-8"), "text/csv")}

    # 4. Dry-run execution
    dry_resp = await async_client.post(
        f"/api/v1/timetable/import/csv?dry_run=true&term_id={term_id}",
        headers=admin_headers,
        files=files,
    )
    assert dry_resp.status_code == 200
    dry_data = dry_resp.json()
    assert dry_data["dry_run"] is True
    assert dry_data["total_rows"] == 3
    assert dry_data["conflict_count"] == 2  # 2 rows with errors
    assert len(dry_data["errors"]) == 2
