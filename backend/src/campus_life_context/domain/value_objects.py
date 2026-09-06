from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ListingCategory(str, Enum):
    """Catégorie d'une annonce sur la marketplace."""
    BOOKS = "BOOKS"
    ELECTRONICS = "ELECTRONICS"
    CLOTHING = "CLOTHING"
    SERVICES = "SERVICES"
    HOUSING = "HOUSING"
    OTHER = "OTHER"


class ListingStatus(str, Enum):
    """État d'une annonce."""
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class RideStatus(str, Enum):
    """État d'un trajet de covoiturage."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MessageType(str, Enum):
    """Type de message dans la messagerie interne."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    LOCATION = "LOCATION"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class RideLocation:
    """
    Localisation d'un point de covoiturage (adresse + coordonnées GPS optionnelles).
    """
    address_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.address_name or not self.address_name.strip():
            raise ValueError("address_name cannot be empty.")
        # Validation simple des coordonnées si fournies
        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            raise ValueError("latitude must be between -90 and 90.")
        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            raise ValueError("longitude must be between -180 and 180.")