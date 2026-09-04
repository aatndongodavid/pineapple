from enum import Enum
from dataclasses import dataclass
import re

from shared_kernel.domain.value_objects import DomainValidationError


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CERTIFICATION_REQUIRED = "CERTIFICATION_REQUIRED"


class AcademicStatus(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ALUMNI = "ALUMNI"


class DocumentType(str, Enum):
    CARTE_ETUDIANT = "CARTE_ETUDIANT"
    QUITTANCE = "QUITTANCE"
    DIPLOME = "DIPLOME"
    ACTE_NAISSANCE = "ACTE_NAISSANCE"


class CampusStatusDisplay(str, Enum):
    CERTIFIED_STUDENT = "Étudiant certifié"
    PENDING_CERTIFICATION = "Certification en attente"
    NOT_CERTIFIED = "Non certifié"
    ARCHIVED = "Archivé"
    ALUMNI = "Alumni"
    VERIFIED_TEACHER = "Enseignant vérifié"


@dataclass(frozen=True)
class Matricule:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^[A-Za-z0-9-]+$"
        if not self.value or not re.match(pattern, self.value):
            raise DomainValidationError(
                "Matricule must be non-empty and contain only alphanumeric characters or hyphens (no spaces)."
            )