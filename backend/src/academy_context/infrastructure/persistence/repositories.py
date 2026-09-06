import base64
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from democracy_context.domain.entities import (
    AuditLedgerEntry,
    Ballot,
    Election,
    ElectionStatus,
    EncryptedVote,
    VoterHash,
)
from democracy_context.domain.ports import (
    AuditLedgerPort,
    CryptoEnginePort,
    ElectionRepositoryPort,
    VoteRepositoryPort,
)
from democracy_context.infrastructure.persistence.models import (
    AuditLogModel,
    BallotModel,
    ElectionModel,
)


# ---------------------------------------------------------------------------
# Helpers de conversion
# ---------------------------------------------------------------------------

def _election_model_to_entity(model: ElectionModel) -> Election:
    return Election(
        id=model.id,
        tenant_id=model.tenant_id,
        title=model.title,
        election_type=model.election_type,
        status=model.status,
        eligibility_rules=model.eligibility_rules,
        voting_start_at=model.voting_start_at,
        voting_end_at=model.voting_end_at,
        created_at=model.created_at,
    )


def _election_entity_to_model(election: Election) -> ElectionModel:
    return ElectionModel(
        id=election.id,
        tenant_id=election.tenant_id,
        title=election.title,
        election_type=election.election_type,
        status=election.status,
        eligibility_rules=election.eligibility_rules,
        voting_start_at=election.voting_start_at,
        voting_end_at=election.voting_end_at,
        created_at=election.created_at,
    )


def _ballot_model_to_entity(model: BallotModel) -> Ballot:
    return Ballot(
        id=model.id,
        election_id=model.election_id,
        tenant_id=model.tenant_id,
        voter_hash=VoterHash(value=model.voter_hash),
        encrypted_vote=EncryptedVote(data=base64.b64decode(model.encrypted_vote)),
        cast_at=model.cast_at,
        is_valid=getattr(model, "is_valid", True),
    )


def _ballot_entity_to_model(ballot: Ballot) -> BallotModel:
    return BallotModel(
        id=ballot.id,
        election_id=ballot.election_id,
        tenant_id=ballot.tenant_id,
        voter_hash=ballot.voter_hash.value,
        encrypted_vote=base64.b64encode(ballot.encrypted_vote.data).decode("utf-8"),
        cast_at=ballot.cast_at,
    )


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

class PostgresElectionRepository(ElectionRepositoryPort):
    """Implémentation PostgreSQL du port ElectionRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def save_election(self, election: Election) -> Election:
        async with self._session_factory() as session:
            model = _election_entity_to_model(election)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return election

    async def get_election_by_id(self, election_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Election]:
        async with self._session_factory() as session:
            stmt = select(ElectionModel).where(
                ElectionModel.id == election_id,
                ElectionModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return _election_model_to_entity(model) if model else None

    async def list_elections_by_tenant(
        self, tenant_id: uuid.UUID, status: Optional[ElectionStatus] = None
    ) -> List[Election]:
        async with self._session_factory() as session:
            stmt = select(ElectionModel).where(ElectionModel.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(ElectionModel.status == status)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [_election_model_to_entity(m) for m in models]


class PostgresVoteRepository(VoteRepositoryPort):
    """Implémentation PostgreSQL du port VoteRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def has_voted(self, voter_hash: VoterHash, election_id: uuid.UUID) -> bool:
        async with self._session_factory() as session:
            stmt = select(BallotModel).where(
                BallotModel.election_id == election_id,
                BallotModel.voter_hash == voter_hash.value,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def cast_ballot(self, ballot: Ballot) -> Ballot:
        async with self._session_factory() as session:
            model = _ballot_entity_to_model(ballot)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return ballot

    async def get_encrypted_ballots(self, election_id: uuid.UUID) -> List[Ballot]:
        async with self._session_factory() as session:
            stmt = select(BallotModel).where(BallotModel.election_id == election_id)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [_ballot_model_to_entity(m) for m in models]


class RSACryptoEngine(CryptoEnginePort):
    """Implémentation RSA/ECIES-like du moteur cryptographique."""

    def encrypt_choice(self, choice_data: dict, public_key_pem: str) -> EncryptedVote:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        plaintext = json.dumps(choice_data).encode("utf-8")
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return EncryptedVote(data=ciphertext)

    def decrypt_ballots(
        self, encrypted_ballots: List[EncryptedVote], private_key_pem: str
    ) -> Dict[str, int]:
        private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        tally: Dict[str, int] = {}
        for ballot in encrypted_ballots:
            try:
                plaintext = private_key.decrypt(
                    ballot.data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
                choice_data = json.loads(plaintext.decode("utf-8"))
                choice_id = choice_data.get("choice_id")
                if choice_id:
                    tally[choice_id] = tally.get(choice_id, 0) + 1
            except Exception:
                # Ignorer les bulletins invalides ou corrompus
                continue
        return tally


class PostgresAuditLedgerRepository(AuditLedgerPort):
    """Implémentation PostgreSQL du journal d'audit immuable."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def append_entry(
        self, action: str, metadata: dict, tenant_id: uuid.UUID
    ) -> AuditLedgerEntry:
        import hashlib
        payload = f"{action}|{json.dumps(metadata, sort_keys=True)}|{tenant_id}"
        entry_hash = hashlib.sha256(payload.encode()).hexdigest()

        entry = AuditLedgerEntry(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action=action,
            metadata=metadata,
            hash=entry_hash,
            created_at=datetime.utcnow(),
        )

        model = AuditLogModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            action=entry.action,
            metadata=entry.metadata,
            hash=entry.hash,
            created_at=entry.created_at,
        )

        async with self._session_factory() as session:
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return entry