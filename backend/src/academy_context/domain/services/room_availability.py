# backend/src/academy_context/domain/services/room_availability.py

import uuid
from datetime import date, datetime, time, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from community_context.infrastructure.persistence.models import RoomModel, RoomStatusDeclarationModel
from community_context.domain.value_objects import RoomStatus
from academy_context.domain.value_objects import TimetableExceptionType, ReservationStatus
from academy_context.infrastructure.persistence.models import (
    RoomReservationModel,
    TimetableRuleModel, TimetableExceptionModel, RoomFeatureModel
)
from academy_context.domain.services.recurrence_engine import RecurrenceEngine


class RoomAvailabilityService:
    """
    Service d'évaluation de la disponibilité réelle des salles selon l'algorithme de priorité T3 :
    1. Délégué (room_status_declarations ou status manuel actif non expiré)
    2. Réservation approuvée (RoomReservationModel status=APPROVED)
    3. Cours planifié (TimetableRuleModel actif sauf exception CANCELLED)
    4. Libre (FREE)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rooms_availability(
        self,
        tenant_id: uuid.UUID,
        target_date: date,
        start_time: time,
        end_time: time,
        min_capacity: Optional[int] = None,
        required_features: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        # 1. Fetch active rooms in tenant
        stmt = select(RoomModel).where(
            RoomModel.tenant_id == tenant_id,
            RoomModel.is_active == True
        )
        if min_capacity is not None:
            stmt = stmt.where(RoomModel.capacity >= min_capacity)
        
        result = await self.db.execute(stmt)
        rooms = result.scalars().all()

        # Filter features if required
        if required_features:
            feat_stmt = select(RoomFeatureModel.room_id).where(
                RoomFeatureModel.tenant_id == tenant_id,
                RoomFeatureModel.feature_code.in_(required_features)
            )
            feat_res = await self.db.execute(feat_stmt)
            room_ids_with_features = set(feat_res.scalars().all())
            rooms = [r for r in rooms if r.id in room_ids_with_features]

        target_dt_start = datetime.combine(target_date, start_time)
        target_dt_end = datetime.combine(target_date, end_time)

        # 2. Fetch approved reservations for target_date
        res_stmt = select(RoomReservationModel).where(
            RoomReservationModel.tenant_id == tenant_id,
            RoomReservationModel.reservation_date == target_date,
            RoomReservationModel.status == ReservationStatus.APPROVED,
            RoomReservationModel.start_time < end_time,
            RoomReservationModel.end_time > start_time
        )
        res_results = (await self.db.execute(res_stmt)).scalars().all()
        reservations_by_room = {r.room_id: r for r in res_results}

        # 3. Fetch active timetable rules for the tenant
        rules_stmt = select(TimetableRuleModel).where(
            TimetableRuleModel.tenant_id == tenant_id,
            TimetableRuleModel.is_active == True,
            TimetableRuleModel.start_date <= target_date,
            or_(TimetableRuleModel.end_date == None, TimetableRuleModel.end_date >= target_date)
        )
        rules = (await self.db.execute(rules_stmt)).scalars().all()

        # 4. Fetch timetable exceptions for target_date
        ex_stmt = select(TimetableExceptionModel).where(
            TimetableExceptionModel.tenant_id == tenant_id,
            TimetableExceptionModel.target_date == target_date
        )
        exceptions = (await self.db.execute(ex_stmt)).scalars().all()
        cancelled_rule_ids = {e.rule_id for e in exceptions if e.exception_type == TimetableExceptionType.CANCELLED and e.rule_id}

        # 5. Evaluate availability for each room using T3 Priority
        availability_list = []
        for room in rooms:
            # Check Priority 1: Delegate declaration
            # Check RoomStatusDeclarationModel first if active
            decl_stmt = select(RoomStatusDeclarationModel).where(
                RoomStatusDeclarationModel.room_id == room.id,
                RoomStatusDeclarationModel.declared_at <= datetime.now(timezone.utc),
                RoomStatusDeclarationModel.expires_at >= datetime.now(timezone.utc)
            ).order_by(RoomStatusDeclarationModel.declared_at.desc())
            latest_decl = (await self.db.execute(decl_stmt)).scalars().first()

            status = RoomStatus.FREE
            reason = "Salle libre"
            active_event = None

            if latest_decl and latest_decl.status in (RoomStatus.OCCUPIED, RoomStatus.TO_CONFIRM):
                status = latest_decl.status
                reason = f"Déclaration délégué : {latest_decl.note or status.value}"
            elif room.expires_at and room.expires_at > datetime.now(timezone.utc) and room.status in (RoomStatus.OCCUPIED, RoomStatus.TO_CONFIRM):
                status = room.status
                reason = f"Statut manuel actif : {room.status.value}"
            elif room.id in reservations_by_room:
                # Priority 2: Approved reservation
                res = reservations_by_room[room.id]
                status = RoomStatus.RESERVED
                reason = f"Réservée : {res.title}"
                active_event = {
                    "type": "RESERVATION",
                    "title": res.title,
                    "start_time": res.start_time.isoformat(),
                    "end_time": res.end_time.isoformat()
                }
            else:
                # Priority 3: Scheduled course
                scheduled_course = None
                for rule in rules:
                    if rule.room_id == room.id and rule.id not in cancelled_rule_ids:
                        # Check recurrence
                        if RecurrenceEngine.matches_date(rule, target_date):
                            if rule.start_time < end_time and rule.end_time > start_time:
                                scheduled_course = rule
                                break
                if scheduled_course:
                    status = RoomStatus.OCCUPIED_SCHEDULED
                    reason = "Cours planifié"
                    active_event = {
                        "type": "COURSE",
                        "rule_id": str(scheduled_course.id),
                        "offering_id": str(scheduled_course.course_offering_id),
                        "start_time": scheduled_course.start_time.isoformat(),
                        "end_time": scheduled_course.end_time.isoformat()
                    }

            availability_list.append({
                "room_id": str(room.id),
                "room_name": room.name,
                "building": room.building,
                "capacity": room.capacity,
                "status": status.value if hasattr(status, 'value') else str(status),
                "reason": reason,
                "active_event": active_event
            })

        return availability_list
