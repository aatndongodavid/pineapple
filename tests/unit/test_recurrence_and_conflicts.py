# tests/unit/test_recurrence_and_conflicts.py

import uuid
from datetime import date, time, timedelta, datetime
import pytest
from hypothesis import given, strategies as st

from academy_context.domain.services.recurrence_engine import RecurrenceEngine
from academy_context.domain.services.conflict_detector import ConflictDetectorService


def test_gate_e1_recurrence_engine_generates_occurrences_excluding_holidays():
    """Gate E1: Création d'un cours sans conflit -> occurrences correctes sur le semestre, jours fériés exclus."""
    rule_id = str(uuid.uuid4())
    offering_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    class_id = str(uuid.uuid4())
    teacher_id = str(uuid.uuid4())

    # Octobre 2026: 05-Oct (Mon), 12-Oct (Mon), 19-Oct (Mon), 26-Oct (Mon)
    start_date = date(2026, 10, 1)
    end_date = date(2026, 10, 31)

    # Jour férié le lundi 12 Octobre
    holidays = {date(2026, 10, 12)}

    occurrences = RecurrenceEngine.generate_occurrences(
        rule_id=rule_id,
        course_offering_id=offering_id,
        subject_code="INF301",
        subject_name="Algorithmique",
        class_group_id=class_id,
        class_group_name="GIT3",
        room_id=room_id,
        room_name="Amphi A",
        teacher_id=teacher_id,
        teacher_name="Prof MBIDA",
        day_of_week=0,  # Monday
        start_time=time(8, 0),
        end_time=time(10, 0),
        rule_start_date=start_date,
        rule_end_date=end_date,
        range_start=start_date,
        range_end=end_date,
        calendar_holiday_dates=holidays,
    )

    occurrence_dates = [occ.occurrence_date for occ in occurrences]
    assert len(occurrences) == 3
    assert date(2026, 10, 5) in occurrence_dates
    assert date(2026, 10, 12) not in occurrence_dates  # Excluded!
    assert date(2026, 10, 19) in occurrence_dates
    assert date(2026, 10, 26) in occurrence_dates


def test_gate_e5_recurrence_engine_applies_occurrence_cancellation_and_move():
    """Gate E5: Annulation et modification d'une occurrence ciblée."""
    rule_id = str(uuid.uuid4())
    offering_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    new_room_id = str(uuid.uuid4())
    class_id = str(uuid.uuid4())

    start_date = date(2026, 10, 1)
    end_date = date(2026, 10, 31)

    # 12-Oct CANCELLED, 19-Oct MOVED to new_room_id
    exceptions_map = {
        date(2026, 10, 12): {"exception_type": "CANCELLED", "reason": "Prof indisponible"},
        date(2026, 10, 19): {"exception_type": "ROOM_CHANGED", "new_room_id": new_room_id, "new_room_name": "Labo 2"},
    }

    occurrences = RecurrenceEngine.generate_occurrences(
        rule_id=rule_id,
        course_offering_id=offering_id,
        subject_code="INF301",
        subject_name="Algorithmique",
        class_group_id=class_id,
        class_group_name="GIT3",
        room_id=room_id,
        room_name="Amphi A",
        teacher_id=None,
        teacher_name=None,
        day_of_week=0,
        start_time=time(8, 0),
        end_time=time(10, 0),
        rule_start_date=start_date,
        rule_end_date=end_date,
        range_start=start_date,
        range_end=end_date,
        exceptions_map=exceptions_map,
    )

    occurrence_dates = [occ.occurrence_date for occ in occurrences]
    assert len(occurrences) == 3
    assert date(2026, 10, 12) not in occurrence_dates

    occ_19 = next(o for o in occurrences if o.occurrence_date == date(2026, 10, 19))
    assert occ_19.room_id == new_room_id
    assert occ_19.is_exception is True
    assert occ_19.exception_type == "ROOM_CHANGED"


