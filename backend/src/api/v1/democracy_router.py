import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from democracy_context.application.dtos import (
    CastVoteDTO,
    ElectionCreateDTO,
    ElectionResponseDTO,
    ElectionResultsDTO,
)
from democracy_context.application.use_cases import (
    AlreadyVotedError,
    CastVoteUseCase,
    CreateElectionUseCase,
    ElectionNotFoundError,
    NotEligibleError,
    TallyNotAllowedError,
    TallyResultsUseCase,
    VotingNotOpenError,
)
from democracy_context.domain.entities import ElectionStatus
from democracy_context.domain.ports import (
    AuditLedgerPort,
    CryptoEnginePort,
    ElectionRepositoryPort,
    VoteRepositoryPort,
)
from democracy_context.infrastructure.persistence.repositories import (
    PostgresAuditLedgerRepository,
    PostgresElectionRepository,
    PostgresVoteRepository,
    RSACryptoEngine,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

# ---------------------------------------------------------------------------
# Sécurité & dépendances transverses
# ---------------------------------------------------------------------------
security = HTTPBearer()


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_election_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresElectionRepository:
    return PostgresElectionRepository(session_factory)


async def get_vote_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresVoteRepository:
    return PostgresVoteRepository(session_factory)


async def get_crypto_engine() -> RSACryptoEngine:
    return RSACryptoEngine()


async def get_audit_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresAuditLedgerRepository:
    return PostgresAuditLedgerRepository(session_factory)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> dict:
    """Retourne l'utilisateur courant à partir du JWT (simplifié : id + tenant)."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = uuid.UUID(payload.get("sub"))
        token_tenant = uuid.UUID(payload.get("tenant_id"))
        if token_tenant != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tenant mismatch",
            )
        return {"user_id": user_id, "tenant_id": tenant_id}
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


# NOTE: Pour les opérations admin, il faudrait un rôle vérifié.
# On suppose qu'une dépendance get_admin_user vérifie le rôle admin.
# Ici, on se contente d'authentifier l'utilisateur et on documente la nécessité du contrôle RBAC.
async def get_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    # TODO: Implémenter la vérification du rôle admin (cf. A.15 RBAC)
    return current_user


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/democracy", tags=["Democracy & Voting Engine"])


@router.post("/elections", response_model=ElectionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_election(
    dto: ElectionCreateDTO,
    admin: dict = Depends(get_admin_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    election_repo: PostgresElectionRepository = Depends(get_election_repo),
    audit_repo: PostgresAuditLedgerRepository = Depends(get_audit_repo),
):
    """
    Création d'une élection (réservé aux administrateurs).
    """
    use_case = CreateElectionUseCase(election_repo, audit_repo)
    election = await use_case.execute(dto, tenant_id)

    return ElectionResponseDTO(
        id=election.id,
        tenant_id=election.tenant_id,
        title=election.title,
        election_type=election.election_type,
        status=election.status.value,
        eligibility_rules=election.eligibility_rules,
        voting_start_at=election.voting_start_at,
        voting_end_at=election.voting_end_at,
        total_voters_count=0,  # à calculer si nécessaire
    )


@router.get("/elections", response_model=List[ElectionResponseDTO])
async def list_elections(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    election_repo: PostgresElectionRepository = Depends(get_election_repo),
):
    """
    Liste les élections du campus (toutes ou filtrées par statut si query param fourni).
    """
    # Optionnel : status en query param
    # Ici on renvoie toutes les élections non archivées par exemple
    elections = await election_repo.list_elections_by_tenant(tenant_id)
    return [
        ElectionResponseDTO(
            id=e.id,
            tenant_id=e.tenant_id,
            title=e.title,
            election_type=e.election_type,
            status=e.status.value,
            eligibility_rules=e.eligibility_rules,
            voting_start_at=e.voting_start_at,
            voting_end_at=e.voting_end_at,
            total_voters_count=0,
        )
        for e in elections
        if e.status != ElectionStatus.ARCHIVED
    ]


@router.post("/elections/{election_id}/vote", status_code=status.HTTP_202_ACCEPTED)
async def cast_vote(
    election_id: uuid.UUID,
    dto: CastVoteDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    election_repo: PostgresElectionRepository = Depends(get_election_repo),
    vote_repo: PostgresVoteRepository = Depends(get_vote_repo),
    crypto_engine: RSACryptoEngine = Depends(get_crypto_engine),
    audit_repo: PostgresAuditLedgerRepository = Depends(get_audit_repo),
):
    """
    Exprime un vote pour une élection donnée.
    Vérifie l'éligibilité, l'unicité et chiffre le bulletin avant enregistrement.
    """
    # Le use case requiert un UserInfoProvider ; pour la démonstration on fournit un provider simple.
    class UserInfoProvider:
        def get_user_info(self, user_id: uuid.UUID) -> dict:
            # TODO: Appel au service Identity pour obtenir les infos académiques.
            # Pour l'exemple, on suppose que l'utilisateur est éligible.
            return {
                "academic_status": "student",
                "is_certified": True,
                "level": "L3",
            }

    use_case = CastVoteUseCase(
        election_repo=election_repo,
        vote_repo=vote_repo,
        crypto_engine=crypto_engine,
        audit_ledger=audit_repo,
        user_info_provider=UserInfoProvider(),
    )

    # Clé publique à récupérer depuis la configuration ou un service de clés.
    # Pour le prototype, on met une clé factice (à remplacer).
    PUBLIC_KEY_PEM = "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

    try:
        await use_case.execute(
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=dto,
            public_key_pem=PUBLIC_KEY_PEM,
        )
    except ElectionNotFoundError:
        raise HTTPException(status_code=404, detail="Election not found")
    except VotingNotOpenError:
        raise HTTPException(status_code=400, detail="Voting is not currently open")
    except NotEligibleError:
        raise HTTPException(status_code=403, detail="User is not eligible for this election")
    except AlreadyVotedError:
        raise HTTPException(status_code=409, detail="User has already voted")

    return {"message": "Vote cast successfully"}


@router.post("/elections/{election_id}/tally", response_model=ElectionResultsDTO)
async def tally_election(
    election_id: uuid.UUID,
    admin: dict = Depends(get_admin_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    election_repo: PostgresElectionRepository = Depends(get_election_repo),
    vote_repo: PostgresVoteRepository = Depends(get_vote_repo),
    crypto_engine: RSACryptoEngine = Depends(get_crypto_engine),
    audit_repo: PostgresAuditLedgerRepository = Depends(get_audit_repo),
):
    """
    Clôture et dépouille le scrutin (réservé aux administrateurs).
    """
    use_case = TallyResultsUseCase(
        election_repo=election_repo,
        vote_repo=vote_repo,
        crypto_engine=crypto_engine,
        audit_ledger=audit_repo,
    )

    # Clé privée à récupérer depuis un stockage sécurisé (jamais en clair dans le code).
    PRIVATE_KEY_PEM = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

    try:
        results = await use_case.execute(election_id, tenant_id, PRIVATE_KEY_PEM)
    except ElectionNotFoundError:
        raise HTTPException(status_code=404, detail="Election not found")
    except TallyNotAllowedError:
        raise HTTPException(status_code=400, detail="Election must be closed before tallying")

    return results


@router.get("/elections/{election_id}/audit")
async def get_election_audit(
    election_id: uuid.UUID,
    admin: dict = Depends(get_admin_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    audit_repo: PostgresAuditLedgerRepository = Depends(get_audit_repo),
):
    """
    Consulte le registre immuable de l'élection (réservé aux administrateurs).
    """
    # TODO: Implémenter une méthode de listing des entrées d'audit filtrées par élection.
    # Pour le moment, on renvoie un message indiquant que la fonctionnalité est en cours.
    return {
        "message": "Audit log query not yet implemented",
        "election_id": str(election_id),
    }