from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from academy_context.domain.value_objects import DocumentType
from shared_kernel.domain.value_objects import Money


@dataclass
class PremiumPurchase:
    """Achat d'un document premium par un utilisateur."""
    id: UUID
    user_id: UUID
    tenant_id: UUID
    document_id: UUID
    price_paid: Money
    purchased_at: datetime
    is_active: bool = True


@dataclass
class Course:
    """Cours dispensé dans le cadre d'une formation."""
    id: UUID
    tenant_id: UUID
    title: str
    description: str
    instructor_id: UUID
    faculty: str
    filiere: str
    academic_level: str


@dataclass
class LibraryDocument:
    """
    Agrégat racine représentant un document de la bibliothèque numérique.
    Peut être gratuit ou premium.
    """
    id: UUID
    tenant_id: UUID
    title: str
    document_type: DocumentType
    s3_key: str
    is_premium: bool
    price: Money
    faculty: str
    filiere: str
    academic_level: str
    downloads_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def can_be_accessed_by(self, user_id: UUID, user_purchases: List[UUID]) -> bool:
        """
        Détermine si un utilisateur donné peut accéder au document.
        - Si le document n'est pas premium : accès libre.
        - Si le document est premium : l'utilisateur doit avoir acheté ce document
          (son identifiant figure dans la liste des documents achetés).
        """
        if not self.is_premium:
            return True
        return self.id in user_purchases