import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from community_context.infrastructure.persistence.models import (
    ClassAnnouncementModel,
    ClassEventModel,
    ClassIncidentModel,
    ClassPollModel,
    ClassPollOptionModel,
    ClassPollVoteModel,
)
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_class_scope,
    require_membership,
    require_permission,
)

router = APIRouter(prefix="/classes", tags=["Class & Delegate Features"])


# DTOs
class AnnouncementCreateDTO(BaseModel):
    title: str
    content: str
    is_pinned: bool = False


class IncidentCreateDTO(BaseModel):
    title: str
    description: str
    category: str = "TEACHER_ABSENT"  # TEACHER_ABSENT, COURSE_CANCELLED, ROOM_ISSUE, REQUEST, OTHER


class PollOptionDTO(BaseModel):
    option_text: str


class PollCreateDTO(BaseModel):
    question: str
    options: List[str]


class VoteRequestDTO(BaseModel):
    option_id: str


class EventCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str = "EVENT"  # EXAM, ASSIGNMENT, EVENT
    start_time: str
    end_time: Optional[str] = None


# --- ANNONCES DE CLASSE ---
@router.get("/{class_id}/announcements")
async def list_class_announcements(
    class_id: str,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    stmt = (
        select(ClassAnnouncementModel)
        .where(ClassAnnouncementModel.class_group_id == cid)
        .order_by(ClassAnnouncementModel.is_pinned.desc(), ClassAnnouncementModel.created_at.desc())
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "content": a.content,
            "is_pinned": a.is_pinned,
            "author_id": str(a.author_id),
            "created_at": a.created_at.isoformat(),
        }
        for a in items
    ]


@router.post("/{class_id}/announcements", status_code=status.HTTP_201_CREATED)
async def create_class_announcement(
    class_id: str,
    dto: AnnouncementCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("class.announce")),
    _scope: AuthenticatedUserContext = Depends(require_class_scope("class_id")),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    anc = ClassAnnouncementModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        class_group_id=cid,
        title=dto.title,
        content=dto.content,
        is_pinned=dto.is_pinned,
        author_id=ctx.user_id,
    )
    db.add(anc)
    await db.commit()
    return {"id": str(anc.id), "title": anc.title}


# --- SIGNALEMENTS D'INCIDENTS ---
@router.get("/{class_id}/incidents")
async def list_class_incidents(
    class_id: str,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    stmt = select(ClassIncidentModel).where(ClassIncidentModel.class_group_id == cid).order_by(ClassIncidentModel.created_at.desc())
    res = await db.execute(stmt)
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "description": i.description,
            "category": i.category,
            "status": i.status,
            "reported_by": str(i.reported_by),
            "created_at": i.created_at.isoformat(),
        }
        for i in res.scalars().all()
    ]


@router.post("/{class_id}/incidents", status_code=status.HTTP_201_CREATED)
async def report_class_incident(
    class_id: str,
    dto: IncidentCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("class.incident.report")),
    _scope: AuthenticatedUserContext = Depends(require_class_scope("class_id")),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    inc = ClassIncidentModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        class_group_id=cid,
        title=dto.title,
        description=dto.description,
        category=dto.category,
        status="OPEN",
        reported_by=ctx.user_id,
    )
    db.add(inc)
    await db.commit()
    return {"id": str(inc.id), "status": "OPEN"}


