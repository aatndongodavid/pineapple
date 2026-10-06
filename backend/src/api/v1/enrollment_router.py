import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.infrastructure.persistence.models import (
    ClassGroupModel,
    EnrollmentAttemptModel,
    InvitationModel,
    MembershipModel,
    RosterEntryModel,
    TenantModel,
    UserModel,
)
from shared_kernel.infrastructure.audit_log import log_audit_event
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.encryption import normalize_matricule, normalize_text
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    create_jwt_token,
    get_user_context,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])

GENERIC_CLAIM_ERROR = "Informations non reconnues. Vérifie auprès de ton établissement."
GENERIC_ACTIVATE_ERROR = "Identifiant ou mot de passe temporaire invalide."


class ClaimSchoolRequestDTO(BaseModel):
    tenant_id: str
    matricule: str = Field(..., description="Matricule officiel")
    first_name: str = Field(..., description="Prénom officiel")
    last_name: str = Field(..., description="Nom officiel")
    birth_date: str = Field(..., description="Date de naissance au format YYYY-MM-DD")
    birth_place: str = Field(..., description="Lieu de naissance officiel")


class ActivateInvitationRequestDTO(BaseModel):
    identifier: str = Field(..., description="Identifiant unique d'invitation (ex: PNL-ENSPD-X7K2M9N4)")
    temp_password: str = Field(..., description="Mot de passe temporaire reçu par e-mail")


class EnrollmentStatusResponseDTO(BaseModel):
    has_membership: bool
    status: Optional[str] = None
    tenant_name: Optional[str] = None
    role: Optional[str] = None
    joined_via: Optional[str] = None


