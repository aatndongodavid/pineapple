from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    DocumentType,
    VerificationStatus,
)


class BaseDTO(BaseModel):
    """Classe de base pour tous les DTOs avec configuration ORM."""
    model_config = ConfigDict(from_attributes=True)


class UserRegisterDTO(BaseDTO):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    last_name: str
    matricule: str
    faculty: str
    filiere: str
    academic_year: str


class UserLoginDTO(BaseDTO):
    email: EmailStr
    password: str


class TokenResponseDTO(BaseDTO):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    tenant_id: UUID


class CertificationSubmitDTO(BaseDTO):
    document_type: DocumentType
    file_base64_or_name: str


class CertificationReviewDTO(BaseDTO):
    document_id: UUID
    approved: bool
    rejection_reason: Optional[str] = None


class UserResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    matricule: str
    faculty: str
    filiere: str
    academic_year: str
    account_status: AccountStatus
    verification_status: VerificationStatus
    academic_status: AcademicStatus
    campus_status_display: str