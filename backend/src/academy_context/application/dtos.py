from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from academy_context.domain.value_objects import AccessStatus, DocumentType


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DocumentUploadDTO(BaseDTO):
    title: str
    document_type: DocumentType
    faculty: str
    filiere: str
    academic_level: str
    is_premium: bool = False
    price_fcfa: int = 0


class DocumentResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    title: str
    document_type: DocumentType
    faculty: str
    filiere: str
    academic_level: str
    is_premium: bool
    price_fcfa: int
    access_status: AccessStatus


class PurchaseRequestDTO(BaseDTO):
    document_id: UUID
    payment_method: str


class ReaderAccessDTO(BaseDTO):
    document_id: UUID
    stream_url: str
    watermark_notice: str