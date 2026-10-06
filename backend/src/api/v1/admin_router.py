import csv
import io
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from community_context.infrastructure.persistence.models import RoomModel
from identity_context.infrastructure.persistence.models import (
    ClassDelegateModel,
    ClassGroupModel,
    ImportBatchModel,
    InvitationModel,
    MembershipModel,
    RosterEntryModel,
    TenantModel,
    TenantSubscriptionModel,
    UserModel,
)
from shared_kernel.infrastructure.audit_log import AuditLogModel, log_audit_event
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.email_gateway import email_gateway
from shared_kernel.infrastructure.encryption import encrypt_field, normalize_matricule, normalize_text, sanitize_csv_cell
from shared_kernel.infrastructure.security import AuthenticatedUserContext, require_permission

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/admin", tags=["School Admin"])


# DTOs
class RosterEntryCreateDTO(BaseModel):
    matricule: str
    last_name: str
    first_name: str
    birth_date: str  # YYYY-MM-DD
    birth_place: str
    class_group_id: Optional[str] = None
    official_email: Optional[str] = None
    phone: Optional[str] = None


class ClassGroupCreateDTO(BaseModel):
    name: str
    code: str
    faculty: Optional[str] = None
    filiere: Optional[str] = None
    level: Optional[str] = None
    capacity: Optional[int] = None


class RoomCreateDTO(BaseModel):
    name: str
    building: Optional[str] = None
    capacity: Optional[int] = None


class DelegateAssignDTO(BaseModel):
    user_id: str
    kind: str = "TITULAIRE"  # TITULAIRE, SUPPLEANT


class TenantSettingsDTO(BaseModel):
    enrollment_mode: Optional[str] = None
    auto_approve_claims: Optional[bool] = None
    current_academic_year: Optional[str] = None
    timezone: Optional[str] = None


@router.get("/dashboard")
async def get_admin_dashboard(
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.settings.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Tableau de bord administrateur d'établissement."""
    tenant_id = ctx.tenant_id

    total_roster = (await db.execute(select(func.count(RosterEntryModel.id)).where(RosterEntryModel.tenant_id == tenant_id))).scalar() or 0
    total_active = (await db.execute(select(func.count(MembershipModel.id)).where(MembershipModel.tenant_id == tenant_id, MembershipModel.status == "ACTIVE"))).scalar() or 0
    total_pending = (await db.execute(select(func.count(MembershipModel.id)).where(MembershipModel.tenant_id == tenant_id, MembershipModel.status == "PENDING"))).scalar() or 0
    total_unclaimed = (await db.execute(select(func.count(RosterEntryModel.id)).where(RosterEntryModel.tenant_id == tenant_id, RosterEntryModel.status == "NOT_CLAIMED"))).scalar() or 0

    sub = (await db.execute(select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tenant_id))).scalars().first()

    return {
        "tenant_id": str(tenant_id),
        "total_roster": total_roster,
        "total_active_members": total_active,
        "total_pending_claims": total_pending,
        "total_unclaimed": total_unclaimed,
        "activation_rate": round((total_active / total_roster * 100), 1) if total_roster > 0 else 0,
        "subscription": {
            "plan": sub.plan if sub else "STANDARD",
            "status": sub.status if sub else "ACTIVE",
            "seats_used": total_active,
            "seats_limit": sub.seats_limit if sub else 1000,
            "ends_at": sub.ends_at.isoformat() if sub and sub.ends_at else None,
        },
    }


