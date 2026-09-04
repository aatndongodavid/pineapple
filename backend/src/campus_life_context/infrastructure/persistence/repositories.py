from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from campus_life_context.domain.entities import (
    Conversation,
    MarketplaceListing,
    Message,
    RideShare,
)
from campus_life_context.domain.ports import (
    MarketplaceRepositoryPort,
    MessagingRepositoryPort,
    RideRepositoryPort,
)
from campus_life_context.domain.value_objects import (
    ListingCategory,
    ListingStatus,
    MessageType,
    RideLocation,
    RideStatus,
)
from campus_life_context.infrastructure.persistence.models import (
    ConversationModel,
    MarketplaceListingModel,
    MessageModel,
    RideShareModel,
)
from shared_kernel.domain.value_objects import Money


class PostgresMarketplaceRepository(MarketplaceRepositoryPort):
    """Implémentation PostgreSQL du port MarketplaceRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: MarketplaceListingModel) -> MarketplaceListing:
        return MarketplaceListing(
            id=model.id,
            tenant_id=model.tenant_id,
            seller_id=model.seller_id,
            title=model.title,
            description=model.description,
            price=Money(amount=Decimal(model.price_amount), currency="XAF"),
            category=model.category,
            status=model.status,
            image_urls=model.image_urls,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(listing: MarketplaceListing) -> MarketplaceListingModel:
        return MarketplaceListingModel(
            id=listing.id,
            tenant_id=listing.tenant_id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            price_amount=int(listing.price.amount),
            category=listing.category,
            status=listing.status,
            image_urls=listing.image_urls,
            created_at=listing.created_at,
        )

    async def save_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        async with self._session_factory() as session:
            model = self._to_model(listing)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return listing

    async def get_listing_by_id(self, listing_id: UUID, tenant_id: UUID) -> Optional[MarketplaceListing]:
        async with self._session_factory() as session:
            stmt = select(MarketplaceListingModel).where(
                MarketplaceListingModel.id == listing_id,
                MarketplaceListingModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_listings(
        self, tenant_id: UUID, category: Optional[ListingCategory]
    ) -> List[MarketplaceListing]:
        async with self._session_factory() as session:
            stmt = select(MarketplaceListingModel).where(
                MarketplaceListingModel.tenant_id == tenant_id
            )
            if category is not None:
                stmt = stmt.where(MarketplaceListingModel.category == category)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresRideRepository(RideRepositoryPort):
    """Implémentation PostgreSQL du port RideRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: RideShareModel) -> RideShare:
        # Convertir les listes de strings en UUIDs
        passenger_ids = [UUID(pid) for pid in model.passenger_ids]
        return RideShare(
            id=model.id,
            tenant_id=model.tenant_id,
            driver_id=model.driver_id,
            departure=RideLocation(address_name=model.departure_name),
            destination=RideLocation(address_name=model.destination_name),
            departure_time=model.departure_time,
            total_seats=model.total_seats,
            available_seats=model.available_seats,
            price_per_seat=Money(amount=Decimal(model.price_per_seat), currency="XAF"),
            passenger_ids=passenger_ids,
            status=model.status,
        )

    @staticmethod
    def _to_model(ride: RideShare) -> RideShareModel:
        passenger_ids_str = [str(pid) for pid in ride.passenger_ids]
        return RideShareModel(
            id=ride.id,
            tenant_id=ride.tenant_id,
            driver_id=ride.driver_id,
            departure_name=ride.departure.address_name,
            destination_name=ride.destination.address_name,
            departure_time=ride.departure_time,
            total_seats=ride.total_seats,
            available_seats=ride.available_seats,
            price_per_seat=int(ride.price_per_seat.amount),
            passenger_ids=passenger_ids_str,
            status=ride.status,
        )

    async def save_ride(self, ride: RideShare) -> RideShare:
        async with self._session_factory() as session:
            model = self._to_model(ride)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return ride

    async def get_ride_by_id(self, ride_id: UUID, tenant_id: UUID) -> Optional[RideShare]:
        async with self._session_factory() as session:
            stmt = select(RideShareModel).where(
                RideShareModel.id == ride_id,
                RideShareModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def search_rides(
        self, tenant_id: UUID, departure_query: Optional[str]
    ) -> List[RideShare]:
        async with self._session_factory() as session:
            stmt = select(RideShareModel).where(RideShareModel.tenant_id == tenant_id)
            if departure_query:
                # Recherche partielle insensible à la casse sur l'adresse de départ
                stmt = stmt.where(
                    RideShareModel.departure_name.ilike(f"%{departure_query}%")
                )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresMessagingRepository(MessagingRepositoryPort):
    """Implémentation PostgreSQL du port MessagingRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_conversation_entity(model: ConversationModel) -> Conversation:
        participant_ids = [UUID(pid) for pid in model.participant_ids]
        return Conversation(
            id=model.id,
            tenant_id=model.tenant_id,
            participant_ids=participant_ids,
            context_type=model.context_type,
            context_id=model.context_id,
            last_message_at=model.last_message_at,
        )

    @staticmethod
    def _to_conversation_model(conversation: Conversation) -> ConversationModel:
        participant_ids_str = [str(pid) for pid in conversation.participant_ids]
        return ConversationModel(
            id=conversation.id,
            tenant_id=conversation.tenant_id,
            participant_ids=participant_ids_str,
            context_type=conversation.context_type,
            context_id=conversation.context_id,
            last_message_at=conversation.last_message_at,
        )

    @staticmethod
    def _to_message_entity(model: MessageModel) -> Message:
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            sender_id=model.sender_id,
            content=model.content,
            message_type=model.message_type,
            sent_at=model.sent_at,
        )

    @staticmethod
    def _to_message_model(message: Message) -> MessageModel:
        return MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            sent_at=message.sent_at,
        )

    async def get_or_create_conversation(
        self,
        tenant_id: UUID,
        participants: List[UUID],
        context_type: str,
        context_id: UUID,
    ) -> Conversation:
        async with self._session_factory() as session:
            # Chercher une conversation existante avec le même contexte et les mêmes participants
            # Pour simplifier, on compare les listes triées de participants.
            stmt = select(ConversationModel).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.context_type == context_type,
                ConversationModel.context_id == context_id,
            )
            result = await session.execute(stmt)
            existing = result.scalars().all()

            # Normaliser la liste des participants pour comparaison
            participants_set = set(participants)
            for conv_model in existing:
                conv_participants = {UUID(pid) for pid in conv_model.participant_ids}
                if conv_participants == participants_set:
                    return self._to_conversation_entity(conv_model)

            # Aucune conversation correspondante : créer une nouvelle
            conversation = Conversation(
                id=uuid4(),
                tenant_id=tenant_id,
                participant_ids=participants,
                context_type=context_type,
                context_id=context_id,
                last_message_at=None,
            )
            model = self._to_conversation_model(conversation)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            return conversation

    async def save_message(self, message: Message) -> Message:
        async with self._session_factory() as session:
            model = self._to_message_model(message)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            # Mettre à jour last_message_at de la conversation
            conv_model = await session.get(ConversationModel, message.conversation_id)
            if conv_model:
                conv_model.last_message_at = message.sent_at
                await session.commit()
        return message

    async def list_messages(self, conversation_id: UUID, limit: int = 50) -> List[Message]:
        async with self._session_factory() as session:
            stmt = (
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.sent_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_message_entity(m) for m in models]