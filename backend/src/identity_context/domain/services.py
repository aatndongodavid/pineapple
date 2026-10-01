# backend/src/identity_context/domain/services.py

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from identity_context.domain.entities import User
from identity_context.domain.value_objects import AcademicStatus, AccountStatus
from monetization_context.domain.value_objects import CampusLicenseTier


class AlumniRetentionService:
    """
    Service de domaine gérant la rétention des comptes Alumni selon le palier de licence de l'établissement.
    """

    @staticmethod
    def get_retention_window_days(license_tier: CampusLicenseTier) -> Optional[int]:
        """Retourne la durée maximale de rétention en jours pour un palier donné. None = Illimité."""
        if license_tier == CampusLicenseTier.BASIC:
            return 180  # 6 mois
        elif license_tier == CampusLicenseTier.STANDARD:
            return 365  # 12 mois
        elif license_tier == CampusLicenseTier.ENTERPRISE:
            return None  # Illimité
        return 180

    @staticmethod
    def is_alumni_expired(user: User, license_tier: CampusLicenseTier, now: Optional[datetime] = None) -> bool:
        """
        Détermine si un compte Alumni a dépassé sa période de grâce selon la licence tenant.
        Exclut explicitement les tenants au palier ENTERPRISE.
        """
        if user.academic_status != AcademicStatus.ALUMNI:
            return False

        if license_tier == CampusLicenseTier.ENTERPRISE:
            return False  # Jamais archivé pour ce motif

        window_days = AlumniRetentionService.get_retention_window_days(license_tier)
        if window_days is None:
            return False

        current_time = now or datetime.utcnow()
        # On calcule la fin de formation à partir de la date de création ou mise à jour
        expiration_date = user.created_at + timedelta(days=window_days)
        return current_time > expiration_date
