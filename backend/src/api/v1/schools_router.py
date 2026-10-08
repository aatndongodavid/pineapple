from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.infrastructure.persistence.models import TenantModel
from shared_kernel.infrastructure.database import get_db_session

router = APIRouter(prefix="/schools", tags=["Schools Public"])


class SchoolPublicDTO(BaseModel):
    id: str
    name: str
    code: str
    logo_url: Optional[str] = None
    country: str
    enrollment_mode: str


@router.get("/public", response_model=List[SchoolPublicDTO])
async def list_public_schools(
    q: Optional[str] = Query(None, description="Recherche par nom ou code d'établissement"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Recherche publique d'établissements (pour l'assistant de rattachement Mode A/B).
    Ne renvoie que des informations publiques (nom, code, logo).
    """
    stmt = select(TenantModel).where(TenantModel.is_active.is_(True))
    if q:
        search_term = f"%{q.strip()}%"
        stmt = stmt.where(
            (TenantModel.name.ilike(search_term)) | (TenantModel.code.ilike(search_term))
        )
    stmt = stmt.order_by(TenantModel.name).limit(50)

    result = await db.execute(stmt)
    tenants = result.scalars().all()

    return [
        SchoolPublicDTO(
            id=str(t.id),
            name=t.name,
            code=t.code,
            logo_url=t.logo_url,
            country=t.country,
            enrollment_mode=t.enrollment_mode,
        )
        for t in tenants
    ]
