import json
import uuid
from datetime import datetime

from democracy_context.application.dtos import CastVoteDTO, ElectionCreateDTO, ElectionResultsDTO
from democracy_context.domain.entities import Election, ElectionStatus, Vote


class ElectionNotFoundError(Exception):
    pass


class VotingNotOpenError(Exception):
    pass


class NotEligibleError(Exception):
    pass


class AlreadyVotedError(Exception):
    pass


class TallyNotAllowedError(Exception):
    pass


class CreateElectionUseCase:
    def __init__(self, election_repo, audit_ledger):
        self._election_repo = election_repo
        self._audit_ledger = audit_ledger

    async def execute(self, dto: ElectionCreateDTO, tenant_id: uuid.UUID) -> Election:
        election = Election(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            title=dto.title,
            election_type=dto.election_type,
            status=ElectionStatus.DRAFT,
            eligibility_rules=dto.eligibility_rules,
            voting_start_at=dto.voting_start_at,
            voting_end_at=dto.voting_end_at,
        )
        await self._election_repo.add(election)
        await self._audit_ledger.append_entry(
            "election.created", {"election_id": str(election.id)}, tenant_id
        )
        return election


class CastVoteUseCase:
    def __init__(self, election_repo, vote_repo, crypto_engine, audit_ledger, user_info_provider):
        self._election_repo = election_repo
        self._vote_repo = vote_repo
        self._crypto_engine = crypto_engine
        self._audit_ledger = audit_ledger
        self._user_info_provider = user_info_provider

    async def execute(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        dto: CastVoteDTO,
        public_key_pem: str,
    ) -> Vote:
        election_id = dto.election_id
        if election_id is None:
            raise ElectionNotFoundError()
        election = await self._election_repo.get_by_id(election_id, tenant_id)
        if election is None:
            raise ElectionNotFoundError()
        if election.status != ElectionStatus.OPEN:
            raise VotingNotOpenError()

        voter_hash = str(user_id)
        if await self._vote_repo.has_voted(election_id, tenant_id, voter_hash):
            raise AlreadyVotedError()

        encrypted_vote = self._crypto_engine.encrypt(
            json.dumps(dto.ballot, sort_keys=True, default=str), public_key_pem
        )
        vote = Vote(
            id=uuid.uuid4(),
            election_id=election_id,
            tenant_id=tenant_id,
            voter_hash=voter_hash,
            encrypted_vote=encrypted_vote,
            cast_at=datetime.utcnow(),
        )
        await self._vote_repo.add(vote)
        await self._audit_ledger.append_entry(
            "vote.cast", {"election_id": str(election_id), "vote_id": str(vote.id)}, tenant_id
        )
        return vote


class TallyResultsUseCase:
    def __init__(self, election_repo, vote_repo, crypto_engine, audit_ledger):
        self._election_repo = election_repo
        self._vote_repo = vote_repo
        self._crypto_engine = crypto_engine
        self._audit_ledger = audit_ledger

    async def execute(
        self, election_id: uuid.UUID, tenant_id: uuid.UUID, private_key_pem: str
    ) -> ElectionResultsDTO:
        election = await self._election_repo.get_by_id(election_id, tenant_id)
        if election is None:
            raise ElectionNotFoundError()
        votes = await self._vote_repo.list_by_election(election_id, tenant_id)
        await self._audit_ledger.append_entry(
            "election.tallied", {"election_id": str(election_id), "votes": len(votes)}, tenant_id
        )
        return ElectionResultsDTO(
            election_id=election_id,
            tenant_id=tenant_id,
            results={"total_votes": len(votes)},
        )
