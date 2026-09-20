import uuid

from pydantic import BaseModel

from academy_context.domain.value_objects import AccessStatus, DocumentType


class DocumentUploadDTO(BaseModel):
    title: str
    document_type: DocumentType
    faculty: str
    filiere: str
    academic_level: str
    is_premium: bool = False
    price_fcfa: int = 0


class DocumentResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    document_type: DocumentType
    faculty: str
    filiere: str
    academic_level: str
    is_premium: bool
    price_fcfa: int
    access_status: AccessStatus


class PurchaseRequestDTO(BaseModel):
    document_id: uuid.UUID


class ReaderAccessDTO(BaseModel):
    document_id: uuid.UUID
    access_status: AccessStatus
