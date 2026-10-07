# tests/unit/test_timetable_concurrency.py

import asyncio
import uuid
from datetime import date, time
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from shared_kernel.infrastructure.database import Base
from identity_context.infrastructure.persistence.models import TenantModel, ClassGroupModel, UserModel
from community_context.infrastructure.persistence.models import RoomModel
from academy_context.infrastructure.persistence.models import (
    AcademicTermModel,
    SubjectModel,
    CourseOfferingModel,
    TimetableRuleModel,
)


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session, session_factory

    await engine.dispose()


@pytest.mark.asyncio
async def test_sec_003_concurrent_booking_only_one_succeeds(async_db):
    """
    Gate E3: Teste que deux transactions concurrentes tentant de réserver
    la même salle sur le même créneau ne créent pas un double booking.
    """
    session, session_factory = async_db

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    room_id = uuid.uuid4()
    term_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    class_id = uuid.uuid4()
    offering_id = uuid.uuid4()

    # Create prerequisites
    tenant = TenantModel(id=tenant_id, name="Campus Tech", code="CTECH")
    user = UserModel(id=user_id, email="prof@campustech.cm", first_name="Prof", last_name="MBIDA", hashed_password="hash")
    room = RoomModel(id=room_id, tenant_id=tenant_id, name="Amphi A", capacity=150)
    term = AcademicTermModel(
        id=term_id, tenant_id=tenant_id, name="Semestre 1", academic_year="2026-2027",
        start_date=date(2026, 10, 1), end_date=date(2027, 2, 28)
    )
    subject = SubjectModel(id=subject_id, tenant_id=tenant_id, code="INF301", name="Algorithmique")
    class_group = ClassGroupModel(id=class_id, tenant_id=tenant_id, name="Génie Informatique 3", code="GIT3", academic_year="2026-2027")
    offering = CourseOfferingModel(
        id=offering_id, tenant_id=tenant_id, term_id=term_id, subject_id=subject_id,
        class_group_id=class_id, teacher_id=user_id
    )

    session.add_all([tenant, user, room, term, subject, class_group, offering])
    await session.commit()

    async def attempt_booking(task_id: int):
        async with session_factory() as sess:
            async with sess.begin():
                # Transaction lock check
                stmt = select(TimetableRuleModel).where(
                    TimetableRuleModel.tenant_id == tenant_id,
                    TimetableRuleModel.room_id == room_id,
                    TimetableRuleModel.day_of_week == 0,
                    TimetableRuleModel.start_time < time(10, 0),
                    TimetableRuleModel.end_time > time(8, 0),
                    TimetableRuleModel.is_active == True,
                ).with_for_update()

                res = await sess.execute(stmt)
                existing = res.scalars().all()
                if existing:
                    return False, "ROOM_BUSY"

                # Simulate small microsecond delay
                await asyncio.sleep(0.01)

                try:
                    rule = TimetableRuleModel(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        course_offering_id=offering_id,
                        room_id=room_id,
                        day_of_week=0,
                        start_time=time(8, 0),
                        end_time=time(10, 0),
                        start_date=date(2026, 10, 1),
                        end_date=date(2027, 2, 28),
                    )
                    sess.add(rule)
                    await sess.commit()
                    return True, "SUCCESS"
                except Exception:
                    await sess.rollback()
                    return False, "CONCURRENCY_CONFLICT"

    # Run two concurrent booking tasks
    res1, res2 = await asyncio.gather(
        attempt_booking(1),
        attempt_booking(2),
        return_exceptions=True
    )

    results = [res1[0] if isinstance(res1, tuple) else False, res2[0] if isinstance(res2, tuple) else False]
    success_count = sum(1 for r in results if r is True)

    assert success_count == 1, f"Expected exactly 1 booking success under concurrency, got {success_count}"