# Registre & Import dry-run
@router.get("/roster")
async def list_roster_entries(
    q: Optional[str] = Query(None),
    class_group_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.roster.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(RosterEntryModel).where(RosterEntryModel.tenant_id == ctx.tenant_id)
    if class_group_id:
        stmt = stmt.where(RosterEntryModel.class_group_id == uuid.UUID(class_group_id))
    if status_filter:
        stmt = stmt.where(RosterEntryModel.status == status_filter)
    if q:
        search = f"%{q.strip()}%"
        stmt = stmt.where((RosterEntryModel.last_name.ilike(search)) | (RosterEntryModel.first_name.ilike(search)) | (RosterEntryModel.matricule.ilike(search)))

    stmt = stmt.order_by(RosterEntryModel.last_name).limit(100)
    res = await db.execute(stmt)
    entries = res.scalars().all()

    return [
        {
            "id": str(e.id),
            "matricule": e.matricule,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "class_group_id": str(e.class_group_id) if e.class_group_id else None,
            "official_email": e.official_email,
            "status": e.status,
            "academic_year": e.academic_year,
            "claimed_at": e.claimed_at.isoformat() if e.claimed_at else None,
        }
        for e in entries
    ]


@router.post("/roster")
async def create_roster_entry(
    dto: RosterEntryCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.roster.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    tenant = await db.get(TenantModel, ctx.tenant_id)

    entry = RosterEntryModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        matricule=dto.matricule.strip(),
        last_name=dto.last_name.strip(),
        first_name=dto.first_name.strip(),
        birth_date=encrypt_field(dto.birth_date.strip()),
        birth_place=encrypt_field(dto.birth_place.strip()),
        norm_matricule=normalize_matricule(dto.matricule),
        norm_first_name=normalize_text(dto.first_name),
        norm_last_name=normalize_text(dto.last_name),
        norm_birth_date=dto.birth_date.strip(),
        norm_birth_place=normalize_text(dto.birth_place),
        class_group_id=uuid.UUID(dto.class_group_id) if dto.class_group_id else None,
        academic_year=tenant.current_academic_year,
        official_email=dto.official_email,
        phone=dto.phone,
        status="NOT_CLAIMED",
        created_by=ctx.user_id,
    )
    db.add(entry)
    await log_audit_event(db, "ROSTER_ENTRY_CREATE", "roster_entry", ctx.tenant_id, ctx.user_id, str(entry.id), {"matricule": entry.matricule})
    await db.commit()
    return {"id": str(entry.id), "status": "created"}


@router.post("/roster/import")
async def import_roster_csv(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.roster.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Import du registre via fichier CSV avec mode dry-run de prévisualisation."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .csv sont autorisés")

    content = await file.read()
    decoded = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    tenant = await db.get(TenantModel, ctx.tenant_id)
    now = datetime.now(timezone.utc)

    valid_rows = []
    error_rows = []

    for idx, row in enumerate(reader, start=2):
        mat = row.get("matricule") or row.get("Matricule")
        nom = row.get("nom") or row.get("Nom") or row.get("last_name")
        prenom = row.get("prenom") or row.get("Prenom") or row.get("first_name")
        bdate = row.get("date_naissance") or row.get("DateNaissance") or row.get("birth_date")
        bplace = row.get("lieu_naissance") or row.get("LieuNaissance") or row.get("birth_place")
        email = row.get("email") or row.get("Email") or row.get("official_email")

        if not mat or not nom or not prenom or not bdate or not bplace:
            error_rows.append({"row": idx, "error": "Champs requis manquants (matricule, nom, prénom, date_naissance, lieu_naissance)"})
            continue

        valid_rows.append({
            "matricule": sanitize_csv_cell(mat),
            "last_name": sanitize_csv_cell(nom),
            "first_name": sanitize_csv_cell(prenom),
            "birth_date": bdate.strip(),
            "birth_place": sanitize_csv_cell(bplace),
            "official_email": email.strip() if email else None,
        })

    if dry_run:
        return {
            "dry_run": True,
            "total_rows": len(valid_rows) + len(error_rows),
            "valid_rows_count": len(valid_rows),
            "error_rows_count": len(error_rows),
            "error_sample": error_rows[:10],
            "valid_sample": valid_rows[:5],
        }

    # Import réel
    batch = ImportBatchModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        filename=file.filename,
        total_rows=len(valid_rows) + len(error_rows),
        created_rows=len(valid_rows),
        error_rows=len(error_rows),
        errors_json=str(error_rows) if error_rows else None,
        created_by=ctx.user_id,
        created_at=now,
    )
    db.add(batch)

    for item in valid_rows:
        entry = RosterEntryModel(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            matricule=item["matricule"],
            last_name=item["last_name"],
            first_name=item["first_name"],
            birth_date=encrypt_field(item["birth_date"]),
            birth_place=encrypt_field(item["birth_place"]),
            norm_matricule=normalize_matricule(item["matricule"]),
            norm_first_name=normalize_text(item["first_name"]),
            norm_last_name=normalize_text(item["last_name"]),
            norm_birth_date=item["birth_date"],
            norm_birth_place=normalize_text(item["birth_place"]),
            academic_year=tenant.current_academic_year,
            official_email=item["official_email"],
            status="NOT_CLAIMED",
            created_by=ctx.user_id,
            import_batch_id=batch.id,
        )
        db.add(entry)

    await log_audit_event(db, "ROSTER_IMPORT", "import_batch", ctx.tenant_id, ctx.user_id, str(batch.id), {"total": len(valid_rows)})
    await db.commit()

    return {
        "dry_run": False,
        "batch_id": str(batch.id),
        "created_rows": len(valid_rows),
        "error_rows": len(error_rows),
    }