def test_gate_e2_conflict_detector_detects_room_and_teacher_conflicts():
    """Gate E2: Deux cours dans la même salle au même créneau -> refusé avec détail et suggestions."""
    tenant_id = str(uuid.uuid4())
    room1 = str(uuid.uuid4())
    room2 = str(uuid.uuid4())
    teacher1 = str(uuid.uuid4())
    class1 = str(uuid.uuid4())
    class2 = str(uuid.uuid4())

    existing_rules = [
        {
            "id": "rule-100",
            "tenant_id": tenant_id,
            "room_id": room1,
            "room_name": "Amphi A",
            "class_group_id": class1,
            "class_group_name": "GIT3",
            "teacher_id": teacher1,
            "teacher_name": "Prof MBIDA",
            "day_of_week": 0,  # Monday
            "start_time": time(8, 0),
            "end_time": time(10, 0),
            "start_date": date(2026, 10, 1),
            "end_date": date(2027, 2, 28),
            "subject_code": "INF301",
        }
    ]

    available_rooms = [
        {"id": room1, "name": "Amphi A", "building": "Bloc B", "capacity": 150},
        {"id": room2, "name": "Salle B12", "building": "Bloc B", "capacity": 60},
    ]

    # Tentative de réserver Amphi A le lundi de 9h à 11h (chevauchement 9h-10h) pour la classe 2
    res = ConflictDetectorService.check_conflicts(
        candidate_rule_id=None,
        tenant_id=tenant_id,
        room_id=room1,
        class_group_id=class2,
        teacher_id=str(uuid.uuid4()),
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(11, 0),
        start_date=date(2026, 10, 1),
        end_date=date(2027, 2, 28),
        existing_rules=existing_rules,
        available_rooms=available_rooms,
    )

    assert res.has_conflict is True
    assert len(res.conflicts) == 1
    assert res.conflicts[0].conflict_type == "ROOM"
    assert "Amphi A est déjà occupée" in res.conflicts[0].description

    # Suggestions d'alternatives (Salle B12 disponible)
    assert len(res.suggested_rooms) == 1
    assert res.suggested_rooms[0].room_id == room2
    assert res.suggested_rooms[0].room_name == "Salle B12"


def test_conflict_detector_self_conflict_freedom():
    """Vérifie qu'une règle en cours d'édition ne rentre pas en conflit avec elle-même."""
    tenant_id = str(uuid.uuid4())
    room_id = str(uuid.uuid4())
    rule_id = "rule-200"

    existing_rules = [
        {
            "id": rule_id,
            "tenant_id": tenant_id,
            "room_id": room_id,
            "class_group_id": str(uuid.uuid4()),
            "teacher_id": str(uuid.uuid4()),
            "day_of_week": 1,
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "start_date": date(2026, 10, 1),
            "end_date": date(2027, 2, 28),
        }
    ]

    # Editing rule-200 with same parameters
    res = ConflictDetectorService.check_conflicts(
        candidate_rule_id=rule_id,
        tenant_id=tenant_id,
        room_id=room_id,
        class_group_id=existing_rules[0]["class_group_id"],
        teacher_id=existing_rules[0]["teacher_id"],
        day_of_week=1,
        start_time=time(10, 0),
        end_time=time(12, 0),
        start_date=date(2026, 10, 1),
        end_date=date(2027, 2, 28),
        existing_rules=existing_rules,
    )

    assert res.has_conflict is False


# ---------------------------------------------------------------------------
# Property-Based Tests (Hypothesis)
# ---------------------------------------------------------------------------

@given(
    start1_min=st.integers(min_value=6, max_value=16),
    dur1_hrs=st.integers(min_value=1, max_value=4),
    start2_min=st.integers(min_value=6, max_value=16),
    dur2_hrs=st.integers(min_value=1, max_value=4),
)
def test_hypothesis_time_overlap_symmetry(start1_min, dur1_hrs, start2_min, dur2_hrs):
    """Propriété hypothesis: la détection de chevauchement temporel est strictement symétrique."""
    t1_s = time(start1_min, 0)
    t1_e = time(start1_min + dur1_hrs, 0)
    t2_s = time(start2_min, 0)
    t2_e = time(start2_min + dur2_hrs, 0)

    overlap1 = ConflictDetectorService.times_overlap(t1_s, t1_e, t2_s, t2_e)
    overlap2 = ConflictDetectorService.times_overlap(t2_s, t2_e, t1_s, t1_e)

    assert overlap1 == overlap2