@router.post("/claim")
async def claim_school_membership(
    dto: ClaimSchoolRequestDTO,
    request: Request,
    response: Response,
    ctx: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Mode A — Auto-rattachement par vérification d'état civil (5 champs).
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    tenant_uuid = uuid.UUID(dto.tenant_id)

    # 1. Vérification anti-bruteforce dans enrollment_attempts
    now = datetime.now(timezone.utc)
    half_hour_ago = now - timedelta(minutes=30)
    one_hour_ago = now - timedelta(hours=1)

    # Échecs par utilisateur (max 5 / 30 min)
    u_fails = await db.execute(
        select(func.count(EnrollmentAttemptModel.id)).where(
            EnrollmentAttemptModel.user_id == ctx.user_id,
            EnrollmentAttemptModel.success.is_(False),
            EnrollmentAttemptModel.created_at >= half_hour_ago,
        )
    )
    if u_fails.scalar() >= 5:
        response.headers["Retry-After"] = "1800"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de rattachement échouées. Réessaie dans 30 minutes.",
        )

    # Échecs par IP (max 20 / 1h)
    ip_fails = await db.execute(
        select(func.count(EnrollmentAttemptModel.id)).where(
            EnrollmentAttemptModel.ip == client_ip,
            EnrollmentAttemptModel.success.is_(False),
            EnrollmentAttemptModel.created_at >= one_hour_ago,
        )
    )
    if ip_fails.scalar() >= 20:
        response.headers["Retry-After"] = "3600"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives depuis cette adresse IP. Réessaie plus tard.",
        )

    # 2. Vérification de l'établissement
    tenant = await db.get(TenantModel, tenant_uuid)
    if not tenant or not tenant.is_active:
        await _log_attempt(db, tenant_uuid, ctx.user_id, client_ip, "CLAIM", False, "Tenant inexistant ou inactif")
        raise HTTPException(status_code=400, detail={"code": "ENROLLMENT_FAILED", "message": GENERIC_CLAIM_ERROR})

    # 3. Normalisation des données saisies
    n_matricule = normalize_matricule(dto.matricule)
    n_first_name = normalize_text(dto.first_name)
    n_last_name = normalize_text(dto.last_name)
    n_birth_date = dto.birth_date.strip()
    n_birth_place = normalize_text(dto.birth_place)

    # 4. Requête de comparaison exacte sur les 5 champs
    stmt = select(RosterEntryModel).where(
        RosterEntryModel.tenant_id == tenant_uuid,
        RosterEntryModel.norm_matricule == n_matricule,
        RosterEntryModel.norm_first_name == n_first_name,
        RosterEntryModel.norm_last_name == n_last_name,
        RosterEntryModel.norm_birth_date == n_birth_date,
        RosterEntryModel.norm_birth_place == n_birth_place,
        RosterEntryModel.status.in_(["NOT_CLAIMED", "INVITED"]),
    ).with_for_update()

    result = await db.execute(stmt)
    roster_entry = result.scalars().first()

    if not roster_entry:
        await _log_attempt(db, tenant_uuid, ctx.user_id, client_ip, "CLAIM", False, "Mismatch sur les 5 champs civil_status")
        raise HTTPException(status_code=400, detail={"code": "ENROLLMENT_FAILED", "message": GENERIC_CLAIM_ERROR})

    # 5. Création atomique du Membership & Mise à jour du RosterEntry
    membership_status = "ACTIVE" if tenant.auto_approve_claims else "PENDING"
    membership = MembershipModel(
        id=uuid.uuid4(),
        tenant_id=tenant_uuid,
        user_id=ctx.user_id,
        roster_entry_id=roster_entry.id,
        class_group_id=roster_entry.class_group_id,
        role="STUDENT",
        status=membership_status,
        joined_via="CLAIM",
        joined_at=now,
        academic_year=tenant.current_academic_year,
    )
    db.add(membership)

    roster_entry.status = "CLAIMED"
    roster_entry.claimed_by_user_id = ctx.user_id
    roster_entry.claimed_at = now

    await _log_attempt(db, tenant_uuid, ctx.user_id, client_ip, "CLAIM", True, None)
    await log_audit_event(
        db,
        action="ENROLLMENT_CLAIM_SUCCESS",
        resource_type="membership",
        tenant_id=tenant_uuid,
        user_id=ctx.user_id,
        resource_id=str(membership.id),
        details={"status": membership_status, "matricule": roster_entry.matricule},
        ip_address=client_ip,
    )

    await db.commit()

    # Nouveau jeton JWT enrichi avec tid & mid
    new_token = create_jwt_token(
        user_id=ctx.user_id,
        tenant_id=tenant_uuid,
        membership_id=membership.id,
        role="STUDENT",
    )

    return {
        "status": membership_status,
        "message": "Auto-rattachement réussi ! Votre compte est maintenant associé à votre établissement." if membership_status == "ACTIVE" else "Demande de rattachement enregistrée. En attente de validation par l'administration.",
        "access_token": new_token,
        "token_type": "bearer",
        "tenant_id": str(tenant_uuid),
        "membership_id": str(membership.id),
    }


