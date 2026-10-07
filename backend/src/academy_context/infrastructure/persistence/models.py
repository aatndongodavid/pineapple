import uuid
from datetime import datetime, date, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from academy_context.domain.value_objects import (
    AccessStatus,
    CalendarExceptionType,
    ChangeRequestStatus,
    DocumentType,
    ReservationStatus,
    TimetableExceptionType,
)
from shared_kernel.infrastructure.database import Base


class LibraryDocumentModel(Base):
    __tablename__ = "library_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="academy_document_type_enum"), nullable=False
    )
    faculty: Mapped[str] = mapped_column(String(150), nullable=False)
    filiere: Mapped[str] = mapped_column(String(150), nullable=False)
    academic_level: Mapped[str] = mapped_column(String(50), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price_fcfa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PremiumPurchaseModel(Base):
    __tablename__ = "premium_purchases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("library_documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount_fcfa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Timetable & Room Management Models
# ---------------------------------------------------------------------------

class AcademicTermModel(Base):
    """Semestres académiques par tenant."""
    __tablename__ = "academic_terms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: "Semestre 1 2026-2027"
    academic_year: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "2026-2027"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CalendarExceptionModel(Base):
    """Exceptions académiques globalement applicables (fériés, vacances, périodes d'examens)."""
    __tablename__ = "calendar_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    term_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    exception_type: Mapped[CalendarExceptionType] = mapped_column(
        Enum(CalendarExceptionType, name="calendar_exception_type_enum"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SubjectModel(Base):
    """Catalogue des matières par tenant."""
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "INF301"
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # ex: "Algorithmique"
    credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CourseOfferingModel(Base):
    """Enseignement (Matière x Classe x Enseignant x Semestre)."""
    __tablename__ = "course_offerings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id", ondelete="CASCADE"), index=True, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    color_code: Mapped[str] = mapped_column(String(20), default="#3182CE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TimetableRuleModel(Base):
    """Règle de récurrence hebdomadaire pour un cours."""
    __tablename__ = "timetable_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "room_id", "day_of_week", "start_time", name="uq_timetable_room_slot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    course_offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_offerings.id", ondelete="CASCADE"), index=True, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Lundi..6=Dimanche
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    recurrence_rule: Mapped[str] = mapped_column(String(200), default="FREQ=WEEKLY", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TimetableExceptionModel(Base):
    """Exception ponctuelle sur une occurrence de cours (annulation, déplacement, changement salle/enseignant)."""
    __tablename__ = "timetable_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("timetable_rules.id", ondelete="CASCADE"), index=True, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    exception_type: Mapped[TimetableExceptionType] = mapped_column(
        Enum(TimetableExceptionType, name="timetable_exception_type_enum"), nullable=False
    )
    new_room_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    new_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    new_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    new_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoomFeatureModel(Base):
    """Équipements et caractéristiques d'une salle."""
    __tablename__ = "room_features"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: PROJECTOR, AC, POWER_OUTLETS, COMPUTERS
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoomReservationModel(Base):
    """Réservation ponctuelle de salle (demandée par enseignant ou club étudiant)."""
    __tablename__ = "room_reservations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reservation_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="room_reservation_status_enum"), default=ReservationStatus.PENDING, nullable=False
    )
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TimetableChangeRequestModel(Base):
    """Demandes de modification formulées par un enseignant."""
    __tablename__ = "timetable_change_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("timetable_rules.id", ondelete="SET NULL"), nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    requested_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CANCEL, MOVE, ROOM_CHANGE
    proposed_room_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    proposed_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    proposed_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ChangeRequestStatus] = mapped_column(
        Enum(ChangeRequestStatus, name="change_request_status_enum"), default=ChangeRequestStatus.PENDING, nullable=False
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class IcsTokenModel(Base):
    """Jetons d'abonnement iCal (ICS) révocables."""
    __tablename__ = "ics_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=True)
    token: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

