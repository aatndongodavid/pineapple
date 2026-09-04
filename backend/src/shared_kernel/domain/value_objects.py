import re
import uuid
from dataclasses import dataclass
from decimal import Decimal


class DomainValidationError(Exception):
    """Raised when a domain value object validation fails."""
    pass


@dataclass(frozen=True)
class TenantID:
    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise DomainValidationError("TenantID must be a UUID")


@dataclass(frozen=True)
class UserID:
    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise DomainValidationError("UserID must be a UUID")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "XAF"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise DomainValidationError("Money amount must be a Decimal")
        if self.amount < 0:
            raise DomainValidationError("Money amount cannot be negative")
        if self.currency != "XAF":
            raise DomainValidationError(f"Unsupported currency: {self.currency}. Only XAF is allowed.")

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise DomainValidationError("Can only add Money to Money")
        if self.currency != other.currency:
            raise DomainValidationError("Currency mismatch")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise DomainValidationError("Can only subtract Money from Money")
        if self.currency != other.currency:
            raise DomainValidationError("Currency mismatch")
        new_amount = self.amount - other.amount
        if new_amount < 0:
            raise DomainValidationError("Resulting Money cannot be negative")
        return Money(amount=new_amount, currency=self.currency)


@dataclass(frozen=True)
class AcademicYear:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^\d{4}-\d{4}$"
        if not re.match(pattern, self.value):
            raise DomainValidationError("AcademicYear must be in format YYYY-YYYY (e.g., 2026-2027)")