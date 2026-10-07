# backend/src/monetization_context/domain/value_objects.py

from enum import Enum


class BillingPeriod(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"


SubscriptionPlan = BillingPeriod



class SubscriptionStatus(str, Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    GRACE = "GRACE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    VOID = "VOID"
    OVERDUE = "OVERDUE"


class PaymentChannel(str, Enum):
    MOBILE_MONEY = "MOBILE_MONEY"
    MANUAL_PROOF = "MANUAL_PROOF"
    CREDIT_NOTE = "CREDIT_NOTE"
    SUPER_ADMIN = "SUPER_ADMIN"


class PaymentProviderName(str, Enum):
    CAMPAY = "CAMPAY"
    NOTCHPAY = "NOTCHPAY"
    CINETPAY = "CINETPAY"
    FLUTTERWAVE = "FLUTTERWAVE"
    MANUAL = "MANUAL"
    FAKE = "FAKE"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class ManualProofStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DunningEventType(str, Enum):
    NOTICE_J30 = "NOTICE_J30"
    NOTICE_J7 = "NOTICE_J7"
    NOTICE_J1 = "NOTICE_J1"
    DUE_J0 = "DUE_J0"
    PAST_DUE_J3 = "PAST_DUE_J3"
    GRACE_J7 = "GRACE_J7"
    SUSPENDED = "SUSPENDED"


class SponsorshipStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class CampusLicenseTier(str, Enum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    ENTERPRISE = "ENTERPRISE"