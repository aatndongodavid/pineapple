# backend/src/monetization_context/domain/value_objects.py

from enum import Enum


class SponsorshipStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class SubscriptionPlan(str, Enum):
    MONTHLY = "MONTHLY"
    SEMESTRIAL = "SEMESTRIAL"
    ANNUAL = "ANNUAL"


class CampusLicenseTier(str, Enum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    ENTERPRISE = "ENTERPRISE"