# backend/src/academy_context/domain/services/conflict_detector.py

from dataclasses import dataclass
from datetime import date, time
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class ConflictDetail:
    conflict_type: str  # "ROOM", "TEACHER", "CLASS_GROUP"
    conflicting_rule_id: str
    entity_id: str
    description: str
    day_of_week: int
    start_time: time
    end_time: time


@dataclass(frozen=True)
class AlternativeRoomSuggestion:
    room_id: str
    room_name: str
    building: Optional[str]
    capacity: int
    features: List[str]


@dataclass(frozen=True)
class ConflictCheckResult:
    has_conflict: bool
    conflicts: List[ConflictDetail]
    suggested_rooms: List[AlternativeRoomSuggestion]
    suggested_time_windows: List[Dict[str, Any]]


class ConflictDetectorService:
    """Service de domaine pur pour la détection des conflits de planning et la génération de suggestions (3.2)."""

    @staticmethod
    def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
        """Détermine si deux créneaux d'une même journée se chevauchent."""
        return start1 < end2 and end1 > start2

    @staticmethod
    def dates_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
        """Détermine si deux plages de dates se chevauchent."""
        return max(start1, start2) <= min(end1, end2)

    @classmethod
    def check_conflicts(
        cls,
        candidate_rule_id: Optional[str],
        tenant_id: str,
        room_id: str,
        class_group_id: str,
        teacher_id: Optional[str],
        day_of_week: int,  # 0..6
        start_time: time,
        end_time: time,
        start_date: date,
        end_date: date,
        existing_rules: List[Dict[str, Any]],
        available_rooms: Optional[List[Dict[str, Any]]] = None,
        existing_reservations: Optional[List[Dict[str, Any]]] = None,
        class_capacity_requirement: int = 0,
    ) -> ConflictCheckResult:
        if available_rooms is None:
            available_rooms = []
        if existing_reservations is None:
            existing_reservations = []

        conflicts: List[ConflictDetail] = []

        # 1. Vérification contre les règles existantes (3.2)
        for rule in existing_rules:
            # Règle auto-référente ignorée
            r_id = str(rule.get("id"))
            if candidate_rule_id and r_id == str(candidate_rule_id):
                continue

            r_tenant = str(rule.get("tenant_id"))
            if r_tenant != str(tenant_id):
                continue

            r_day = rule.get("day_of_week")
            if r_day != day_of_week:
                continue

            r_start_date = rule.get("start_date")
            r_end_date = rule.get("end_date")
            if not cls.dates_overlap(start_date, end_date, r_start_date, r_end_date):
                continue

            r_start_time = rule.get("start_time")
            r_end_time = rule.get("end_time")
            if not cls.times_overlap(start_time, end_time, r_start_time, r_end_time):
                continue

            # Check room collision
            r_room_id = str(rule.get("room_id"))
            if r_room_id == str(room_id):
                conflicts.append(
                    ConflictDetail(
                        conflict_type="ROOM",
                        conflicting_rule_id=r_id,
                        entity_id=r_room_id,
                        description=f"La salle {rule.get('room_name', r_room_id)} est déjà occupée par le cours {rule.get('subject_code', '')} ({r_start_time.strftime('%H:%M')} - {r_end_time.strftime('%H:%M')})",
                        day_of_week=day_of_week,
                        start_time=r_start_time,
                        end_time=r_end_time,
                    )
                )

            # Check teacher collision
            r_teacher_id = rule.get("teacher_id")
            if teacher_id and r_teacher_id and str(r_teacher_id) == str(teacher_id):
                conflicts.append(
                    ConflictDetail(
                        conflict_type="TEACHER",
                        conflicting_rule_id=r_id,
                        entity_id=str(r_teacher_id),
                        description=f"L'enseignant {rule.get('teacher_name', r_teacher_id)} a déjà un cours ({rule.get('subject_code', '')}) sur ce créneau ({r_start_time.strftime('%H:%M')} - {r_end_time.strftime('%H:%M')})",
                        day_of_week=day_of_week,
                        start_time=r_start_time,
                        end_time=r_end_time,
                    )
                )

            # Check class group collision
            r_class_id = str(rule.get("class_group_id"))
            if r_class_id == str(class_group_id):
                conflicts.append(
                    ConflictDetail(
                        conflict_type="CLASS_GROUP",
                        conflicting_rule_id=r_id,
                        entity_id=r_class_id,
                        description=f"La classe {rule.get('class_group_name', r_class_id)} a déjà le cours {rule.get('subject_code', '')} sur ce créneau ({r_start_time.strftime('%H:%M')} - {r_end_time.strftime('%H:%M')})",
                        day_of_week=day_of_week,
                        start_time=r_start_time,
                        end_time=r_end_time,
                    )
                )

        # 2. Check room reservations collision
        for res in existing_reservations:
            if str(res.get("room_id")) == str(room_id) and res.get("status") == "APPROVED":
                r_date = res.get("reservation_date")
                if cls.dates_overlap(start_date, end_date, r_date, r_date):
                    if r_date.weekday() == day_of_week:
                        if cls.times_overlap(start_time, end_time, res.get("start_time"), res.get("end_time")):
                            conflicts.append(
                                ConflictDetail(
                                    conflict_type="ROOM_RESERVATION",
                                    conflicting_rule_id=str(res.get("id")),
                                    entity_id=str(room_id),
                                    description=f"Réservation ponctuelle approved '{res.get('title')}' sur la salle le {r_date} ({res.get('start_time').strftime('%H:%M')}-{res.get('end_time').strftime('%H:%M')})",
                                    day_of_week=day_of_week,
                                    start_time=res.get("start_time"),
                                    end_time=res.get("end_time"),
                                )
                            )

        # 3. Generate Smart Suggestions (3.2)
        suggested_rooms: List[AlternativeRoomSuggestion] = []
        if conflicts:
            # Find rooms free on candidate day & time
            busy_room_ids = set()
            for r in existing_rules:
                if (
                    r.get("day_of_week") == day_of_week
                    and cls.dates_overlap(start_date, end_date, r.get("start_date"), r.get("end_date"))
                    and cls.times_overlap(start_time, end_time, r.get("start_time"), r.get("end_time"))
                    and (not candidate_rule_id or str(r.get("id")) != str(candidate_rule_id))
                ):
                    busy_room_ids.add(str(r.get("room_id")))

            for room_info in available_rooms:
                r_id = str(room_info.get("id"))
                if r_id != str(room_id) and r_id not in busy_room_ids:
                    cap = room_info.get("capacity", 0)
                    if class_capacity_requirement == 0 or cap >= class_capacity_requirement:
                        suggested_rooms.append(
                            AlternativeRoomSuggestion(
                                room_id=r_id,
                                room_name=room_info.get("name", "Salle"),
                                building=room_info.get("building"),
                                capacity=cap,
                                features=room_info.get("features", []),
                            )
                        )

        return ConflictCheckResult(
            has_conflict=len(conflicts) > 0,
            conflicts=conflicts,
            suggested_rooms=suggested_rooms,
            suggested_time_windows=[],
        )
