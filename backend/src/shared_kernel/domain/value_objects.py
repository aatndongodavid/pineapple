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
    amount_xaf: int
    currency: str = "XAF"

    def __post_init__(self) -> None:
        if isinstance(self.amount_xaf, float):
            raise DomainValidationError("Money amount_xaf MUST be an integer, never a float.")
        if not isinstance(self.amount_xaf, int):
            try:
                object.__setattr__(self, 'amount_xaf', int(self.amount_xaf))
            except Exception:
                raise DomainValidationError("Money amount_xaf must be an integer XAF amount.")
        if self.amount_xaf < 0:
            raise DomainValidationError("Money amount_xaf cannot be negative")
        if self.currency != "XAF":
            raise DomainValidationError(f"Unsupported currency: {self.currency}. Only XAF is allowed.")

    @property
    def amount(self) -> int:
        return self.amount_xaf

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise DomainValidationError("Can only add Money to Money")
        return Money(amount_xaf=self.amount_xaf + other.amount_xaf, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise DomainValidationError("Can only subtract Money from Money")
        res = self.amount_xaf - other.amount_xaf
        if res < 0:
            raise DomainValidationError("Resulting Money cannot be negative")
        return Money(amount_xaf=res, currency=self.currency)

    def add(self, other: "Money") -> "Money":
        return self.__add__(other)

    def subtract(self, other: "Money") -> "Money":
        return self.__sub__(other)

    def multiply(self, factor: int) -> "Money":
        if isinstance(factor, float):
            raise DomainValidationError("Multiplication factor must be an integer.")
        return Money(amount_xaf=self.amount_xaf * int(factor), currency=self.currency)

    def prorate(self, days_used: int, total_days: int) -> "Money":
        """Calcul du prorata exact en entiers XAF FCFA (arrondi supérieur en entiers)."""
        if total_days <= 0 or days_used <= 0:
            return Money(amount_xaf=0, currency=self.currency)
        if days_used >= total_days:
            return self
        prorated_amount = (self.amount_xaf * days_used + (total_days - 1)) // total_days
        return Money(amount_xaf=prorated_amount, currency=self.currency)

    def format_xaf(self) -> str:
        """Formatage de présentation en FCFA (ex: '150 000 FCFA')."""
        formatted = f"{self.amount_xaf:,}".replace(",", " ")
        return f"{formatted} FCFA"



@dataclass(frozen=True)
class AcademicYear:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^\d{4}-\d{4}$"
        if not re.match(pattern, self.value):
            raise DomainValidationError("AcademicYear must be in format YYYY-YYYY (e.g., 2026-2027)")