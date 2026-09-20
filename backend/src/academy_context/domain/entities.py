import uuid
from dataclasses import dataclass
from datetime import datetime

from academy_context.domain.value_objects import DocumentType
from shared_kernel.domain.value_objects import Money


@dataclass
class LibraryDocument:
    id: uuid.UUID
    tenant_id: uuid.UUID
    uploader_id: uuid.UUID
    title: str
    document_type: DocumentType
    faculty: str
    filiere: str
    academic_level: str
    file_key: str
    is_premium: bool
    price: Money
    created_at: datetime


@dataclass
class PremiumPurchase:
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    amount: Money
    purchased_at: datetime
