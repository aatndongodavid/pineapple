# backend/src/academy_context/domain/services/recurrence_engine.py

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Set
import zoneinfo

from dateutil.rrule import rrule, WEEKLY, MO, TU, WE, TH, FR, SA, SU


WEEKDAY_MAP = {
    0: MO,
    1: TU,
    2: WE,
    3: TH,
    4: FR,
    5: SA,
    6: SU,
}


@dataclass(frozen=True)
class CourseOccurrence:
    rule_id: str
    course_offering_id: str
    subject_code: str
    subject_name: str
    class_group_id: str
    class_group_name: str
    room_id: str
    room_name: str
    teacher_id: Optional[str]
    teacher_name: Optional[str]
    occurrence_date: date
    start_time: time
    end_time: time
    start_datetime_utc: datetime
    end_datetime_utc: datetime
    color_code: str
    is_exception: bool = False
    exception_type: Optional[str] = None
    exception_reason: Optional[str] = None
    timezone_name: str = "Africa/Douala"


class RecurrenceEngine:
    """Calculateur d'occurrences de cours avec récurrence hebdomadaire et exceptions (T1, T2)."""

    @staticmethod
    def local_to_utc(dt_local: datetime, tz_name: str = "Africa/Douala") -> datetime:
        """Convertit un datetime local (ex: Africa/Douala UTC+1) en UTC."""
        tz = zoneinfo.ZoneInfo(tz_name)
        if dt_local.tzinfo is None:
            dt_local = dt_local.replace(tzinfo=tz)
        return dt_local.astimezone(timezone.utc)

    @classmethod
    def generate_occurrences(
        cls,
        rule_id: str,
        course_offering_id: str,
        subject_code: str,
        subject_name: str,
        class_group_id: str,
        class_group_name: str,
        room_id: str,
        room_name: str,
        teacher_id: Optional[str],
        teacher_name: Optional[str],
        day_of_week: int,  # 0=Monday..6=Sunday
        start_time: time,
        end_time: time,
        rule_start_date: date,
        rule_end_date: date,
        range_start: date,
        range_end: date,
        color_code: str = "#3182CE",
        calendar_holiday_dates: Optional[Set[date]] = None,
        exceptions_map: Optional[dict] = None,  # date -> exception object or dict
        tz_name: str = "Africa/Douala",
    ) -> List[CourseOccurrence]:
        if calendar_holiday_dates is None:
            calendar_holiday_dates = set()
        if exceptions_map is None:
            exceptions_map = {}

        eff_start = max(rule_start_date, range_start)
        eff_end = min(rule_end_date, range_end)
        if eff_start > eff_end:
            return []

        byweekday = WEEKDAY_MAP.get(day_of_week, MO)

        # Generating dates via rrule
        dt_start = datetime.combine(eff_start, time(0, 0))
        dt_until = datetime.combine(eff_end, time(23, 59, 59))

        rule_dates = list(
            rrule(
                WEEKLY,
                byweekday=byweekday,
                dtstart=dt_start,
                until=dt_until,
            )
        )

        occurrences: List[CourseOccurrence] = []

        for r_dt in rule_dates:
            cur_date = r_dt.date()

            # 1. Exclude calendar holidays/vacation (T1)
            if cur_date in calendar_holiday_dates:
                continue

            # 2. Check targeted timetable exception
            exc = exceptions_map.get(cur_date)

            eff_room_id = room_id
            eff_room_name = room_name
            eff_teacher_id = teacher_id
            eff_teacher_name = teacher_name
            eff_start_time = start_time
            eff_end_time = end_time
            is_exception = False
            exc_type = None
            exc_reason = None

            if exc:
                exc_type_val = getattr(exc, "exception_type", None) or exc.get("exception_type")
                if isinstance(exc_type_val, str):
                    type_str = exc_type_val
                else:
                    type_str = exc_type_val.value if hasattr(exc_type_val, "value") else str(exc_type_val)

                if type_str == "CANCELLED":
                    # Skip cancelled occurrence
                    continue

                is_exception = True
                exc_type = type_str
                exc_reason = getattr(exc, "reason", None) or exc.get("reason")

                if type_str in ("MOVED", "ROOM_CHANGED"):
                    new_r_id = getattr(exc, "new_room_id", None) or exc.get("new_room_id")
                    new_r_name = getattr(exc, "new_room_name", None) or exc.get("new_room_name")
                    if new_r_id:
                        eff_room_id = str(new_r_id)
                        eff_room_name = new_r_name or eff_room_name

                if type_str in ("MOVED", "TEACHER_CHANGED"):
                    new_t_id = getattr(exc, "new_teacher_id", None) or exc.get("new_teacher_id")
                    new_t_name = getattr(exc, "new_teacher_name", None) or exc.get("new_teacher_name")
                    if new_t_id:
                        eff_teacher_id = str(new_t_id)
                        eff_teacher_name = new_t_name or eff_teacher_name

                if type_str == "MOVED":
                    new_st = getattr(exc, "new_start_time", None) or exc.get("new_start_time")
                    new_et = getattr(exc, "new_end_time", None) or exc.get("new_end_time")
                    if new_st:
                        eff_start_time = new_st
                    if new_et:
                        eff_end_time = new_et

            start_dt_local = datetime.combine(cur_date, eff_start_time)
            end_dt_local = datetime.combine(cur_date, eff_end_time)

            start_dt_utc = cls.local_to_utc(start_dt_local, tz_name)
            end_dt_utc = cls.local_to_utc(end_dt_local, tz_name)

            occurrences.append(
                CourseOccurrence(
                    rule_id=str(rule_id),
                    course_offering_id=str(course_offering_id),
                    subject_code=subject_code,
                    subject_name=subject_name,
                    class_group_id=str(class_group_id),
                    class_group_name=class_group_name,
                    room_id=str(eff_room_id),
                    room_name=eff_room_name,
                    teacher_id=str(eff_teacher_id) if eff_teacher_id else None,
                    teacher_name=eff_teacher_name,
                    occurrence_date=cur_date,
                    start_time=eff_start_time,
                    end_time=eff_end_time,
                    start_datetime_utc=start_dt_utc,
                    end_datetime_utc=end_dt_utc,
                    color_code=color_code,
                    is_exception=is_exception,
                    exception_type=exc_type,
                    exception_reason=exc_reason,
                    timezone_name=tz_name,
                )
            )

        return occurrences
