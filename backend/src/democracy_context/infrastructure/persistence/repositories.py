import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from democracy_context.domain.entities import AuditLedgerEntry, Election, ElectionStatus, Vote
from democracy_context.infrastructure.persistence.models import (
    DemocracyAuditLogModel,
    ElectionModel,
    VoteModel,
)


class PostgresElectionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: ElectionModel) -> Election:
        return Election(
            id=model.id,
            tenant_id=model.tenant_id,
            title=model.title,
            election_type=model.election_type,
            status=model.status,
            eligibility_rules=model.eligibility_rules,
            voting_start_at=model.voting_start_at,
            voting_end_at=model.voting_end_at,
        )

    async def add(self, election: Election) -> Election:
        model = ElectionModel(
            id=election.id,
            tenant_id=election.tenant_id,
            title=election.title,
            election_type=election.election_type,
            status=election.status,
            eligibility_rules=election.eligibility_rules,
            config={},
            voting_start_at=election.voting_start_at,
            voting_end_at=election.voting_end_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return election

    async def get_by_id(self, election_id: uuid.UUID, tenant_id: uuid.UUID) -> Election | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ElectionModel).where(
                    ElectionModel.id == election_id,
                    ElectionModel.tenant_id == tenant_id,
                )
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_elections_by_tenant(self, tenant_id: uuid.UUID) -> list[Election]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ElectionModel).where(ElectionModel.tenant_id == tenant_id)
            )
            return [self._to_entity(model) for model in result.scalars().all()]


class PostgresVoteRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def has_voted(self, election_id: uuid.UUID, tenant_id: uuid.UUID, voter_hash: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                select(VoteModel).where(
                    VoteModel.election_id == election_id,
                    VoteModel.tenant_id == tenant_id,
                    VoteModel.voter_hash == voter_hash,
                )
            )
            return result.scalar_one_or_none() is not None

    async def add(self, vote: Vote) -> Vote:
        model = VoteModel(
            id=vote.id,
            election_id=vote.election_id,
            tenant_id=vote.tenant_id,
            voter_hash=vote.voter_hash,
            encrypted_vote=vote.encrypted_vote,
            cast_at=vote.cast_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return vote

    async def list_by_election(self, election_id: uuid.UUID, tenant_id: uuid.UUID) -> list[Vote]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(VoteModel).where(
                    VoteModel.election_id == election_id,
                    VoteModel.tenant_id == tenant_id,
                )
            )
            return [
                Vote(
                    id=model.id,
                    election_id=model.election_id,
                    tenant_id=model.tenant_id,
                    voter_hash=model.voter_hash,
                    encrypted_vote=model.encrypted_vote,
                    cast_at=model.cast_at,
                )
                for model in result.scalars().all()
            ]


class RSACryptoEngine:
    def encrypt(self, payload: str, public_key_pem: str) -> str:
        return payload

    def decrypt(self, payload: str, private_key_pem: str) -> str:
        return payload


class PostgresAuditLedgerRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def append_entry(
        self, action: str, metadata: dict[str, Any], tenant_id: uuid.UUID
    ) -> AuditLedgerEntry:
        payload = f"{action}|{json.dumps(metadata, sort_keys=True, default=str)}|{tenant_id}"
        entry = AuditLedgerEntry(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action=action,
            metadata=metadata,
            hash=hashlib.sha256(payload.encode()).hexdigest(),
            created_at=datetime.utcnow(),
        )
        model = DemocracyAuditLogModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            action=entry.action,
            metadata_=entry.metadata,
            hash=entry.hash,
            created_at=entry.created_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return entry
