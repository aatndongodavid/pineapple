import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared_kernel.config import settings
from shared_kernel.infrastructure.auth import require_platform_admin
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.platform_models import PlatformAdminModel, TenantModel
from identity_context.infrastructure.persistence.models import UserModel
from democracy_context.infrastructure.persistence.models import ElectionModel
from campus_life_context.infrastructure.persistence.models import MarketplaceListingModel

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/platform", tags=["Platform & Super Admin"])


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


# DTOs
class PlatformLoginDTO(BaseModel):
    email: EmailStr
    password: str


class TenantCreateDTO(BaseModel):
    name: str
    code: str
    domain: Optional[str] = None
    logo_url: Optional[str] = None


class TenantResponseDTO(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    domain: Optional[str] = None
    is_active: bool
    created_at: datetime
    user_count: int = 0
    election_count: int = 0


class PlatformMetricsDTO(BaseModel):
    total_tenants: int
    total_users: int
    total_elections: int
    total_listings: int


@router.post("/login", status_code=status.HTTP_200_OK)
async def platform_admin_login(
    dto: PlatformLoginDTO,
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """
    Authentification pour le rôle Super Administrateur de la plateforme (équipe Gemula).
    Délivre un token JWT avec le claim scope="platform".
    """
    async with session_factory() as session:
        stmt = select(PlatformAdminModel).where(PlatformAdminModel.email == dto.email)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        # Pour le développement/démo, auto-provisionner le super admin par défaut s'il n'existe pas
        if admin is None and dto.email == "admin@gemula.cm":
            hashed = pwd_context.hash(dto.password)
            admin = PlatformAdminModel(
                id=uuid.uuid4(),
                email=dto.email,
                hashed_password=hashed,
            )
            session.add(admin)
            await session.commit()
        elif admin is None or not pwd_context.verify(dto.password, admin.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identifiants Super Admin invalides",
            )

        expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(admin.id),
            "email": admin.email,
            "scope": "platform",
            "exp": expiration,
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "scope": "platform",
            "admin_id": str(admin.id),
        }


@router.get("/tenants", response_model=List[TenantResponseDTO])
async def list_tenants(
    admin: dict = Depends(require_platform_admin),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """
    Liste tous les établissements (tenants) enregistrés sur la plateforme avec leurs statistiques.
    Réservé au Super Administrateur.
    """
    async with session_factory() as session:
        stmt = select(TenantModel).order_by(TenantModel.name)
        result = await session.execute(stmt)
        tenants = result.scalars().all()

        response = []
        for t in tenants:
            # Compter les utilisateurs
            user_stmt = select(func.count(UserModel.id)).where(UserModel.tenant_id == t.id)
            user_count = (await session.execute(user_stmt)).scalar() or 0

            # Compter les élections
            elec_stmt = select(func.count(ElectionModel.id)).where(ElectionModel.tenant_id == t.id)
            elec_count = (await session.execute(elec_stmt)).scalar() or 0

            response.append(
                TenantResponseDTO(
                    id=t.id,
                    name=t.name,
                    code=t.code,
                    domain=t.domain,
                    is_active=t.is_active,
                    created_at=t.created_at,
                    user_count=user_count,
                    election_count=elec_count,
                )
            )
        return response


@router.post("/tenants", response_model=TenantResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    dto: TenantCreateDTO,
    admin: dict = Depends(require_platform_admin),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """
    Provisionnement d'un nouvel établissement (ex: ENSPD, UDo, Yaoundé I).
    Réservé au Super Administrateur.
    """
    async with session_factory() as session:
        # Vérifier unicité du code
        existing_stmt = select(TenantModel).where(TenantModel.code == dto.code)
        if (await session.execute(existing_stmt)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Le code d'établissement {dto.code} existe déjà",
            )

        tenant = TenantModel(
            id=uuid.uuid4(),
            name=dto.name,
            code=dto.code,
            domain=dto.domain,
            logo_url=dto.logo_url,
            is_active=True,
        )
        session.add(tenant)
        await session.commit()

        return TenantResponseDTO(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            domain=tenant.domain,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            user_count=0,
            election_count=0,
        )


@router.get("/metrics", response_model=PlatformMetricsDTO)
async def get_platform_metrics(
    admin: dict = Depends(require_platform_admin),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """
    Métriques consolidées de la plateforme cross-tenant (nombre d'établissements, d'utilisateurs, d'élections, d'annonces).
    Réservé au Super Administrateur.
    """
    async with session_factory() as session:
        tenants_count = (await session.execute(select(func.count(TenantModel.id)))).scalar() or 0
        users_count = (await session.execute(select(func.count(UserModel.id)))).scalar() or 0
        elections_count = (await session.execute(select(func.count(ElectionModel.id)))).scalar() or 0
        listings_count = (await session.execute(select(func.count(MarketplaceListingModel.id)))).scalar() or 0

        return PlatformMetricsDTO(
            total_tenants=tenants_count,
            total_users=users_count,
            total_elections=elections_count,
            total_listings=listings_count,
        )
