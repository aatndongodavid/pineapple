# tests/unit/test_subscription_domain.py
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from monetization_context.domain.entities import Subscription, Plan
from monetization_context.domain.value_objects import SubscriptionStatus, BillingPeriod
from shared_kernel.domain.value_objects import Money, DomainValidationError


def test_b11_money_prohibits_floats():
    """B11: L'objet valeur Money refuse catégoriquement les montants en float."""
    with pytest.raises(DomainValidationError, match="float"):
        Money(amount_xaf=1500.50)  # type: ignore

    with pytest.raises(DomainValidationError, match="integer"):
        Money(amount_xaf=1000).multiply(1.5)  # type: ignore


def test_money_proration_integer_exactness():
    """B11: Le prorata d'un montant Money s'effectue en entiers stricts XAF FCFA."""
    base = Money(amount_xaf=100_000)
    # Prorata 15 jours sur 30 jours
    prorated = base.prorate(days_used=15, total_days=30)
    assert prorated.amount_xaf == 50_000

    # Prorata 1 jour sur 365 jours
    prorated_1_day = base.prorate(days_used=1, total_days=365)
    assert isinstance(prorated_1_day.amount_xaf, int)
    assert prorated_1_day.amount_xaf > 0


@pytest.mark.parametrize("val1,val2", [
    (0, 0),
    (100, 200),
    (150_000, 500_000),
    (10_000_000, 5_000_000),
])
def test_money_addition_properties(val1, val2):
    """B11: Test de propriétés sur l'addition de montants XAF en entiers stricts."""
    m1 = Money(amount_xaf=val1)
    m2 = Money(amount_xaf=val2)
    result = m1 + m2
    assert result.amount_xaf == val1 + val2
    assert isinstance(result.amount_xaf, int)


def test_b5_subscription_state_machine_transitions():
    """B5: Vérification des transitions d'états de l'abonnement."""
    now = datetime.now(timezone.utc)
    sub = Subscription(
        id=uuid4(),
        tenant_id=uuid4(),
        plan_id=uuid4(),
        status=SubscriptionStatus.TRIAL,
        seats_limit=1000,
        current_period_start=now,
        current_period_end=now + timedelta(days=14),
        trial_ends_at=now + timedelta(days=14),
    )

    # 1. TRIAL -> ACTIVE lors d'un paiement
    sub.record_successful_payment(next_period_end=now + timedelta(days=365))
    assert sub.status == SubscriptionStatus.ACTIVE

    # 2. ACTIVE -> PAST_DUE lorsque la période expire
    past_due_date = now + timedelta(days=366)
    sub.evaluate_expiry(now=past_due_date)
    assert sub.status == SubscriptionStatus.PAST_DUE

    # 3. PAST_DUE -> GRACE
    sub.evaluate_expiry(now=past_due_date + timedelta(days=1))
    assert sub.status == SubscriptionStatus.GRACE

    # 4. GRACE -> SUSPENDED après expiration du délai de grâce
    suspended_date = past_due_date + timedelta(days=10)
    sub.evaluate_expiry(now=suspended_date)
    assert sub.status == SubscriptionStatus.SUSPENDED
    assert sub.is_in_read_only_mode is True
