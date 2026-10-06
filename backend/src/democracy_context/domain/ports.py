import uuid
from abc import ABC, abstractmethod
from typing import Optional
from democracy_context.domain.entities import Election, Vote


class ElectionRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, election_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Election]:
        pass

    async def get_election_by_id(self, election_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Election]:
        return await self.get_by_id(election_id, tenant_id)

    @abstractmethod
    async def save(self, election: Election) -> Election:
        pass


class VoteRepositoryPort(ABC):
    @abstractmethod
    async def has_voted(self, election_id: uuid.UUID, voter_hash: str) -> bool:
        pass

    @abstractmethod
    async def save_vote(self, vote: Vote) -> Vote:
        pass

    async def cast_ballot(self, vote: Vote) -> Vote:
        return await self.save_vote(vote)


class CryptoEnginePort(ABC):
    @abstractmethod
    def generate_voter_hash(self, user_id: uuid.UUID, election_id: uuid.UUID, pepper: str) -> str:
        pass

    @abstractmethod
    def encrypt_vote(self, candidate_id: str, election_key: str) -> str:
        pass

    def encrypt(self, payload: str, key: str) -> str:
        return self.encrypt_vote(payload, key)

    def encrypt_choice(self, choice_id: str, key: str) -> str:
        return self.encrypt_vote(choice_id, key)


class AuditLedgerPort(ABC):
    @abstractmethod
    async def record_entry(self, tenant_id: uuid.UUID, action: str, metadata: dict) -> None:
        pass

    async def append_entry(self, action: str, metadata: dict, tenant_id: uuid.UUID = None) -> None:
        await self.record_entry(tenant_id, action, metadata)
