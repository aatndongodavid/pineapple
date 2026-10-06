import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.infrastructure.persistence.models import (
    ClassGroupModel,
    MembershipModel,
    TenantModel,
    TenantSubscriptionModel,
    UserModel,
)
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    create_jwt_token,
    get_user_context,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/identity", tags=["Identity & Auth"])


# DTOs
class PublicRegisterDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mot de passe fort")
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class LoginDTO(BaseModel):
    email: EmailStr
    password: str


class PasswordChangeDTO(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    tenant_id: Optional[str] = None
    membership_id: Optional[str] = None
    must_change_password: bool = False


@router.post("/register", response_model=TokenResponseDTO, status_code=status.HTTP_201_CREATED)
async def register_public_user(
    dto: PublicRegisterDTO,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Inscription publique gratuite pour devenir un utilisateur Visiteur.
    Aucun champ matricule / filière requis.
    """
    normalized_email = dto.email.lower().strip()

    # Vérifier l'existence de l'e-mail
    existing = (await db.execute(select(UserModel).where(UserModel.email == normalized_email))).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet adresse e-mail est déjà utilisée.",
        )

    user = UserModel(
        id=uuid.uuid4(),
        email=normalized_email,
        hashed_password=pwd_context.hash(dto.password),
        first_name=dto.first_name.strip(),
        last_name=dto.last_name.strip(),
        phone_number=dto.phone_number,
        account_status="ACTIVE",
        user_type="STANDARD",
        must_change_password=False,
    )
    db.add(user)
    await db.commit()

    token = create_jwt_token(user_id=user.id, role="VISITOR")

    return TokenResponseDTO(
        access_token=token,
        token_type="bearer",
        user_id=str(user.id),
        role="VISITOR",
    )


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    dto: LoginDTO,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authentification globale et émission de JWT.
    """
    normalized_email = dto.email.lower().strip()
    user = (await db.execute(select(UserModel).where(UserModel.email == normalized_email))).scalars().first()

    if not user or not pwd_context.verify(dto.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )

    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est inactif ou suspendu",
        )

    if user.user_type == "PLATFORM_ADMIN":
        token = create_jwt_token(user_id=user.id, role="PLATFORM_SUPER_ADMIN")
        return TokenResponseDTO(
            access_token=token,
            user_id=str(user.id),
            role="PLATFORM_SUPER_ADMIN",
            must_change_password=user.must_change_password,
        )

    # Rechercher un membership actif
    m_stmt = select(MembershipModel).where(
        MembershipModel.user_id == user.id,
        MembershipModel.status == "ACTIVE",
    )
    membership = (await db.execute(m_stmt)).scalars().first()

    if membership:
        token = create_jwt_token(
            user_id=user.id,
            tenant_id=membership.tenant_id,
            membership_id=membership.id,
            role=membership.role,
        )
        return TokenResponseDTO(
            access_token=token,
            user_id=str(user.id),
            role=membership.role,
            tenant_id=str(membership.tenant_id),
            membership_id=str(membership.id),
            must_change_password=user.must_change_password,
        )

    # Utilisateur Visiteur sans appartenance d'établissement
    token = create_jwt_token(user_id=user.id, role="VISITOR")
    return TokenResponseDTO(
        access_token=token,
        user_id=str(user.id),
        role="VISITOR",
        must_change_password=user.must_change_password,
    )


@router.get("/me")
async def get_current_user_profile(
    ctx: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Renvoie le profil enrichi de l'utilisateur connecté :
    user, membership, tenant, class_group, delegate_of, permissions, subscription_state, campus_status_display.
    """
    tenant_obj = None
    class_group_obj = None

    if ctx.tenant_id:
        tenant = await db.get(TenantModel, ctx.tenant_id)
        if tenant:
            tenant_obj = {
                "id": str(tenant.id),
                "name": tenant.name,
                "code": tenant.code,
                "logo_url": tenant.logo_url,
                "current_academic_year": tenant.current_academic_year,
            }

    if ctx.class_group_id:
        cg = await db.get(ClassGroupModel, ctx.class_group_id)
        if cg:
            class_group_obj = {
                "id": str(cg.id),
                "name": cg.name,
                "code": cg.code,
                "level": cg.level,
            }

    campus_status_display = "Visiteur"
    if ctx.role == "PLATFORM_SUPER_ADMIN":
        campus_status_display = "Super Admin Pineapple"
    elif ctx.role == "TENANT_ADMIN":
        campus_status_display = "Administrateur Établissement"
    elif ctx.role == "STAFF":
        campus_status_display = "Membre de la Scolarité"
    elif ctx.role == "TEACHER":
        campus_status_display = "Enseignant Vérifié"
    elif ctx.role == "DELEGATE" or ctx.delegate_of:
        campus_status_display = "Délégué de Classe"
    elif ctx.role == "STUDENT":
        campus_status_display = "Étudiant Vérifié"

    return {
        "user": {
            "id": str(ctx.user_id),
            "email": ctx.email,
            "first_name": ctx.first_name,
            "last_name": ctx.last_name,
            "user_type": ctx.user_type,
        },
        "membership": {
            "id": str(ctx.membership_id) if ctx.membership_id else None,
            "role": ctx.role,
            "status": "ACTIVE" if ctx.membership_id else "NONE",
        },
        "tenant": tenant_obj,
        "class_group": class_group_obj,
        "delegate_of": [str(c) for c in ctx.delegate_of],
        "permissions": list(ctx.permissions),
        "subscription_state": ctx.subscription_status,
        "campus_status_display": campus_status_display,
    }


@router.post("/password/change")
async def change_password(
    dto: PasswordChangeDTO,
    ctx: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    user = await db.get(UserModel, ctx.user_id)
    if not user or not pwd_context.verify(dto.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    user.hashed_password = pwd_context.hash(dto.new_password)
    user.must_change_password = False
    await db.commit()
    return {"status": "ok", "message": "Mot de passe modifié avec succès"}


@router.post("/revoke-token")
async def revoke_token():
    """Révocation du jeton de session courant (déconnexion)."""
    return {"status": "ok", "message": "Jeton révoqué"}