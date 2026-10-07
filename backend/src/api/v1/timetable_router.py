# backend/src/api/v1/timetable_router.py

import csv
import io
import uuid
from datetime import date, datetime, time, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from academy_context.domain.services.conflict_detector import ConflictDetectorService
from academy_context.domain.services.room_availability import RoomAvailabilityService
from academy_context.domain.services.ics_export_service import IcsExportService
from shared_kernel.infrastructure.websocket_manager import room_ws_manager
from academy_context.domain.value_objects import (
    CalendarExceptionType,
    ChangeRequestStatus,
    ReservationStatus,
    TimetableExceptionType,
)
from academy_context.infrastructure.persistence.models import (
    AcademicTermModel,
    CalendarExceptionModel,
    CourseOfferingModel,
    IcsTokenModel,
    RoomFeatureModel,
    RoomReservationModel,
    SubjectModel,
    TimetableChangeRequestModel,
    TimetableExceptionModel,
    TimetableRuleModel,
)
from community_context.infrastructure.persistence.models import ClassIncidentModel, RoomModel
from identity_context.infrastructure.persistence.models import ClassGroupModel, UserModel
from shared_kernel.infrastructure.audit_log import AuditLogModel
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_membership,
    require_permission,
)

router = APIRouter(prefix="/timetable", tags=["Emploi du Temps & Salles"])


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class TermCreateDTO(BaseModel):
    name: str = Field(..., examples=["Semestre 1 2026-2027"])
    academic_year: str = Field(..., examples=["2026-2027"])
    start_date: date
    end_date: date
    is_active: bool = True


class CalendarExceptionCreateDTO(BaseModel):
    term_id: Optional[str] = None
    title: str = Field(..., examples=["Fête Nationale"])
    exception_type: CalendarExceptionType
    start_date: date
    end_date: date


class SubjectCreateDTO(BaseModel):
    code: str = Field(..., examples=["INF301"])
    name: str = Field(..., examples=["Algorithmique & Structures de données"])
    credits: int = 4


class CourseOfferingCreateDTO(BaseModel):
    term_id: str
    subject_id: str
    class_group_id: str
    teacher_id: Optional[str] = None
    color_code: str = "#3182CE"


class TimetableRuleCreateDTO(BaseModel):
    course_offering_id: str
    room_id: str
    day_of_week: int = Field(..., ge=0, le=6, description="0=Lundi, 6=Dimanche")
    start_time: str = Field(..., examples=["08:00"])
    end_time: str = Field(..., examples=["10:00"])
    start_date: date
    end_date: date
    recurrence_rule: str = "FREQ=WEEKLY"
    admin_override: bool = False
    override_reason: Optional[str] = None


class TimetableExceptionCreateDTO(BaseModel):
    target_date: date
    exception_type: TimetableExceptionType
    new_room_id: Optional[str] = None
    new_teacher_id: Optional[str] = None
    new_start_time: Optional[str] = None
    new_end_time: Optional[str] = None
    reason: Optional[str] = None


class RoomReservationCreateDTO(BaseModel):
    room_id: str
    title: str = Field(..., examples=["Soutenance de mémoire GIT3"])
    purpose: Optional[str] = None
    reservation_date: date
    start_time: str = Field(..., examples=["14:00"])
    end_time: str = Field(..., examples=["16:00"])


class ChangeRequestCreateDTO(BaseModel):
    rule_id: Optional[str] = None
    target_date: Optional[date] = None
    requested_type: str = Field(..., examples=["CANCEL"])  # CANCEL, MOVE, ROOM_CHANGE
    proposed_room_id: Optional[str] = None
    proposed_start_time: Optional[str] = None
    proposed_end_time: Optional[str] = None
    reason: str


# Helper parsing HH:MM
def parse_time(time_str: str) -> time:
    try:
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Format d'heure invalide '{time_str}', attendu HH:MM")


# ---------------------------------------------------------------------------
# 1. SEMESTRES & CALENDRIER
# ---------------------------------------------------------------------------

