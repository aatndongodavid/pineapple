# tests/unit/test_domain.py

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

import pytest

from identity_context.domain.entities import User
from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    CampusStatusDisplay,
    VerificationStatus,
)

from democracy_context.domain.entities import (
    Election,
    ElectionStatus,
    MovementStatus,
    VoterHash,
)
from democracy_context.domain.value_objects import AcademicStatus as DemoAcademicStatus
from democracy_context.domain.ports import (
    ElectionRepositoryPort,
    VoteRepositoryPort,
    CryptoEnginePort,
    AuditLedgerPort,
)
from democracy_context.application.use_cases import CastVoteUseCase, AlreadyVotedError, NotEligibleError, VotingNotOpenError
from democracy_context.application.dtos import CastVoteDTO

from shared_kernel.config import settings


# ---------------------------------------------------------------------------
# Fixtures utilitaires
# ---------------------------------------------------------------------------
def make_user(**overrides) -> User:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "matricule": "MAT123",
        "faculty": "Génie",
        "filiere": "Informatique",
        "academic_year": "2026-2027",
        "account_status": AccountStatus.ACTIVE,
        "verification_status": VerificationStatus.UNVERIFIED,
        "academic_status": AcademicStatus.STUDENT,
        "created_at": datetime.utcnow(),
        "password_hash": "hashed",
    }
    defaults.update(overrides)
    return User(**defaults)


# ===========================================================================
# Tests Identity
# ===========================================================================
class TestIdentityCampusStatus:
    def test_archived_account_returns_archived(self):
        user = make_user(account_status=AccountStatus.ARCHIVED)
        assert user.resolve_campus_status() == CampusStatusDisplay.ARCHIVED

    def test_verified_teacher_returns_verified_teacher(self):
        user = make_user(
            academic_status=AcademicStatus.TEACHER,
            verification_status=VerificationStatus.VERIFIED,
        )
        assert user.resolve_campus_status() == CampusStatusDisplay.VERIFIED_TEACHER

    def test_alumni_returns_alumni(self):
        user = make_user(academic_status=AcademicStatus.ALUMNI)
        assert user.resolve_campus_status() == CampusStatusDisplay.ALUMNI

    def test_verified_student_returns_certified_student(self):
        user = make_user(verification_status=VerificationStatus.VERIFIED)
        assert user.resolve_campus_status() == CampusStatusDisplay.CERTIFIED_STUDENT

    def test_pending_certification_returns_pending_certification(self):
        user = make_user(verification_status=VerificationStatus.PENDING)
        assert user.resolve_campus_status() == CampusStatusDisplay.PENDING_CERTIFICATION

    def test_certification_required_returns_pending_certification(self):
        user = make_user(verification_status=VerificationStatus.CERTIFICATION_REQUIRED)
        assert user.resolve_campus_status() == CampusStatusDisplay.PENDING_CERTIFICATION

    def test_unverified_student_returns_not_certified(self):
        user = make_user(verification_status=VerificationStatus.UNVERIFIED)
        assert user.resolve_campus_status() == CampusStatusDisplay.NOT_CERTIFIED


class TestIdentityCertificationExpiry:
    def test_expire_certification_sets_status_to_required(self):
        user = make_user(verification_status=VerificationStatus.VERIFIED)
        user.expire_certification()
        assert user.verification_status == VerificationStatus.CERTIFICATION_REQUIRED


# ===========================================================================
# Tests Democracy
# ===========================================================================
def make_election(**overrides) -> Election:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "title": "Test Election",
        "election_type": "BDE",
        "status": ElectionStatus.VOTING_OPEN,
        "eligibility_rules": {"level": "L3", "certified": True},
        "voting_start_at": datetime.utcnow() - timedelta(hours=1),
        "voting_end_at": datetime.utcnow() + timedelta(hours=1),
        "created_at": datetime.utcnow(),
    }
    defaults.update(overrides)
    return Election(**defaults)


class TestElectionEligibility:
    def test_eligible_student_returns_true(self):
        election = make_election(
            eligibility_rules={"level": "L3", "certified": True}
        )
        assert election.is_eligible(
            user_academic_status="student",
            is_certified=True,
            user_level="L3",
        ) is True

    def test_not_certified_returns_false_when_required(self):
        election = make_election(
            eligibility_rules={"level": "L3", "certified": True}
        )
        assert election.is_eligible(
            user_academic_status="student",
            is_certified=False,
            user_level="L3",
        ) is False

    def test_wrong_level_returns_false(self):
        election = make_election(
            eligibility_rules={"level": "L3", "certified": True}
        )
        assert election.is_eligible(
            user_academic_status="student",
            is_certified=True,
            user_level="L2",
        ) is False


class TestElectionVotingWindow:
    def test_can_vote_during_window(self):
        election = make_election(status=ElectionStatus.VOTING_OPEN)
        now = datetime.utcnow()
        assert election.can_vote(now) is True

    def test_cannot_vote_outside_window(self):
        election = make_election(
            status=ElectionStatus.VOTING_OPEN,
            voting_start_at=datetime.utcnow() + timedelta(hours=1),
            voting_end_at=datetime.utcnow() + timedelta(hours=2),
        )
        assert election.can_vote(datetime.utcnow()) is False

    def test_cannot_vote_when_closed(self):
        election = make_election(status=ElectionStatus.VOTING_CLOSED)
        assert election.can_vote(datetime.utcnow()) is False

    def test_close_voting_changes_status(self):
        election = make_election(status=ElectionStatus.VOTING_OPEN)
        election.close_voting()
        assert election.status == ElectionStatus.VOTING_CLOSED


