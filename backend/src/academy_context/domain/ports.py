from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from democracy_context.domain.entities import (
    AuditLedgerEntry,
    Ballot,
    Election,
    ElectionStatus,
    EncryptedVote,
    VoterHash,
)


class ElectionRepositoryPort(ABC):
    """Port de persistance pour l'agrégat Election."""

    @abstractmethod
    def save_election(self, election: Election) -> Election:
        """Sauvegarde une élection (création ou mise à jour)."""
        raise NotImplementedError

    @abstractmethod
    def get_election_by_id(self, election_id: UUID, tenant_id: UUID) -> Optional[Election]:
        """Récupère une élection par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def list_elections_by_tenant(
        self, tenant_id: UUID, status: Optional[ElectionStatus] = None
    ) -> List[Election]:
        """Liste les élections d'un tenant, avec filtrage optionnel par statut."""
        raise NotImplementedError


class VoteRepositoryPort(ABC):
    """Port de persistance pour les bulletins de vote."""

    @abstractmethod
    def has_voted(self, voter_hash: VoterHash, election_id: UUID) -> bool:
        """Vérifie si un électeur (haché) a déjà voté pour une élection donnée."""
        raise NotImplementedError

    @abstractmethod
    def cast_ballot(self, ballot: Ballot) -> Ballot:
        """Enregistre un bulletin de vote."""
        raise NotImplementedError

    @abstractmethod
    def get_encrypted_ballots(self, election_id: UUID) -> List[Ballot]:
        """Récupère tous les bulletins chiffrés d'une élection."""
        raise NotImplementedError


class CryptoEnginePort(ABC):
    """Port pour le moteur cryptographique des votes."""

    @abstractmethod
    def encrypt_choice(self, choice_data: dict, public_key_pem: str) -> EncryptedVote:
        """Chiffre le choix d'un électeur avec la clé publique fournie."""
        raise NotImplementedError

    @abstractmethod
    def decrypt_ballots(
        self, encrypted_ballots: List[EncryptedVote], private_key_pem: str
    ) -> Dict[str, int]:
        """
        Déchiffre les bulletins et retourne un comptage anonymisé :
        mapping { "candidate_id": nombre_de_voix }.
        """
        raise NotImplementedError


class AuditLedgerPort(ABC):
    """Port pour le journal d'audit immuable."""

    @abstractmethod
    def append_entry(
        self, action: str, metadata: dict, tenant_id: UUID
    ) -> AuditLedgerEntry:
        """Ajoute une entrée au registre d'audit."""
        raise NotImplementedError