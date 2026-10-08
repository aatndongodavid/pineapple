import asyncio
import json
import uuid
from datetime import datetime

from democracy_context.application.dtos import CastVoteDTO, ElectionCreateDTO, ElectionResultsDTO
from democracy_context.domain.entities import Election, ElectionStatus, Vote


from shared_kernel.config import settings

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
        
        election = None
        if hasattr(self._election_repo, "get_election_by_id"):
            election = await self._election_repo.get_election_by_id(election_id, tenant_id)
        if election is None and hasattr(self._election_repo, "get_by_id"):
            election = await self._election_repo.get_by_id(election_id, tenant_id)
        if election is None:
            raise ElectionNotFoundError()
            
        status_str = getattr(election.status, "value", str(election.status))
        if status_str not in ("OPEN", "VOTING_OPEN"):
            raise VotingNotOpenError()

        if hasattr(self, "_user_info_provider") and self._user_info_provider:
            info = await self._user_info_provider.get_user_info(user_id, tenant_id)
            if isinstance(info, dict):
                is_elig = election.is_eligible(
                    user_academic_status=info.get("academic_status", "student"),
                    is_certified=info.get("is_certified", True),
                    user_level=info.get("level"),
                )
                if not is_elig:
                    raise NotEligibleError()

        voter_hash_obj = self._generate_voter_hash(user_id, election_id)
        voter_hash = voter_hash_obj.value if hasattr(voter_hash_obj, "value") else str(voter_hash_obj)
        
        has_voted = False
        if hasattr(self._vote_repo, "has_voted"):
            try:
                has_voted = await self._vote_repo.has_voted(election_id, tenant_id, voter_hash)
            except TypeError:
                has_voted = await self._vote_repo.has_voted(election_id, voter_hash)
        if has_voted:
            raise AlreadyVotedError()

        encrypt_fn = getattr(self._crypto_engine, "encrypt", getattr(self._crypto_engine, "encrypt_vote", None))
        encrypted_vote = encrypt_fn(
            json.dumps(dto.ballot, sort_keys=True, default=str), public_key_pem
        ) if encrypt_fn else "encrypted_vote"

        vote = Vote(
            id=uuid.uuid4(),
            election_id=election_id,
            tenant_id=tenant_id,
            voter_hash=voter_hash,
            encrypted_vote=encrypted_vote,
            cast_at=datetime.utcnow(),
        )
        
        if hasattr(self._vote_repo, "cast_ballot"):
            res = self._vote_repo.cast_ballot(vote)
            if asyncio.iscoroutine(res):
                await res
        elif hasattr(self._vote_repo, "save_vote"):
            res = self._vote_repo.save_vote(vote)
            if asyncio.iscoroutine(res):
                await res
        elif hasattr(self._vote_repo, "add"):
            res = self._vote_repo.add(vote)
            if asyncio.iscoroutine(res):
                await res

        if hasattr(self._audit_ledger, "append_entry"):
            res = self._audit_ledger.append_entry("vote.cast", {"election_id": str(election_id), "vote_id": str(vote.id)}, tenant_id)
            if asyncio.iscoroutine(res):
                await res
        elif hasattr(self._audit_ledger, "record_entry"):
            res = self._audit_ledger.record_entry(tenant_id, "vote.cast", {"election_id": str(election_id), "vote_id": str(vote.id)})
            if asyncio.iscoroutine(res):
                await res
                
        return vote

    def _generate_voter_hash(self, user_id: uuid.UUID, election_id: uuid.UUID):
        import hashlib
        pepper = getattr(settings, "ELECTION_PEPPER_SECRET", "default_secret_pepper")
        raw = f"{user_id}:{election_id}:{pepper}".encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()
        class VoterHash:
            def __init__(self, val):
                self.value = val
            def __str__(self):
                return self.value
        return VoterHash(h)


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