# --- Tests du use case CastVoteUseCase avec mocks ---
@pytest.mark.asyncio
class TestCastVote:
    async def _prepare_use_case(self, election_repo=None, vote_repo=None, crypto_engine=None, audit_ledger=None, user_info_provider=None):
        election_repo = election_repo or AsyncMock(spec=ElectionRepositoryPort)
        vote_repo = vote_repo or AsyncMock(spec=VoteRepositoryPort)
        crypto_engine = crypto_engine or AsyncMock(spec=CryptoEnginePort)
        audit_ledger = audit_ledger or AsyncMock(spec=AuditLedgerPort)
        user_info_provider = user_info_provider or AsyncMock()

        use_case = CastVoteUseCase(
            election_repo=election_repo,
            vote_repo=vote_repo,
            crypto_engine=crypto_engine,
            audit_ledger=audit_ledger,
            user_info_provider=user_info_provider,
        )
        return use_case, election_repo, vote_repo, crypto_engine, audit_ledger

    async def test_generate_voter_hash_is_deterministic_and_anonymous(self):
        """Vérifie que le hash est déterministe et ne contient pas l'ID en clair."""
        use_case, _, _, _, _ = await self._prepare_use_case()
        user_id = uuid.uuid4()
        election_id = uuid.uuid4()
        pepper = settings.ELECTION_PEPPER_SECRET
        hash1 = use_case._generate_voter_hash(user_id, election_id)
        hash2 = use_case._generate_voter_hash(user_id, election_id)
        assert hash1.value == hash2.value  # déterministe
        assert str(user_id) not in hash1.value  # anonyme
        assert str(election_id) not in hash1.value

    async def test_cast_vote_raises_already_voted_if_has_voted_true(self):
        use_case, election_repo, vote_repo, crypto_engine, audit_ledger = await self._prepare_use_case()
        election = make_election()
        election_repo.get_election_by_id.return_value = election
        vote_repo.has_voted.return_value = True
        user_info_provider = AsyncMock()
        user_info_provider.get_user_info.return_value = {
            "academic_status": "student",
            "is_certified": True,
            "level": "L3",
        }
        use_case._user_info_provider = user_info_provider  # réassigner

        dto = CastVoteDTO(election_id=election.id, choice_id="choice1")
        with pytest.raises(AlreadyVotedError):
            await use_case.execute(
                user_id=uuid.uuid4(),
                tenant_id=election.tenant_id,
                dto=dto,
                public_key_pem="fake",
            )
        vote_repo.cast_ballot.assert_not_called()

    async def test_cast_vote_success_calls_repositories(self):
        use_case, election_repo, vote_repo, crypto_engine, audit_ledger = await self._prepare_use_case()
        election = make_election()
        election_repo.get_election_by_id.return_value = election
        vote_repo.has_voted.return_value = False
        crypto_engine.encrypt_choice.return_value = MagicMock()
        user_info_provider = AsyncMock()
        user_info_provider.get_user_info.return_value = {
            "academic_status": "student",
            "is_certified": True,
            "level": "L3",
        }
        use_case._user_info_provider = user_info_provider

        dto = CastVoteDTO(election_id=election.id, choice_id="choice1")
        await use_case.execute(
            user_id=uuid.uuid4(),
            tenant_id=election.tenant_id,
            dto=dto,
            public_key_pem="fake",
        )
        vote_repo.cast_ballot.assert_called_once()
        audit_ledger.append_entry.assert_called_once()

    async def test_cast_vote_not_eligible_raises(self):
        use_case, election_repo, vote_repo, crypto_engine, audit_ledger = await self._prepare_use_case()
        election = make_election(
            eligibility_rules={"level": "L3", "certified": True}
        )
        election_repo.get_election_by_id.return_value = election
        vote_repo.has_voted.return_value = False
        user_info_provider = AsyncMock()
        user_info_provider.get_user_info.return_value = {
            "academic_status": "student",
            "is_certified": False,  # non certifié
            "level": "L3",
        }
        use_case._user_info_provider = user_info_provider

        dto = CastVoteDTO(election_id=election.id, choice_id="choice1")
        with pytest.raises(NotEligibleError):
            await use_case.execute(
                user_id=uuid.uuid4(),
                tenant_id=election.tenant_id,
                dto=dto,
                public_key_pem="fake",
            )
        vote_repo.cast_ballot.assert_not_called()

    async def test_cast_vote_not_open_raises(self):
        use_case, election_repo, vote_repo, crypto_engine, audit_ledger = await self._prepare_use_case()
        election = make_election(status=ElectionStatus.VOTING_CLOSED)
        election_repo.get_election_by_id.return_value = election
        dto = CastVoteDTO(election_id=election.id, choice_id="choice1")
        with pytest.raises(VotingNotOpenError):
            await use_case.execute(
                user_id=uuid.uuid4(),
                tenant_id=election.tenant_id,
                dto=dto,
                public_key_pem="fake",
            )