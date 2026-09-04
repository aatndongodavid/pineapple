from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.value_objects import DocumentType, WatermarkMetadata


class LibraryRepositoryPort(ABC):
    """Port de persistance pour la bibliothèque académique."""

    @abstractmethod
    def save_document(self, doc: LibraryDocument) -> LibraryDocument:
        """Sauvegarde un document de bibliothèque."""
        raise NotImplementedError

    @abstractmethod
    def get_document_by_id(self, doc_id: UUID, tenant_id: UUID) -> Optional[LibraryDocument]:
        """Récupère un document par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def list_documents(
        self,
        tenant_id: UUID,
        faculty: Optional[str],
        level: Optional[str],
        doc_type: Optional[DocumentType],
    ) -> List[LibraryDocument]:
        """Liste les documents filtrés par faculté, niveau et type."""
        raise NotImplementedError


class PurchaseRepositoryPort(ABC):
    """Port de persistance pour les achats premium."""

    @abstractmethod
    def save_purchase(self, purchase: PremiumPurchase) -> PremiumPurchase:
        """Sauvegarde un achat."""
        raise NotImplementedError

    @abstractmethod
    def get_user_purchases(self, user_id: UUID) -> List[PremiumPurchase]:
        """Récupère tous les achats d'un utilisateur."""
        raise NotImplementedError

    @abstractmethod
    def has_purchased(self, user_id: UUID, document_id: UUID) -> bool:
        """Vérifie si un utilisateur a acheté un document donné."""
        raise NotImplementedError


class WatermarkEnginePort(ABC):
    """Port pour l'application de filigranes dynamiques."""

    @abstractmethod
    def apply_dynamic_watermark(self, pdf_bytes: bytes, metadata: WatermarkMetadata) -> bytes:
        """Applique un filigrane personnalisé sur les bytes d'un PDF et retourne le nouveau PDF."""
        raise NotImplementedError