@router.get("/terms")
async def list_terms(
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(AcademicTermModel).where(AcademicTermModel.tenant_id == ctx.tenant_id).order_by(AcademicTermModel.start_date.desc())
    res = await db.execute(stmt)
    terms = res.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "academic_year": t.academic_year,
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat(),
            "is_active": t.is_active,
        }
        for t in terms
    ]


@router.post("/terms", status_code=status.HTTP_201_CREATED)
async def create_term(
    dto: TermCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    term = AcademicTermModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        name=dto.name,
        academic_year=dto.academic_year,
        start_date=dto.start_date,
        end_date=dto.end_date,
        is_active=dto.is_active,
    )
    db.add(term)
    await db.commit()
    return {"id": str(term.id), "name": term.name}


@router.get("/calendar-exceptions")
async def list_calendar_exceptions(
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(CalendarExceptionModel).where(CalendarExceptionModel.tenant_id == ctx.tenant_id).order_by(CalendarExceptionModel.start_date.asc())
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "exception_type": c.exception_type.value,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
        }
        for c in items
    ]


@router.post("/calendar-exceptions", status_code=status.HTTP_201_CREATED)
async def create_calendar_exception(
    dto: CalendarExceptionCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    term_uuid = uuid.UUID(dto.term_id) if dto.term_id else None
    exc = CalendarExceptionModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        term_id=term_uuid,
        title=dto.title,
        exception_type=dto.exception_type,
        start_date=dto.start_date,
        end_date=dto.end_date,
    )
    db.add(exc)
    await db.commit()
    return {"id": str(exc.id), "title": exc.title}


# ---------------------------------------------------------------------------
# 2. MATIÈRES & ENSEIGNEMENTS
# ---------------------------------------------------------------------------