# Invitations Mode B
@router.post("/invitations/bulk")
async def generate_bulk_invitations(
    roster_entry_ids: List[str],
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.invitation.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Génère des accès par invitation (Mode B) pour une liste d'étudiants du registre."""
    tenant = await db.get(TenantModel, ctx.tenant_id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=7)

    created_invitations = []
    alphabet = string.ascii_uppercase + string.digits

    for rid_str in roster_entry_ids:
        entry = await db.get(RosterEntryModel, uuid.UUID(rid_str))
        if not entry or entry.tenant_id != ctx.tenant_id:
            continue

        # Identifiant unique lisible
        rand_suffix = "".join(secrets.choice(alphabet) for _ in range(8))
        identifier = f"PNL-{tenant.code}-{rand_suffix}"

        # Mot de passe temporaire CSPRNG (12 car.)
        temp_pwd = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$") for _ in range(12))
        secret_hash = pwd_context.hash(temp_pwd)

        invitation = InvitationModel(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            roster_entry_id=entry.id,
            identifier=identifier,
            secret_hash=secret_hash,
            email_sent_to=entry.official_email or f"{entry.matricule.lower()}@{tenant.code.lower()}.campus",
            status="PENDING",
            expires_at=expires_at,
            created_by=ctx.user_id,
            last_sent_at=now,
        )
        db.add(invitation)
        entry.status = "INVITED"

        # Envoi e-mail via EmailGateway (MailHog)
        email_html = f"""
        <h2>Activation de votre compte Pineapple — {tenant.name}</h2>
        <p>Bonjour {entry.first_name},</p>
        <p>Votre établissement vous a généré un accès officiel sur Pineapple OS.</p>
        <p><b>Identifiant :</b> <code>{identifier}</code><br>
        <b>Mot de passe temporaire :</b> <code>{temp_pwd}</code></p>
        <p>Activez votre compte dès maintenant : <a href="http://localhost:3000/activate">Activer mon compte</a></p>
        <p>Ce code expire dans 7 jours.</p>
        """
        await email_gateway.send_email(invitation.email_sent_to, f"Activation de votre compte {tenant.name}", email_html)
        created_invitations.append({"identifier": identifier, "email": invitation.email_sent_to})

    await log_audit_event(db, "INVITATIONS_GENERATE_BULK", "invitations", ctx.tenant_id, ctx.user_id, None, {"count": len(created_invitations)})
    await db.commit()

    return {"count": len(created_invitations), "invitations": created_invitations}


# Classes (ClassGroup)
@router.get("/classes")
async def list_classes(
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.class.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(ClassGroupModel).where(ClassGroupModel.tenant_id == ctx.tenant_id).order_by(ClassGroupModel.code)
    res = await db.execute(stmt)
    return [{"id": str(c.id), "name": c.name, "code": c.code, "level": c.level, "capacity": c.capacity} for c in res.scalars().all()]


@router.post("/classes")
async def create_class(
    dto: ClassGroupCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.class.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    tenant = await db.get(TenantModel, ctx.tenant_id)
    cg = ClassGroupModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        name=dto.name,
        code=dto.code,
        faculty=dto.faculty,
        filiere=dto.filiere,
        level=dto.level,
        capacity=dto.capacity,
        academic_year=tenant.current_academic_year,
    )
    db.add(cg)
    await db.commit()
    return {"id": str(cg.id), "code": cg.code}


# Salles (Rooms)
@router.get("/rooms")
async def list_admin_rooms(
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.room.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(RoomModel).where(RoomModel.tenant_id == ctx.tenant_id).order_by(RoomModel.name)
    res = await db.execute(stmt)
    return [{"id": str(r.id), "name": r.name, "building": r.building, "capacity": r.capacity, "status": r.status} for r in res.scalars().all()]


@router.post("/rooms")
async def create_room(
    dto: RoomCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.room.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    room = RoomModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        name=dto.name,
        building=dto.building,
        capacity=dto.capacity,
        status="FREE",
    )
    db.add(room)
    await db.commit()
    return {"id": str(room.id), "name": room.name}


# Délégués
@router.put("/classes/{class_id}/delegates")
async def assign_delegate(
    class_id: str,
    dto: DelegateAssignDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.delegate.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Désigne ou remplace le délégué (titulaire ou suppléant) d'une classe. Révocation immédiate de l'ancien."""
    cid = uuid.UUID(class_id)
    target_user_id = uuid.UUID(dto.user_id)
    now = datetime.now(timezone.utc)

    # Révoquer l'ancien délégué actif du même type
    old_stmt = select(ClassDelegateModel).where(
        ClassDelegateModel.class_group_id == cid,
        ClassDelegateModel.kind == dto.kind,
        ClassDelegateModel.revoked_at.is_(None),
    )
    old_res = await db.execute(old_stmt)
    for old_del in old_res.scalars().all():
        old_del.revoked_at = now
        old_del.revoked_by = ctx.user_id

    # Créer le nouveau délégué
    delegate = ClassDelegateModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        class_group_id=cid,
        user_id=target_user_id,
        kind=dto.kind,
        appointed_by=ctx.user_id,
        appointed_at=now,
    )
    db.add(delegate)

    await log_audit_event(db, "DELEGATE_APPOINT", "class_delegate", ctx.tenant_id, ctx.user_id, str(delegate.id), {"class_id": class_id, "user_id": dto.user_id, "kind": dto.kind})
    await db.commit()
    return {"status": "ok", "delegate_id": str(delegate.id)}


# Audit
@router.get("/audit")
async def get_audit_logs(
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.audit.view")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(AuditLogModel).where(AuditLogModel.tenant_id == str(ctx.tenant_id)).order_by(AuditLogModel.timestamp.desc()).limit(100)
    res = await db.execute(stmt)
    return [
        {
            "id": str(l.id),
            "action": l.action,
            "resource_type": l.resource_type,
            "user_id": str(l.user_id) if l.user_id else None,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in res.scalars().all()
    ]