# --- SONDAGES DE CLASSE ---
@router.get("/{class_id}/polls")
async def list_class_polls(
    class_id: str,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    stmt = select(ClassPollModel).where(ClassPollModel.class_group_id == cid).order_by(ClassPollModel.created_at.desc())
    polls = (await db.execute(stmt)).scalars().all()

    output = []
    for p in polls:
        opt_stmt = select(ClassPollOptionModel).where(ClassPollOptionModel.poll_id == p.id)
        opts = (await db.execute(opt_stmt)).scalars().all()

        vote_stmt = select(ClassPollVoteModel).where(ClassPollVoteModel.poll_id == p.id, ClassPollVoteModel.user_id == ctx.user_id)
        user_vote = (await db.execute(vote_stmt)).scalars().first()

        output.append({
            "id": str(p.id),
            "question": p.question,
            "is_closed": p.is_closed,
            "user_has_voted": user_vote is not None,
            "voted_option_id": str(user_vote.option_id) if user_vote else None,
            "options": [{"id": str(o.id), "option_text": o.option_text, "vote_count": o.vote_count} for o in opts],
        })
    return output


@router.post("/{class_id}/polls", status_code=status.HTTP_201_CREATED)
async def create_class_poll(
    class_id: str,
    dto: PollCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("class.poll.create")),
    _scope: AuthenticatedUserContext = Depends(require_class_scope("class_id")),
    db: AsyncSession = Depends(get_db_session),
):
    if len(dto.options) < 2:
        raise HTTPException(status_code=400, detail="Au moins 2 options sont requises")

    cid = uuid.UUID(class_id)
    poll = ClassPollModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        class_group_id=cid,
        question=dto.question,
        is_closed=False,
        created_by=ctx.user_id,
    )
    db.add(poll)

    for opt_text in dto.options:
        opt = ClassPollOptionModel(
            id=uuid.uuid4(),
            poll_id=poll.id,
            option_text=opt_text.strip(),
            vote_count=0,
        )
        db.add(opt)

    await db.commit()
    return {"id": str(poll.id), "question": poll.question}


@router.post("/{class_id}/polls/{poll_id}/vote")
async def vote_class_poll(
    class_id: str,
    poll_id: str,
    dto: VoteRequestDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("class.poll.vote")),
    db: AsyncSession = Depends(get_db_session),
):
    pid = uuid.UUID(poll_id)
    oid = uuid.UUID(dto.option_id)

    poll = await db.get(ClassPollModel, pid)
    if not poll or poll.is_closed:
        raise HTTPException(status_code=400, detail="Sondage inexistant ou clôturé")

    v_stmt = select(ClassPollVoteModel).where(ClassPollVoteModel.poll_id == pid, ClassPollVoteModel.user_id == ctx.user_id)
    if (await db.execute(v_stmt)).scalars().first():
        raise HTTPException(status_code=400, detail="Vous avez déjà voté sur ce sondage")

    vote = ClassPollVoteModel(
        id=uuid.uuid4(),
        poll_id=pid,
        option_id=oid,
        user_id=ctx.user_id,
    )
    db.add(vote)

    option = await db.get(ClassPollOptionModel, oid)
    if option:
        option.vote_count += 1

    await db.commit()
    return {"status": "ok"}


# --- CALENDRIER DE CLASSE ---
@router.get("/{class_id}/events")
async def list_class_events(
    class_id: str,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    stmt = select(ClassEventModel).where(ClassEventModel.class_group_id == cid).order_by(ClassEventModel.start_time.asc())
    res = await db.execute(stmt)
    return [
        {
            "id": str(e.id),
            "title": e.title,
            "description": e.description,
            "event_type": e.event_type,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat() if e.end_time else None,
        }
        for e in res.scalars().all()
    ]


@router.post("/{class_id}/events", status_code=status.HTTP_201_CREATED)
async def create_class_event(
    class_id: str,
    dto: EventCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("class.event.manage")),
    _scope: AuthenticatedUserContext = Depends(require_class_scope("class_id")),
    db: AsyncSession = Depends(get_db_session),
):
    cid = uuid.UUID(class_id)
    ev = ClassEventModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        class_group_id=cid,
        title=dto.title,
        description=dto.description,
        event_type=dto.event_type,
        start_time=datetime.fromisoformat(dto.start_time),
        end_time=datetime.fromisoformat(dto.end_time) if dto.end_time else None,
        created_by=ctx.user_id,
    )
    db.add(ev)
    await db.commit()
    return {"id": str(ev.id), "title": ev.title}