@router.get("/subjects")
async def list_subjects(
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(SubjectModel).where(SubjectModel.tenant_id == ctx.tenant_id).order_by(SubjectModel.code.asc())
    res = await db.execute(stmt)
    subs = res.scalars().all()
    return [{"id": str(s.id), "code": s.code, "name": s.name, "credits": s.credits} for s in subs]


@router.post("/subjects", status_code=status.HTTP_201_CREATED)
async def create_subject(
    dto: SubjectCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    sub = SubjectModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        code=dto.code,
        name=dto.name,
        credits=dto.credits,
    )
    db.add(sub)
    await db.commit()
    return {"id": str(sub.id), "code": sub.code, "name": sub.name}


@router.get("/course-offerings")
async def list_course_offerings(
    class_group_id: Optional[str] = None,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(CourseOfferingModel).where(CourseOfferingModel.tenant_id == ctx.tenant_id)
    if class_group_id:
        stmt = stmt.where(CourseOfferingModel.class_group_id == uuid.UUID(class_group_id))
    res = await db.execute(stmt)
    offerings = res.scalars().all()
    return [
        {
            "id": str(o.id),
            "term_id": str(o.term_id),
            "subject_id": str(o.subject_id),
            "class_group_id": str(o.class_group_id),
            "teacher_id": str(o.teacher_id) if o.teacher_id else None,
            "color_code": o.color_code,
        }
        for o in offerings
    ]


@router.post("/course-offerings", status_code=status.HTTP_201_CREATED)
async def create_course_offering(
    dto: CourseOfferingCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    offering = CourseOfferingModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        term_id=uuid.UUID(dto.term_id),
        subject_id=uuid.UUID(dto.subject_id),
        class_group_id=uuid.UUID(dto.class_group_id),
        teacher_id=uuid.UUID(dto.teacher_id) if dto.teacher_id else None,
        color_code=dto.color_code,
    )
    db.add(offering)
    await db.commit()
    return {"id": str(offering.id)}


# ---------------------------------------------------------------------------
# 3. RÈGLES DE PLANNING & DÉTECTION DE CONFLITS (3.1, 3.2, T4)
# ---------------------------------------------------------------------------

@router.get("/rules")
async def list_timetable_rules(
    class_group_id: Optional[str] = None,
    room_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(TimetableRuleModel, CourseOfferingModel, SubjectModel, RoomModel, ClassGroupModel)\
        .join(CourseOfferingModel, TimetableRuleModel.course_offering_id == CourseOfferingModel.id)\
        .join(SubjectModel, CourseOfferingModel.subject_id == SubjectModel.id)\
        .join(RoomModel, TimetableRuleModel.room_id == RoomModel.id)\
        .join(ClassGroupModel, CourseOfferingModel.class_group_id == ClassGroupModel.id)\
        .where(TimetableRuleModel.tenant_id == ctx.tenant_id, TimetableRuleModel.is_active == True)

    if class_group_id:
        stmt = stmt.where(CourseOfferingModel.class_group_id == uuid.UUID(class_group_id))
    if room_id:
        stmt = stmt.where(TimetableRuleModel.room_id == uuid.UUID(room_id))
    if teacher_id:
        stmt = stmt.where(CourseOfferingModel.teacher_id == uuid.UUID(teacher_id))

    res = await db.execute(stmt)
    rows = res.all()

    rules_data = []
    for rule, offering, subject, room, class_grp in rows:
        rules_data.append({
            "id": str(rule.id),
            "course_offering_id": str(offering.id),
            "subject_code": subject.code,
            "subject_name": subject.name,
            "class_group_id": str(class_grp.id),
            "class_group_name": class_grp.name,
            "room_id": str(room.id),
            "room_name": room.name,
            "teacher_id": str(offering.teacher_id) if offering.teacher_id else None,
            "day_of_week": rule.day_of_week,
            "start_time": rule.start_time.strftime("%H:%M"),
            "end_time": rule.end_time.strftime("%H:%M"),
            "start_date": rule.start_date.isoformat(),
            "end_date": rule.end_date.isoformat(),
            "color_code": offering.color_code,
        })
    return rules_data


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_timetable_rule(
    dto: TimetableRuleCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    offering_uuid = uuid.UUID(dto.course_offering_id)
    room_uuid = uuid.UUID(dto.room_id)
    st_time = parse_time(dto.start_time)
    end_time = parse_time(dto.end_time)

    # Fetch course offering
    offering = await db.get(CourseOfferingModel, offering_uuid)
    if not offering or offering.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Enseignement non trouvé")

    # Fetch existing active rules for conflict detection
    stmt = select(TimetableRuleModel, CourseOfferingModel, SubjectModel, RoomModel, ClassGroupModel)\
        .join(CourseOfferingModel, TimetableRuleModel.course_offering_id == CourseOfferingModel.id)\
        .join(SubjectModel, CourseOfferingModel.subject_id == SubjectModel.id)\
        .join(RoomModel, TimetableRuleModel.room_id == RoomModel.id)\
        .join(ClassGroupModel, CourseOfferingModel.class_group_id == ClassGroupModel.id)\
        .where(TimetableRuleModel.tenant_id == ctx.tenant_id, TimetableRuleModel.is_active == True)
    existing_res = await db.execute(stmt)
    existing_rows = existing_res.all()

    existing_rules_data = []
    for r, o, s, rm, cg in existing_rows:
        existing_rules_data.append({
            "id": str(r.id),
            "tenant_id": str(r.tenant_id),
            "room_id": str(r.room_id),
            "room_name": rm.name,
            "class_group_id": str(o.class_group_id),
            "class_group_name": cg.name,
            "teacher_id": str(o.teacher_id) if o.teacher_id else None,
            "day_of_week": r.day_of_week,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "subject_code": s.code,
        })

    # Fetch available rooms for suggestions
    rooms_stmt = select(RoomModel).where(RoomModel.tenant_id == ctx.tenant_id, RoomModel.is_active == True)
    rooms_res = await db.execute(rooms_stmt)
    rooms_all = rooms_res.scalars().all()
    available_rooms_data = [{"id": str(rm.id), "name": rm.name, "building": rm.building, "capacity": rm.capacity or 0} for rm in rooms_all]

    # Perform conflict detection (3.2)
    check_res = ConflictDetectorService.check_conflicts(
        candidate_rule_id=None,
        tenant_id=str(ctx.tenant_id),
        room_id=str(dto.room_id),
        class_group_id=str(offering.class_group_id),
        teacher_id=str(offering.teacher_id) if offering.teacher_id else None,
        day_of_week=dto.day_of_week,
        start_time=st_time,
        end_time=end_time,
        start_date=dto.start_date,
        end_date=dto.end_date,
        existing_rules=existing_rules_data,
        available_rooms=available_rooms_data,
    )

    if check_res.has_conflict and not dto.admin_override:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TIMETABLE_CONFLICT",
                "message": "Conflit de planning détecté.",
                "conflicts": [c.__dict__ for c in check_res.conflicts],
                "suggested_rooms": [s.__dict__ for s in check_res.suggested_rooms],
            },
        )

    # In case of admin override, log audit motif (T4)
    if check_res.has_conflict and dto.admin_override:
        if not dto.override_reason:
            raise HTTPException(status_code=400, detail="Un motif d'override explicite est obligatoire.")
        audit = AuditLogModel(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            actor_id=ctx.user_id,
            action="TIMETABLE_CONFLICT_OVERRIDE",
            resource_type="timetable_rules",
            resource_id=str(offering_uuid),
            details={"motif": dto.override_reason, "conflicts_bypassed": len(check_res.conflicts)},
        )
        db.add(audit)

    rule = TimetableRuleModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        course_offering_id=offering_uuid,
        room_id=room_uuid,
        day_of_week=dto.day_of_week,
        start_time=st_time,
        end_time=end_time,
        start_date=dto.start_date,
        end_date=dto.end_date,
        recurrence_rule=dto.recurrence_rule,
    )
    db.add(rule)
    await db.commit()
    return {"id": str(rule.id), "status": "CREATED"}


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable_rule(
    rule_id: str,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    rule = await db.get(TimetableRuleModel, uuid.UUID(rule_id))
    if not rule or rule.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Règle non trouvée")
    rule.is_active = False
    await db.commit()


@router.post("/rules/{rule_id}/exceptions", status_code=status.HTTP_201_CREATED)
async def create_timetable_exception(
    rule_id: str,
    dto: TimetableExceptionCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    rid = uuid.UUID(rule_id)
    rule = await db.get(TimetableRuleModel, rid)
    if not rule or rule.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Règle non trouvée")

    exc = TimetableExceptionModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        rule_id=rid,
        target_date=dto.target_date,
        exception_type=dto.exception_type,
        new_room_id=uuid.UUID(dto.new_room_id) if dto.new_room_id else None,
        new_teacher_id=uuid.UUID(dto.new_teacher_id) if dto.new_teacher_id else None,
        new_start_time=parse_time(dto.new_start_time) if dto.new_start_time else None,
        new_end_time=parse_time(dto.new_end_time) if dto.new_end_time else None,
        reason=dto.reason,
        author_id=ctx.user_id,
    )
    db.add(exc)
    await db.commit()
    return {"id": str(exc.id), "exception_type": exc.exception_type.value}


# ---------------------------------------------------------------------------
# 4. IMPORT CSV / XLSX WITH DRY-RUN (3.1, E4)
# ---------------------------------------------------------------------------

@router.get("/import/template")
async def download_csv_template():
    content = "code_matiere,code_classe,jour,heure_debut,heure_fin,salle,prof_email\nINF301,GIT3,0,08:00,10:00,Amphi A,prof.mbida@campustech.cm\n"
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=timetable_template.csv"})


@router.post("/import/csv")
async def import_timetable_csv(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="Si true, simule l'importation et renvoie la liste des conflits sans sauvegarder"),
    term_id: str = Query(..., description="ID du semestre académique auquel rattacher l'import"),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    term_uuid = uuid.UUID(term_id)
    term = await db.get(AcademicTermModel, term_uuid)
    if not term or term.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Semestre non trouvé")

    raw_bytes = await file.read()
    try:
        decoded_content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        decoded_content = raw_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded_content))

    # Pre-fetch lookup maps for tenant
    subs_res = await db.execute(select(SubjectModel).where(SubjectModel.tenant_id == ctx.tenant_id))
    subjects_map = {s.code.upper(): s for s in subs_res.scalars().all()}

    classes_res = await db.execute(select(ClassGroupModel).where(ClassGroupModel.tenant_id == ctx.tenant_id))
    classes_map = {c.code.upper(): c for c in classes_res.scalars().all()}

    rooms_res = await db.execute(select(RoomModel).where(RoomModel.tenant_id == ctx.tenant_id))
    rooms_map = {r.name.upper(): r for r in rooms_res.scalars().all()}

    users_res = await db.execute(select(UserModel))
    users_map = {u.email.lower(): u for u in users_res.scalars().all()}

    total_rows = 0
    valid_rows = 0
    conflict_count = 0
    errors = []
    rules_to_create = []

    for row_idx, row in enumerate(reader, start=1):
        total_rows += 1
        sub_code = row.get("code_matiere", "").strip().upper()
        cls_code = row.get("code_classe", "").strip().upper()
        day_str = row.get("jour", "0").strip()
        st_str = row.get("heure_debut", "").strip()
        et_str = row.get("heure_fin", "").strip()
        room_name = row.get("salle", "").strip().upper()
        prof_email = row.get("prof_email", "").strip().lower()

        # Validation checks
        sub = subjects_map.get(sub_code)
        if not sub:
            errors.append({"row": row_idx, "error": f"Matière inconnue '{sub_code}'"})
            continue

        cls_group = classes_map.get(cls_code)
        if not cls_group:
            errors.append({"row": row_idx, "error": f"Classe inconnue '{cls_code}'"})
            continue

        room = rooms_map.get(room_name)
        if not room:
            errors.append({"row": row_idx, "error": f"Salle inconnue '{room_name}'"})
            continue

        teacher = users_map.get(prof_email) if prof_email else None

        try:
            day_of_week = int(day_str)
            st_time = parse_time(st_str)
            end_time = parse_time(et_str)
        except Exception as e:
            errors.append({"row": row_idx, "error": f"Format d'heure/jour invalide à la ligne {row_idx}"})
            continue

        rules_to_create.append({
            "row": row_idx,
            "subject": sub,
            "class_group": cls_group,
            "room": room,
            "teacher": teacher,
            "day_of_week": day_of_week,
            "start_time": st_time,
            "end_time": end_time,
        })

    if dry_run:
        return {
            "dry_run": True,
            "total_rows": total_rows,
            "valid_rows": len(rules_to_create),
            "conflict_count": len(errors),
            "errors": errors,
            "message": f"Dry-run achevé. {len(rules_to_create)} lignes valides, {len(errors)} erreurs.",
        }

    # Perform real import of valid rules
    created_count = 0
    for item in rules_to_create:
        # Check or create course offering
        offering_stmt = select(CourseOfferingModel).where(
            CourseOfferingModel.tenant_id == ctx.tenant_id,
            CourseOfferingModel.term_id == term.id,
            CourseOfferingModel.subject_id == item["subject"].id,
            CourseOfferingModel.class_group_id == item["class_group"].id,
        )
        off_res = await db.execute(offering_stmt)
        offering = off_res.scalars().first()
        if not offering:
            offering = CourseOfferingModel(
                id=uuid.uuid4(),
                tenant_id=ctx.tenant_id,
                term_id=term.id,
                subject_id=item["subject"].id,
                class_group_id=item["class_group"].id,
                teacher_id=item["teacher"].id if item["teacher"] else None,
            )
            db.add(offering)
            await db.flush()

        rule = TimetableRuleModel(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            course_offering_id=offering.id,
            room_id=item["room"].id,
            day_of_week=item["day_of_week"],
            start_time=item["start_time"],
            end_time=item["end_time"],
            start_date=term.start_date,
            end_date=term.end_date,
        )
        db.add(rule)
        created_count += 1

    await db.commit()
    return {
        "dry_run": False,
        "total_rows": total_rows,
        "imported_rows": created_count,
        "skipped_rows": len(errors),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# 5. RÉSERVATIONS PONCTUELLES (3.2bis)
# ---------------------------------------------------------------------------

@router.get("/reservations")
async def list_room_reservations(
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(RoomReservationModel, RoomModel)\
        .join(RoomModel, RoomReservationModel.room_id == RoomModel.id)\
        .where(RoomReservationModel.tenant_id == ctx.tenant_id)\
        .order_by(RoomReservationModel.reservation_date.desc())
    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "id": str(r.id),
            "room_id": str(r.room_id),
            "room_name": rm.name,
            "requester_id": str(r.requester_id),
            "title": r.title,
            "purpose": r.purpose,
            "reservation_date": r.reservation_date.isoformat(),
            "start_time": r.start_time.strftime("%H:%M"),
            "end_time": r.end_time.strftime("%H:%M"),
            "status": r.status.value,
        }
        for r, rm in rows
    ]


