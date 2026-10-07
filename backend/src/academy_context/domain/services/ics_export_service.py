# backend/src/academy_context/domain/services/ics_export_service.py

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from academy_context.domain.value_objects import TimetableExceptionType
from academy_context.infrastructure.persistence.models import (
    TimetableRuleModel, TimetableExceptionModel,
    CourseOfferingModel, SubjectModel, AcademicTermModel
)
from identity_context.infrastructure.persistence.models import ClassGroupModel
from community_context.infrastructure.persistence.models import RoomModel
from academy_context.domain.services.recurrence_engine import RecurrenceEngine


class IcsExportService:
    """
    Génère un flux d'agenda iCalendar (.ics) conforme RFC 5545
    avec fuseau horaire Africa/Douala.
    """

    @staticmethod
    async def generate_ics_calendar(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        class_group_id: Optional[uuid.UUID] = None,
        teacher_id: Optional[uuid.UUID] = None,
    ) -> str:
        # 1. Active rules query
        stmt = select(TimetableRuleModel).where(
            TimetableRuleModel.tenant_id == tenant_id,
            TimetableRuleModel.is_active == True
        )

        rules = (await db.execute(stmt)).scalars().all()

        # If class_group_id specified, filter rules by offering class_group_id
        if class_group_id:
            off_stmt = select(CourseOfferingModel.id).where(
                CourseOfferingModel.tenant_id == tenant_id,
                CourseOfferingModel.class_group_id == class_group_id
            )
            offering_ids = set((await db.execute(off_stmt)).scalars().all())
            rules = [r for r in rules if r.course_offering_id in offering_ids]

        # Fetch referenced offerings, subjects, rooms for metadata
        offering_ids = {r.course_offering_id for r in rules}
        room_ids = {r.room_id for r in rules if r.room_id}

        offerings_map = {}
        if offering_ids:
            off_res = await db.execute(select(CourseOfferingModel).where(CourseOfferingModel.id.in_(offering_ids)))
            offerings_map = {o.id: o for o in off_res.scalars().all()}

        # Filter by teacher_id if requested
        if teacher_id:
            rules = [r for r in rules if offerings_map.get(r.course_offering_id) and offerings_map[r.course_offering_id].teacher_id == teacher_id]

        subject_ids = {o.subject_id for o in offerings_map.values() if o.subject_id}
        subjects_map = {}
        if subject_ids:
            sub_res = await db.execute(select(SubjectModel).where(SubjectModel.id.in_(subject_ids)))
            subjects_map = {s.id: s for s in sub_res.scalars().all()}

        rooms_map = {}
        if room_ids:
            room_res = await db.execute(select(RoomModel).where(RoomModel.id.in_(room_ids)))
            rooms_map = {rm.id: rm for rm in room_res.scalars().all()}

        # Fetch exceptions
        ex_stmt = select(TimetableExceptionModel).where(TimetableExceptionModel.tenant_id == tenant_id)
        exceptions = (await db.execute(ex_stmt)).scalars().all()
        cancelled_pairs = {(e.rule_id, e.target_date) for e in exceptions if e.exception_type == TimetableExceptionType.CANCELLED}

        # Build ICS content
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Pineapple OS//Emploi du Temps v1.0//FR",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Emploi du Temps Pineapple",
            "X-WR-TIMEZONE:Africa/Douala",
            "BEGIN:VTIMEZONE",
            "TZID:Africa/Douala",
            "BEGIN:STANDARD",
            "TZOFFSETFROM:+0100",
            "TZOFFSETTO:+0100",
            "TZNAME:WAT",
            "DTSTART:19700101T000000",
            "END:STANDARD",
            "END:VTIMEZONE",
        ]

        now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        # Generate occurrences for each rule over a 12-week horizon
        start_search = date.today() - timedelta(days=14)
        end_search = date.today() + timedelta(days=90)

        for rule in rules:
            offering = offerings_map.get(rule.course_offering_id)
            subject = subjects_map.get(offering.subject_id) if offering else None
            room = rooms_map.get(rule.room_id) if rule.room_id else None

            summary = f"{subject.code if subject else 'COURS'} - {subject.name if subject else 'Matière'}"
            location = room.name if room else "Salle non attribuée"

            cur_date = start_search
            while cur_date <= end_search:
                if (rule.start_date <= cur_date) and (rule.end_date is None or rule.end_date >= cur_date):
                    if RecurrenceEngine.matches_date(rule, cur_date):
                        if (rule.id, cur_date) not in cancelled_pairs:
                            dt_start = datetime.combine(cur_date, rule.start_time)
                            dt_end = datetime.combine(cur_date, rule.end_time)

                            dt_start_fmt = dt_start.strftime("%Y%m%dT%H%M%S")
                            dt_end_fmt = dt_end.strftime("%Y%m%dT%H%M%S")

                            uid = f"timetable-{rule.id}-{cur_date.isoformat()}@pineapple.campus"

                            lines.extend([
                                "BEGIN:VEVENT",
                                f"UID:{uid}",
                                f"DTSTAMP:{now_str}",
                                f"DTSTART;TZID=Africa/Douala:{dt_start_fmt}",
                                f"DTEND;TZID=Africa/Douala:{dt_end_fmt}",
                                f"SUMMARY:{summary}",
                                f"LOCATION:{location}",
                                f"DESCRIPTION:Cours de {summary}",
                                "END:VEVENT"
                            ])
                cur_date += timedelta(days=1)

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)
