import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional, Protocol
from uuid import UUID, uuid4

from democracy_context.application.dtos import (
    CastVoteDTO,
    ElectionCreateDTO,
    ElectionResponseDTO,
    ElectionResultsDTO,
)
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
from shared_kernel.config import settings


class UserInfoProvider(Protocol):
    """Fournit les informations académiques nécessaires à la vérification d'éligibilité."""

    def get_user_info(self, user_id: UUID) -> dict:
        """
        Retourne un dictionnaire contenant au moins :
        - academic_status: str
        - is_certified: bool
        - level: str
        """
        ...


class ElectionNotFoundError(Exception):
    pass


class AlreadyVotedError(Exception):
    pass


class NotEligibleError(Exception):
    pass


class VotingNotOpenError(Exception):
    pass


class TallyNotAllowedError(Exception):
    pass


class CreateElectionUseCase:
    """Crée une élection et enregistre l'événement dans le registre d'audit."""

    def __init__(
        self,
        election_repo: ElectionRepositoryPort,
        audit_ledger: AuditLedgerPort,
    ):
        self._election_repo = election_repo
        self._audit_ledger = audit_ledger

    def execute(self, dto: ElectionCreateDTO, tenant_id: UUID) -> Election:
        election = Election(
            id=uuid4(),
            tenant_id=tenant_id,
            title=dto.title,
            election_type=dto.election_type,
            status=ElectionStatus.DRAFT,
            eligibility_rules=dto.eligibility_rules,
            voting_start_at=dto.voting_start_at,
            voting_end_at=dto.voting_end_at,
        )

        saved = self._election_repo.save_election(election)

        self._audit_ledger.append_entry(
            action="election.created",
            metadata={
                "election_id": str(saved.id),
                "title": saved.title,
                "tenant_id": str(tenant_id),
            },
            tenant_id=tenant_id,
        )

        return saved


class CastVoteUseCase:
    """Use case de vote : anonymisation, éligibilité, unicité, chiffrement et audit."""

    def __init__(
        self,
        election_repo: ElectionRepositoryPort,
        vote_repo: VoteRepositoryPort,
        crypto_engine: CryptoEnginePort,
        audit_ledger: AuditLedgerPort,
        user_info_provider: UserInfoProvider,
    ):
        self._election_repo = election_repo
        self._vote_repo = vote_repo
        self._crypto_engine = crypto_engine
        self._audit_ledger = audit_ledger
        self._user_info_provider = user_info_provider

    def _generate_voter_hash(self, user_id: UUID, election_id: UUID) -> VoterHash:
        """Génère un hash anonyme de l'électeur en utilisant un pepper système."""
        pepper = settings.ELECTION_PEPPER_SECRET.encode()
        message = f"{user_id}:{election_id}".encode()
        digest = hmac.new(pepper, message, hashlib.sha256).hexdigest()
        return VoterHash(value=digest)

    def execute(
        self,
        user_id: UUID,
        tenant_id: UUID,
        dto: CastVoteDTO,
        public_key_pem: str,
    ) -> None:
        election = self._election_repo.get_election_by_id(dto.election_id, tenant_id)
        if not election:
            raise ElectionNotFoundError("Election not found")

        if not election.can_vote(datetime.utcnow()):
            raise VotingNotOpenError("Voting is not currently open")

        # Récupération des infos académiques de l'utilisateur
        user_info = self._user_info_provider.get_user_info(user_id)

        # Vérification de l'éligibilité
        if not election.is_eligible(
            user_academic_status=user_info.get("academic_status", ""),
            is_certified=user_info.get("is_certified", False),
            user_level=user_info.get("level", ""),
        ):
            raise NotEligibleError("User is not eligible for this election")

        # Génération du hash anonyme et vérification d'unicité
        voter_hash = self._generate_voter_hash(user_id, dto.election_id)
        if self._vote_repo.has_voted(voter_hash, dto.election_id):
            raise AlreadyVotedError("User has already voted in this election")

        # Chiffrement du choix
        choice_data = {"choice_id": dto.choice_id}
        encrypted = self._crypto_engine.encrypt_choice(choice_data, public_key_pem)

        # Création du bulletin strictement anonyme
        ballot = Ballot(
            id=uuid4(),
            election_id=dto.election_id,
            tenant_id=tenant_id,
            voter_hash=voter_hash,
            encrypted_vote=encrypted,
            cast_at=datetime.utcnow(),
        )
        self._vote_repo.cast_ballot(ballot)

        # Enregistrement dans le registre d'audit
        self._audit_ledger.append_entry(
            action="vote.cast",
            metadata={
                "election_id": str(dto.election_id),
                "voter_hash": voter_hash.value,
                "tenant_id": str(tenant_id),
            },
            tenant_id=tenant_id,
        )


class TallyResultsUseCase:
    """Dépouillement des bulletins et publication des résultats après clôture."""

    def __init__(
        self,
        election_repo: ElectionRepositoryPort,
        vote_repo: VoteRepositoryPort,
        crypto_engine: CryptoEnginePort,
        audit_ledger: AuditLedgerPort,
    ):
        self._election_repo = election_repo
        self._vote_repo = vote_repo
        self._crypto_engine = crypto_engine
        self._audit_ledger = audit_ledger

    def execute(
        self, election_id: UUID, tenant_id: UUID, private_key_pem: str
    ) -> ElectionResultsDTO:
        election = self._election_repo.get_election_by_id(election_id, tenant_id)
        if not election:
            raise ElectionNotFoundError("Election not found")

        if election.status != ElectionStatus.VOTING_CLOSED:
            raise TallyNotAllowedError("Election must be closed before tallying")

        # Récupération des bulletins chiffrés
        ballots = self._vote_repo.get_encrypted_ballots(election_id)
        encrypted_ballots = [b.encrypted_vote for b in ballots if b.is_valid]

        # Déchiffrement et comptage
        tally = self._crypto_engine.decrypt_ballots(encrypted_ballots, private_key_pem)

        # Mise à jour du statut
        election.status = ElectionStatus.RESULTS_PUBLISHED
        self._election_repo.save_election(election)

        # Audit de publication
        self._audit_ledger.append_entry(
            action="election.results_published",
            metadata={
                "election_id": str(election_id),
                "total_ballots": len(encrypted_ballots),
                "tenant_id": str(tenant_id),
            },
            tenant_id=tenant_id,
        )

        return ElectionResultsDTO(
            election_id=election_id,
            total_ballots=len(encrypted_ballots),
            tally_results=tally,
            published_at=datetime.utcnow(),
        )