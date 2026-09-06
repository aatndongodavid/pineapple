# backend/src/opportunities_context/domain/value_objects.py

from enum import Enum


class OpportunityType(str, Enum):
    PROJECT = "PROJECT"
    RESEARCH = "RESEARCH"
    CHALLENGE = "CHALLENGE"
    INTERNSHIP = "INTERNSHIP"
    STARTUP = "STARTUP"


class OpportunityStatus(str, Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"