@router.post("/activate")
async def activate_invitation(
    dto: ActivateInvitationRequestDTO,
    request: Request,
    ctx: Optional[AuthenticatedUserContext] = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Mode B — Activation par identifiant unique et mot de passe temporaire.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = datetime.now(timezone.utc)

    # 1. Rechercher l'invitation
    stmt = select(InvitationModel).where(
        InvitationModel.identifier == dto.identifier.strip().upper(),
        InvitationModel.status == "PENDING",
    ).with_for_update()

    res = await db.execute(stmt)
    invitation = res.scalars().first()

    if not invitation or invitation.expires_at < now or invitation.failed_attempts >= 5:
        if invitation:
            invitation.failed_attempts += 1
            if invitation.failed_attempts >= 5:
                invitation.status = "REVOKED"
            await db.commit()
        await _log_attempt(db, None, ctx.user_id if ctx else None, client_ip, "ACTIVATE", False, "Invitation invalide/expirée")
        raise HTTPException(status_code=400, detail={"code": "ENROLLMENT_FAILED", "message": GENERIC_ACTIVATE_ERROR})

    # 2. Vérifier le mot de passe temporaire haché
    if not pwd_context.verify(dto.temp_password, invitation.secret_hash):
        invitation.failed_attempts += 1
        if invitation.failed_attempts >= 5:
            invitation.status = "REVOKED"
        await db.commit()
        await _log_attempt(db, invitation.tenant_id, ctx.user_id if ctx else None, client_ip, "ACTIVATE", False, "Mot de passe temporaire incorrect")
        raise HTTPException(status_code=400, detail={"code": "ENROLLMENT_FAILED", "message": GENERIC_ACTIVATE_ERROR})

    # 3. Récupérer l'entrée du registre
    roster_entry = await db.get(RosterEntryModel, invitation.roster_entry_id)
    if not roster_entry:
        raise HTTPException(status_code=400, detail={"code": "ENROLLMENT_FAILED", "message": GENERIC_ACTIVATE_ERROR})

    user_id = ctx.user_id if ctx else None

    # Si l'utilisateur n'est pas connecté, créer son compte utilisateur avec e-mail officiel
    if not user_id:
        user_email = roster_entry.official_email or invitation.email_sent_to
        existing_user_stmt = select(UserModel).where(UserModel.email == user_email.lower())
        ex_res = await db.execute(existing_user_stmt)
        existing_user = ex_res.scalars().first()

        if existing_user:
            user_id = existing_user.id
        else:
            user_id = uuid.uuid4()
            new_user = UserModel(
                id=user_id,
                email=user_email.lower(),
                hashed_password=pwd_context.hash(dto.temp_password),
                first_name=roster_entry.first_name,
                last_name=roster_entry.last_name,
                account_status="ACTIVE",
                must_change_password=True,
                created_at=now,
            )
            db.add(new_user)

    # 4. Activer le compte & Créer le Membership
    invitation.status = "USED"
    invitation.used_at = now

    roster_entry.status = "CLAIMED"
    roster_entry.claimed_by_user_id = user_id
    roster_entry.claimed_at = now

    tenant = await db.get(TenantModel, invitation.tenant_id)
    membership = MembershipModel(
        id=uuid.uuid4(),
        tenant_id=invitation.tenant_id,
        user_id=user_id,
        roster_entry_id=roster_entry.id,
        class_group_id=roster_entry.class_group_id,
        role="STUDENT",
        status="ACTIVE",
        joined_via="INVITATION",
        joined_at=now,
        academic_year=tenant.current_academic_year if tenant else "2026-2027",
    )
    db.add(membership)

    await _log_attempt(db, invitation.tenant_id, user_id, client_ip, "ACTIVATE", True, None)
    await log_audit_event(
        db,
        action="ENROLLMENT_ACTIVATE_SUCCESS",
        resource_type="invitation",
        tenant_id=invitation.tenant_id,
        user_id=user_id,
        resource_id=str(invitation.id),
        details={"identifier": invitation.identifier},
        ip_address=client_ip,
    )

    await db.commit()

    token = create_jwt_token(
        user_id=user_id,
        tenant_id=invitation.tenant_id,
        membership_id=membership.id,
        role="STUDENT",
    )

    return {
        "status": "ACTIVE",
        "message": "Compte activé avec succès !",
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": True,
    }


@router.get("/status", response_model=EnrollmentStatusResponseDTO)
async def get_enrollment_status(
    ctx: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Renvoie le statut de rattachement de l'utilisateur connecté."""
    if ctx.role == "VISITOR" or not ctx.tenant_id:
        return EnrollmentStatusResponseDTO(has_membership=False)

    tenant = await db.get(TenantModel, ctx.tenant_id)
    return EnrollmentStatusResponseDTO(
        has_membership=True,
        status="ACTIVE",
        tenant_name=tenant.name if tenant else None,
        role=ctx.role,
        joined_via="CLAIM",
    )


async def _log_attempt(
    db: AsyncSession,
    tenant_id: Optional[uuid.UUID],
    user_id: Optional[uuid.UUID],
    ip: str,
    kind: str,
    success: bool,
    failure_reason: Optional[str],
):
    attempt = EnrollmentAttemptModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        ip=ip,
        kind=kind,
        success=success,
        failure_reason=failure_reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
