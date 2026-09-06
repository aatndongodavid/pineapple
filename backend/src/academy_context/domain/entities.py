from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class ElectionStatus(str, Enum):
    DRAFT = "DRAFT"
    CAMPAIGN = "CAMPAIGN"
    VOTING_OPEN = "VOTING_OPEN"
    VOTING_CLOSED = "VOTING_CLOSED"
    RESULTS_PUBLISHED = "RESULTS_PUBLISHED"
    ARCHIVED = "ARCHIVED"


class MovementStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class VoterHash:
    """Hash anonymisé de l'électeur : séparation stricte entre identité et bulletin."""
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("VoterHash cannot be empty")


@dataclass(frozen=True)
class EncryptedVote:
    """Bulletin chiffré. Aucun lien direct avec UserID."""
    data: bytes

    def __post_init__(self) -> None:
        if not self.data:
            raise ValueError("EncryptedVote cannot be empty")


@dataclass
class Candidate:
    id: UUID
    movement_id: UUID
    user_id: UUID  # référence à l'utilisateur candidat
    position: str   # ex: "Président"
    order: int = 0


@dataclass
class Movement:
    id: UUID
    election_id: UUID
    tenant_id: UUID
    name: str
    slogan: str
    program_text: str
    status: MovementStatus
    candidates: List[Candidate] = field(default_factory=list)


@dataclass
class Ballot:
    id: UUID
    election_id: UUID
    tenant_id: UUID
    voter_hash: VoterHash
    encrypted_vote: EncryptedVote
    cast_at: datetime
    is_valid: bool = True


@dataclass
class Election:
    """
    Agrégat racine du contexte Democracy.
    Encapsule les règles d'éligibilité, de fenêtre de vote et de clôture.
    """
    id: UUID
    tenant_id: UUID
    title: str
    election_type: str  # ex: "BDE", "Délégué", etc.
    status: ElectionStatus
    eligibility_rules: Dict[str, Any]  # exemple: {"level": "L3", "filiere": ["GL", "SI"], "certified": True}
    voting_start_at: datetime
    voting_end_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_eligible(self, user_academic_status: str, is_certified: bool, user_level: str) -> bool:
        """
        Vérifie l'éligibilité d'un utilisateur selon les règles définies.
        Règles supportées : niveau requis, filière(s) autorisée(s), certification obligatoire.
        """
        rules = self.eligibility_rules

        # Vérification du niveau
        required_level = rules.get("level")
        if required_level and user_level != required_level:
            return False

        # Vérification de la filière
        allowed_filieres = rules.get("filiere")
        if allowed_filieres and isinstance(allowed_filieres, list):
            if user_academic_status not in allowed_filieres:
                return False
        elif allowed_filieres and isinstance(allowed_filieres, str):
            if user_academic_status != allowed_filieres:
                return False

        # Vérification de la certification
        require_certified = rules.get("certified", False)
        if require_certified and not is_certified:
            return False

        return True

    def can_vote(self, now: datetime) -> bool:
        """Le vote est possible uniquement pendant la fenêtre et si le statut est VOTING_OPEN."""
        return (
            self.status == ElectionStatus.VOTING_OPEN
            and self.voting_start_at <= now <= self.voting_end_at
        )

    def close_voting(self) -> None:
        """Passe le statut de l'élection à VOTING_CLOSED."""
        if self.status == ElectionStatus.VOTING_OPEN:
            self.status = ElectionStatus.VOTING_CLOSED