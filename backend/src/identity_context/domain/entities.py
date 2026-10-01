from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    CampusStatusDisplay,
    DocumentType,
    UserRole,
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
class LegalAcceptance:
    """Acceptation d'un document légal par un utilisateur."""
    id: UUID
    user_id: UUID
    document_type: str  # ex: STUDENT_CGU, ENTERPRISE_CGU, PRIVACY_POLICY
    version: str  # ex: 1.0.0
    accepted_at: datetime = datetime.utcnow()


@dataclass
class User:
    """Agrégat racine du contexte Identity."""
    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    matricule: Optional[str] = None
    faculty: Optional[str] = None
    filiere: Optional[str] = None
    academic_year: Optional[str] = None
    phone_number: Optional[str] = None
    sms_consent: bool = False
    account_status: AccountStatus = AccountStatus.ACTIVE
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    academic_status: AcademicStatus = AcademicStatus.STUDENT
    role: UserRole = UserRole.STUDENT
    created_at: datetime = datetime.utcnow()
    password_hash: str = ""

    def __post_init__(self) -> None:
        if self.academic_status != AcademicStatus.ENTERPRISE:
            if not self.matricule or not self.faculty or not self.filiere or not self.academic_year:
                # Si aucun champ académique n'est fourni pour un compte classique, utiliser une valeur par défaut vide
                self.matricule = self.matricule or "N/A"
                self.faculty = self.faculty or "Général"
                self.filiere = self.filiere or "Général"
                self.academic_year = self.academic_year or "2026"

    def resolve_campus_status(self) -> CampusStatusDisplay:
        """Calcule le statut d'affichage public selon la matrice de visibilité."""
        if self.account_status == AccountStatus.ARCHIVED:
            return CampusStatusDisplay.ARCHIVED
        if self.academic_status == AcademicStatus.ENTERPRISE:
            return CampusStatusDisplay.ENTERPRISE
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