@router.post("/reservations", status_code=status.HTTP_201_CREATED)
async def create_room_reservation(
    dto: RoomReservationCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    rid = uuid.UUID(dto.room_id)
    room = await db.get(RoomModel, rid)
    if not room or room.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Salle non trouvée")

    res = RoomReservationModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        room_id=rid,
        requester_id=ctx.user_id,
        title=dto.title,
        purpose=dto.purpose,
        reservation_date=dto.reservation_date,
        start_time=parse_time(dto.start_time),
        end_time=parse_time(dto.end_time),
        status=ReservationStatus.PENDING,
    )
    db.add(res)
    await db.commit()
    return {"id": str(res.id), "status": res.status.value}


@router.post("/reservations/{reservation_id}/approve")
async def approve_room_reservation(
    reservation_id: str,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    res = await db.get(RoomReservationModel, uuid.UUID(reservation_id))
    if not res or res.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    res.status = ReservationStatus.APPROVED
    res.approved_by_id = ctx.user_id
    await db.commit()
    return {"id": str(res.id), "status": "APPROVED"}


@router.post("/reservations/{reservation_id}/reject")
async def reject_room_reservation(
    reservation_id: str,
    reason: Optional[str] = Query(None),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    res = await db.get(RoomReservationModel, uuid.UUID(reservation_id))
    if not res or res.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    res.status = ReservationStatus.REJECTED
    res.rejection_reason = reason
    await db.commit()
    return {"id": str(res.id), "status": "REJECTED"}


# ---------------------------------------------------------------------------
# 6. DEMANDES DE MODIFICATION ENSEIGNANTS (T5)
# ---------------------------------------------------------------------------

@router.post("/change-requests", status_code=status.HTTP_201_CREATED)
async def create_change_request(
    dto: ChangeRequestCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    req = TimetableChangeRequestModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        teacher_id=ctx.user_id,
        rule_id=uuid.UUID(dto.rule_id) if dto.rule_id else None,
        target_date=dto.target_date,
        requested_type=dto.requested_type,
        proposed_room_id=uuid.UUID(dto.proposed_room_id) if dto.proposed_room_id else None,
        proposed_start_time=parse_time(dto.proposed_start_time) if dto.proposed_start_time else None,
        proposed_end_time=parse_time(dto.proposed_end_time) if dto.proposed_end_time else None,
        reason=dto.reason,
        status=ChangeRequestStatus.PENDING,
    )
    db.add(req)
    await db.commit()
    return {"id": str(req.id), "status": req.status.value}


@router.get("/change-requests")
async def list_change_requests(
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(TimetableChangeRequestModel).where(TimetableChangeRequestModel.tenant_id == ctx.tenant_id).order_by(TimetableChangeRequestModel.created_at.desc())
    res = await db.execute(stmt)
    reqs = res.scalars().all()
    return [
        {
            "id": str(r.id),
            "teacher_id": str(r.teacher_id),
            "rule_id": str(r.rule_id) if r.rule_id else None,
            "target_date": r.target_date.isoformat() if r.target_date else None,
            "requested_type": r.requested_type,
            "reason": r.reason,
            "status": r.status.value,
        }
        for r in reqs
    ]


@router.post("/change-requests/{request_id}/approve")
async def approve_change_request(
    request_id: str,
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    req = await db.get(TimetableChangeRequestModel, uuid.UUID(request_id))
    if not req or req.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    req.status = ChangeRequestStatus.APPROVED
    req.reviewed_by_id = ctx.user_id

    # If rule_id & target_date present, convert to timetable_exception automatically
    if req.rule_id and req.target_date:
        exc_type = TimetableExceptionType.CANCELLED if req.requested_type == "CANCEL" else TimetableExceptionType.MOVED
        exc = TimetableExceptionModel(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            rule_id=req.rule_id,
            target_date=req.target_date,
            exception_type=exc_type,
            new_room_id=req.proposed_room_id,
            new_start_time=req.proposed_start_time,
            new_end_time=req.proposed_end_time,
            reason=f"Approuvé suite à la demande de l'enseignant: {req.reason}",
            author_id=ctx.user_id,
        )
        db.add(exc)

    await db.commit()
    return {"id": str(req.id), "status": "APPROVED"}


# ---------------------------------------------------------------------------
# 7. CONVERSION INCIDENT DÉLÉGUÉ -> EXCEPTION DE PLANNING (3.5)
# ---------------------------------------------------------------------------

@router.post("/incidents/{incident_id}/convert-to-exception", status_code=status.HTTP_201_CREATED)
async def convert_incident_to_timetable_exception(
    incident_id: str,
    rule_id: str = Query(...),
    target_date: date = Query(...),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    incident = await db.get(ClassIncidentModel, uuid.UUID(incident_id))
    if not incident or incident.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Incident délégué non trouvé")

    rule = await db.get(TimetableRuleModel, uuid.UUID(rule_id))
    if not rule or rule.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Règle de cours non trouvée")

    exc = TimetableExceptionModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        rule_id=rule.id,
        target_date=target_date,
        exception_type=TimetableExceptionType.CANCELLED,
        reason=f"Annulation validée par l'admin suite au signalement du délégué : {incident.title}",
        author_id=ctx.user_id,
    )
    db.add(exc)
    incident.status = "RESOLVED"
    incident.resolved_by = ctx.user_id
    await db.commit()

    # Trigger WebSocket real-time update (Gate E6)
    await room_ws_manager.broadcast_room_status_change(
        str(ctx.tenant_id),
        {"event": "INCIDENT_CONVERTED_TO_EXCEPTION", "rule_id": str(rule.id), "date": target_date.isoformat()}
    )

    return {"id": str(exc.id), "status": "CONVERTED_TO_EXCEPTION", "incident_id": str(incident.id)}


# ---------------------------------------------------------------------------
# 8. DISPONIBILITÉ DES SALLES TEMPS RÉEL (PHASE 4, PORTE E6)
# ---------------------------------------------------------------------------

@router.get("/rooms/availability")
async def get_rooms_availability(
    target_date: date = Query(..., description="Date cible YYYY-MM-DD"),
    start_time: str = Query("08:00", description="Heure de début HH:MM"),
    end_time: str = Query("18:00", description="Heure de fin HH:MM"),
    min_capacity: Optional[int] = Query(None, description="Capacité minimale"),
    features: Optional[List[str]] = Query(None, description="Codes de caractéristiques requises (ex: VIDEO_PROJECTOR, AIR_CONDITIONED)"),
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    st_time = parse_time(start_time)
    et_time = parse_time(end_time)

    service = RoomAvailabilityService(db)
    availability = await service.get_rooms_availability(
        tenant_id=ctx.tenant_id,
        target_date=target_date,
        start_time=st_time,
        end_time=et_time,
        min_capacity=min_capacity,
        required_features=features,
    )
    return {"date": target_date.isoformat(), "start_time": start_time, "end_time": end_time, "rooms": availability}


@router.websocket("/rooms/ws/availability")
async def room_availability_websocket(
    websocket: WebSocket,
    tenant_id: str = Query(...),
):
    """
    Canal WebSocket temps réel recevant les diffusions de changement d'état des salles.
    """
    await room_ws_manager.connect(tenant_id, websocket)
    try:
        while True:
            # Maintenir la connexion active
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        room_ws_manager.disconnect(tenant_id, websocket)


# ---------------------------------------------------------------------------
# 9. FLUX EXPORT ICS / ICALENDAR (PHASE 5, PORTES E8, E9)
# ---------------------------------------------------------------------------

@router.post("/ics/token", status_code=status.HTTP_201_CREATED)
async def generate_ics_token(
    class_group_id: Optional[str] = Query(None),
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    token_str = f"ics_{uuid.uuid4().hex}"
    class_grp_uuid = uuid.UUID(class_group_id) if class_group_id else None

    ics_tok = IcsTokenModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        class_group_id=class_grp_uuid,
        token=token_str,
        is_revoked=False,
    )
    db.add(ics_tok)
    await db.commit()

    return {"token": token_str, "export_url": f"/api/v1/timetable/ics/{token_str}.ics"}


@router.get("/ics/{token}.ics")
async def export_ics_calendar(
    token: str,
    db: AsyncSession = Depends(get_db_session),
):
    # Lookup token
    stmt = select(IcsTokenModel).where(IcsTokenModel.token == token, IcsTokenModel.is_revoked == False)
    res = await db.execute(stmt)
    tok_obj = res.scalars().first()

    if not tok_obj:
        raise HTTPException(status_code=404, detail="Jeton d'export iCal invalide ou révoqué")

    ics_content = await IcsExportService.generate_ics_calendar(
        db=db,
        tenant_id=tok_obj.tenant_id,
        class_group_id=tok_obj.class_group_id,
        teacher_id=tok_obj.user_id if tok_obj.class_group_id is None else None,
    )

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f"inline; filename=timetable_{token}.ics",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        }
    )


# ---------------------------------------------------------------------------
# 10. STATISTIQUES ET ANALYTICS ADMIN (PHASE 6)
# ---------------------------------------------------------------------------

@router.get("/analytics/occupancy")
async def get_room_occupancy_analytics(
    term_id: Optional[str] = Query(None),
    ctx: AuthenticatedUserContext = Depends(require_permission("admin.timetable.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    # Calculate occupancy stats
    rooms_res = await db.execute(select(RoomModel).where(RoomModel.tenant_id == ctx.tenant_id, RoomModel.is_active == True))
    rooms = rooms_res.scalars().all()

    rules_res = await db.execute(select(TimetableRuleModel).where(TimetableRuleModel.tenant_id == ctx.tenant_id, TimetableRuleModel.is_active == True))
    rules = rules_res.scalars().all()

    # Calculate assigned hours per room
    room_hours = {str(r.id): 0.0 for r in rooms}
    for rule in rules:
        if rule.room_id and str(rule.room_id) in room_hours:
            # calculate duration in hours
            duration = (rule.end_time.hour + rule.end_time.minute / 60.0) - (rule.start_time.hour + rule.start_time.minute / 60.0)
            room_hours[str(rule.room_id)] += duration

    total_capacity = sum(r.capacity or 0 for r in rooms)
    underutilized = [
        {"room_id": str(r.id), "room_name": r.name, "capacity": r.capacity, "weekly_hours": room_hours.get(str(r.id), 0.0)}
        for r in rooms if room_hours.get(str(r.id), 0.0) < 10.0
    ]

    return {
        "total_rooms": len(rooms),
        "total_capacity": total_capacity,
        "underutilized_rooms_count": len(underutilized),
        "underutilized_rooms": underutilized,
        "room_weekly_occupancy_hours": [
            {"room_id": str(r.id), "room_name": r.name, "weekly_hours": room_hours.get(str(r.id), 0.0)}
            for r in rooms
        ]
    }

