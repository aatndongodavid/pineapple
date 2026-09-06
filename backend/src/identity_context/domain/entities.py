from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    CampusStatusDisplay,
    DocumentType,
    VerificationStatus,
)


@dataclass
class CertificationDocument:
    """Document justificatif soumis pour certification."""
    id: UUID
    user_id: UUID
    document_type: DocumentType
    file_key: str
    status: VerificationStatus
    rejection_reason: Optional[str] = None
    submitted_at: datetime = datetime.utcnow()


@dataclass
class User:
    """Agrégat racine du contexte Identity."""
    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    matricule: str
    faculty: str
    filiere: str
    academic_year: str
    account_status: AccountStatus
    verification_status: VerificationStatus
    academic_status: AcademicStatus
    created_at: datetime = datetime.utcnow()

    def resolve_campus_status(self) -> CampusStatusDisplay:
        """Calcule le statut d'affichage public selon la matrice de visibilité."""
        if self.account_status == AccountStatus.ARCHIVED:
            return CampusStatusDisplay.ARCHIVED
        if self.academic_status == AcademicStatus.TEACHER and self.verification_status == VerificationStatus.VERIFIED:
            return CampusStatusDisplay.VERIFIED_TEACHER
        if self.academic_status == AcademicStatus.ALUMNI:
            return CampusStatusDisplay.ALUMNI
        if self.verification_status == VerificationStatus.VERIFIED:
            return CampusStatusDisplay.CERTIFIED_STUDENT
        if self.verification_status in (
            VerificationStatus.PENDING,
            VerificationStatus.CERTIFICATION_REQUIRED,
        ):
            return CampusStatusDisplay.PENDING_CERTIFICATION
        return CampusStatusDisplay.NOT_CERTIFIED

    def expire_certification(self) -> None:
        """Passe le statut de vérification en CERTIFICATION_REQUIRED (renouvellement annuel)."""
        self.verification_status = VerificationStatus.CERTIFICATION_REQUIRED