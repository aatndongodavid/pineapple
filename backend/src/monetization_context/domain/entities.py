# backend/src/monetization_context/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from monetization_context.domain.value_objects import (
    BillingPeriod,
    CampusLicenseTier,
    ManualProofStatus,
    PaymentChannel,
    PaymentStatus,
    SponsorshipStatus,
    SubscriptionStatus,
)
from shared_kernel.domain.value_objects import Money, DomainValidationError


@dataclass
class Plan:
    """Catalogue de forfaits d'abonnements pour les établissements."""
    id: UUID
    code: str  # ex: STANDARD_2026
    name: str  # ex: Forfait Annuel Établissement Standard
    price: Money
    billing_period: BillingPeriod
    seats_included: int
    extra_seat_price: Money
    trial_days: int = 14
    features_json: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Subscription:
    """Abonnement d'un établissement à Pineapple OS avec machine à états stricte."""
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    seats_limit: int
    current_period_start: datetime
    current_period_end: datetime
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    auto_renew: bool = True
    cancel_at_period_end: bool = False
    billing_contact_email: Optional[str] = None
    grace_days: int = 7
    created_at: datetime = field(default_factory=datetime.utcnow)

    def transition_to(self, new_status: SubscriptionStatus, now: Optional[datetime] = None) -> None:
        """Effectue une transition d'état d'abonnement selon les règles métier."""
        valid_transitions = {
            SubscriptionStatus.TRIAL: {SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED},
            SubscriptionStatus.ACTIVE: {SubscriptionStatus.PAST_DUE, SubscriptionStatus.CANCELLED},
            SubscriptionStatus.PAST_DUE: {SubscriptionStatus.ACTIVE, SubscriptionStatus.GRACE, SubscriptionStatus.CANCELLED},
            SubscriptionStatus.GRACE: {SubscriptionStatus.ACTIVE, SubscriptionStatus.SUSPENDED, SubscriptionStatus.CANCELLED},
            SubscriptionStatus.SUSPENDED: {SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED},
            SubscriptionStatus.EXPIRED: {SubscriptionStatus.ACTIVE},  # Réactivation par paiement
            SubscriptionStatus.CANCELLED: {SubscriptionStatus.ACTIVE},
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise DomainValidationError(
                f"Transition de statut d'abonnement invalide : de {self.status.value} vers {new_status.value}"
            )
        self.status = new_status

    def evaluate_expiry(self, now: datetime) -> SubscriptionStatus:
        """Évalue l'état de l'abonnement à un instant donné (now)."""
        if self.status == SubscriptionStatus.TRIAL and self.trial_ends_at and now > self.trial_ends_at:
            self.transition_to(SubscriptionStatus.EXPIRED, now)
        elif self.status == SubscriptionStatus.ACTIVE and now > self.current_period_end:
            self.transition_to(SubscriptionStatus.PAST_DUE, now)
            if not self.grace_ends_at:
                self.grace_ends_at = now + timedelta(days=self.grace_days)
        elif self.status == SubscriptionStatus.PAST_DUE and self.grace_ends_at and now <= self.grace_ends_at:
            self.transition_to(SubscriptionStatus.GRACE, now)
        elif (self.status in [SubscriptionStatus.PAST_DUE, SubscriptionStatus.GRACE]) and self.grace_ends_at and now > self.grace_ends_at:
            self.transition_to(SubscriptionStatus.SUSPENDED, now)
        return self.status

    def record_successful_payment(self, next_period_end: datetime) -> None:
        """Enregistre un paiement réussi et prolonge l'abonnement."""
        if self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.PAST_DUE, SubscriptionStatus.GRACE, SubscriptionStatus.SUSPENDED, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED]:
            self.transition_to(SubscriptionStatus.ACTIVE)
        self.current_period_start = datetime.now(timezone.utc)
        self.current_period_end = next_period_end
        self.grace_ends_at = None

    @property
    def is_in_read_only_mode(self) -> bool:
        """Détermine si l'abonnement est en mode lecture seule (SUSPENDED / EXPIRED)."""
        return self.status in [SubscriptionStatus.SUSPENDED, SubscriptionStatus.EXPIRED]


@dataclass
class Sponsorship:
    """Contrat de sponsoring d'une organisation vers des audiences ciblées."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    target_tenant_ids: List[UUID]
    budget: Money
    status: SponsorshipStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CampusLicense:
    """Licence souscrite par un établissement pour utiliser Pineapple."""
    id: UUID
    tenant_id: UUID
    tier: CampusLicenseTier
    max_certified_students: int
    is_active: bool
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)