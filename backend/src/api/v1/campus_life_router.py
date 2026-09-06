import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from campus_life_context.application.dtos import (
    ListingCreateDTO,
    ListingResponseDTO,
    MessageResponseDTO,
    RideCreateDTO,
    RideResponseDTO,
    SendMessageDTO,
)
from campus_life_context.application.use_cases import (
    AlreadyBookedError,
    BookRideSeatUseCase,
    CreateMarketplaceListingUseCase,
    CreateRideShareUseCase,
    RideNotAvailableError,
    RideNotFoundError,
    SendTransversalMessageUseCase,
    UserNotEligibleError,
)
from campus_life_context.domain.entities import MarketplaceListing, RideShare
from campus_life_context.domain.value_objects import ListingCategory
from campus_life_context.infrastructure.persistence.repositories import (
    PostgresMarketplaceRepository,
    PostgresMessagingRepository,
    PostgresRideRepository,
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


async def get_marketplace_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresMarketplaceRepository:
    return PostgresMarketplaceRepository(session_factory)


async def get_ride_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresRideRepository:
    return PostgresRideRepository(session_factory)


async def get_messaging_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresMessagingRepository:
    return PostgresMessagingRepository(session_factory)


# Provider de statut utilisateur (simulé pour l'instant)
class SimpleUserStatusProvider:
    """Vérifie le statut de certification de l'utilisateur via le contexte Identity (simplifié)."""

    async def is_certified_active(self, user_id: uuid.UUID) -> bool:
        # TODO: Appeler le service Identity pour récupérer verification_status et account_status.
        # Pour la démonstration, on renvoie True (certifié actif).
        return True


async def get_user_status_provider() -> SimpleUserStatusProvider:
    return SimpleUserStatusProvider()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> dict:
    """Retourne l'utilisateur courant à partir du JWT."""
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


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/campus-life", tags=["Campus Life & Marketplace"])


@router.get("/marketplace", response_model=List[ListingResponseDTO])
async def list_listings(
    category: Optional[ListingCategory] = Query(None),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    marketplace_repo: PostgresMarketplaceRepository = Depends(get_marketplace_repo),
):
    """
    Explorer les articles à vendre sur le campus.
    """
    listings = await marketplace_repo.list_listings(tenant_id, category)
    return [
        ListingResponseDTO(
            id=l.id,
            tenant_id=l.tenant_id,
            seller_id=l.seller_id,
            title=l.title,
            description=l.description,
            price_fcfa=int(l.price.amount),
            category=l.category,
            status=l.status,
            image_urls=l.image_urls,
            created_at=l.created_at,
        )
        for l in listings
    ]


@router.post("/marketplace", response_model=ListingResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_listing(
    dto: ListingCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    marketplace_repo: PostgresMarketplaceRepository = Depends(get_marketplace_repo),
    user_status_provider: SimpleUserStatusProvider = Depends(get_user_status_provider),
):
    """
    Publier une annonce (réservé aux étudiants certifiés actifs).
    """
    use_case = CreateMarketplaceListingUseCase(marketplace_repo, user_status_provider)
    try:
        listing = await use_case.execute(
            seller_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=dto,
        )
    except UserNotEligibleError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return ListingResponseDTO(
        id=listing.id,
        tenant_id=listing.tenant_id,
        seller_id=listing.seller_id,
        title=listing.title,
        description=listing.description,
        price_fcfa=int(listing.price.amount),
        category=listing.category,
        status=listing.status,
        image_urls=listing.image_urls,
        created_at=listing.created_at,
    )


@router.get("/ride", response_model=List[RideResponseDTO])
async def search_rides(
    departure: Optional[str] = Query(None),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    ride_repo: PostgresRideRepository = Depends(get_ride_repo),
):
    """
    Parcourir les trajets de covoiturage disponibles.
    """
    rides = await ride_repo.search_rides(tenant_id, departure)
    return [
        RideResponseDTO(
            id=r.id,
            tenant_id=r.tenant_id,
            driver_id=r.driver_id,
            departure_name=r.departure.address_name,
            destination_name=r.destination.address_name,
            departure_time=r.departure_time,
            available_seats=r.available_seats,
            price_per_seat_fcfa=int(r.price_per_seat.amount),
            passenger_ids=r.passenger_ids,
            status=r.status,
        )
        for r in rides
    ]


@router.post("/ride", response_model=RideResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_ride(
    dto: RideCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    ride_repo: PostgresRideRepository = Depends(get_ride_repo),
):
    """
    Proposer un trajet de covoiturage.
    """
    use_case = CreateRideShareUseCase(ride_repo)
    ride = await use_case.execute(
        driver_id=current_user["user_id"],
        tenant_id=tenant_id,
        dto=dto,
    )
    return RideResponseDTO(
        id=ride.id,
        tenant_id=ride.tenant_id,
        driver_id=ride.driver_id,
        departure_name=ride.departure.address_name,
        destination_name=ride.destination.address_name,
        departure_time=ride.departure_time,
        available_seats=ride.available_seats,
        price_per_seat_fcfa=int(ride.price_per_seat.amount),
        passenger_ids=ride.passenger_ids,
        status=ride.status,
    )


@router.post("/ride/{ride_id}/book", response_model=RideResponseDTO)
async def book_ride(
    ride_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    ride_repo: PostgresRideRepository = Depends(get_ride_repo),
):
    """
    Réserver une place dans un trajet.
    """
    use_case = BookRideSeatUseCase(ride_repo)
    try:
        ride = await use_case.execute(
            passenger_id=current_user["user_id"],
            tenant_id=tenant_id,
            ride_id=ride_id,
        )
    except RideNotFoundError:
        raise HTTPException(status_code=404, detail="Trajet introuvable.")
    except RideNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AlreadyBookedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except UserNotEligibleError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return RideResponseDTO(
        id=ride.id,
        tenant_id=ride.tenant_id,
        driver_id=ride.driver_id,
        departure_name=ride.departure.address_name,
        destination_name=ride.destination.address_name,
        departure_time=ride.departure_time,
        available_seats=ride.available_seats,
        price_per_seat_fcfa=int(ride.price_per_seat.amount),
        passenger_ids=ride.passenger_ids,
        status=ride.status,
    )


@router.get("/messages/{conversation_id}", response_model=List[MessageResponseDTO])
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    messaging_repo: PostgresMessagingRepository = Depends(get_messaging_repo),
):
    """
    Obtenir l'historique de discussion d'une conversation.
    """
    # TODO: Vérifier que l'utilisateur fait partie des participants de la conversation.
    messages = await messaging_repo.list_messages(conversation_id)
    return [
        MessageResponseDTO(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            content=m.content,
            message_type=m.message_type,
            sent_at=m.sent_at,
        )
        for m in messages
    ]


@router.post("/messages", response_model=MessageResponseDTO, status_code=status.HTTP_201_CREATED)
async def send_message(
    dto: SendMessageDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    messaging_repo: PostgresMessagingRepository = Depends(get_messaging_repo),
):
    """
    Envoyer un message dans une conversation.
    """
    use_case = SendTransversalMessageUseCase(messaging_repo)
    message_dto = await use_case.execute(
        sender_id=current_user["user_id"],
        tenant_id=tenant_id,
        dto=dto,
    )
    return message_dto