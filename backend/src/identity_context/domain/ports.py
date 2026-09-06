from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from identity_context.domain.entities import CertificationDocument, User


class UserRepositoryPort(ABC):
    """Port de persistance pour l'agrégat User."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Sauvegarde l'utilisateur et retourne l'entité mise à jour."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: UUID, tenant_id: UUID) -> Optional[User]:
        """Récupère un utilisateur par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son adresse email (unique globalement)."""
        raise NotImplementedError

    @abstractmethod
    def get_by_matricule(self, matricule: str, tenant_id: UUID) -> Optional[User]:
        """Récupère un utilisateur par son matricule dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def list_expired_certifications(self, tenant_id: UUID) -> List[User]:
        """Liste les utilisateurs dont la certification est à renouveler."""
        raise NotImplementedError


class CertificationRepositoryPort(ABC):
    """Port de persistance pour les documents de certification."""

    @abstractmethod
    def save_document(self, doc: CertificationDocument) -> CertificationDocument:
        """Sauvegarde un document de certification."""
        raise NotImplementedError

    @abstractmethod
    def get_pending_documents(self, tenant_id: UUID) -> List[CertificationDocument]:
        """Récupère les documents en attente de validation pour un tenant."""
        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[CertificationDocument]:
        """Récupère tous les documents d'un utilisateur."""
        raise NotImplementedError


class FileStoragePort(ABC):
    """Port de stockage de fichiers (S3, etc.)."""

    @abstractmethod
    def upload_file(self, file_bytes: bytes, filename: str, mime_type: str) -> str:
        """Téléverse un fichier et retourne sa clé de stockage."""
        raise NotImplementedError

    @abstractmethod
    def generate_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Génère une URL présignée pour accéder temporairement au fichier."""
        raise NotImplementedError