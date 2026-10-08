import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.infrastructure.persistence.models import DemoRequestModel
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.email_gateway import email_gateway
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_permission,
)

public_router = APIRouter(prefix="/public/demo-requests", tags=["Public Demo Requests"])
admin_router = APIRouter(prefix="/admin/demo-requests", tags=["Admin Demo Requests"])


class DemoRequestDTO(BaseModel):
    institution_name: str
    contact_name: str
    role: str
    email: EmailStr
    whatsapp_phone: str
    student_count_range: str
    notes: Optional[str] = None
    website_url_hp: Optional[str] = None  # Honeypot field


class StatusUpdateDTO(BaseModel):
    status: str  # NEW, CONTACTED, QUALIFIED, CONVERTED, ARCHIVED


@public_router.post("", status_code=status.HTTP_201_CREATED)
async def submit_demo_request(
    dto: DemoRequestDTO,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Soumission d'une demande de démo avec filtre honeypot et rate-limiting IP."""
    # Gate W3: Honeypot check
    if dto.website_url_hp and dto.website_url_hp.strip():
        # Bot detected — return fake 201 success without saving or sending email
        return {
            "status": "success",
            "message": "Demande de démonstration enregistrée.",
            "request_id": str(uuid.uuid4()),
        }

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # Gate W3: IP Rate Limiting (Max 5 req/hour per IP)
    count_stmt = select(func.count(DemoRequestModel.id)).where(
        DemoRequestModel.ip_address == client_ip,
        DemoRequestModel.created_at >= one_hour_ago,
    )
    res = await db.execute(count_stmt)
    recent_requests_count = res.scalar() or 0

    if recent_requests_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de demandes soumises depuis cette adresse IP. Veuillez réessayer dans une heure.",
        )

    # Save to database
    req_id = uuid.uuid4()
    user_agent = request.headers.get("user-agent", "")[:500]

    demo_req = DemoRequestModel(
        id=req_id,
        institution_name=dto.institution_name.strip(),
        contact_name=dto.contact_name.strip(),
        role=dto.role.strip(),
        email=dto.email.lower().strip(),
        whatsapp_phone=dto.whatsapp_phone.strip(),
        student_count_range=dto.student_count_range.strip(),
        notes=dto.notes.strip() if dto.notes else None,
        status="NEW",
        ip_address=client_ip,
        user_agent=user_agent,
        created_at=now,
    )
    db.add(demo_req)
    await db.commit()

    # Send Applicant Confirmation Email
    applicant_html = f"""
    <h2>Confirmation de votre demande de démonstration Pineapple OS</h2>
    <p>Bonjour {dto.contact_name},</p>
    <p>Nous avons bien reçu votre demande pour <b>{dto.institution_name}</b>.</p>
    <p>Un conseiller académique Pineapple vous contactera sous 24 heures au <b>{dto.whatsapp_phone}</b> ou par email.</p>
    <p>En attendant, découvrez notre démo bac à sable en ligne : <a href="https://demo.pineapple.cm">https://demo.pineapple.cm</a></p>
    <br/>
    <p>Cordialement,<br/><b>L'équipe Pineapple OS</b></p>
    """
    await email_gateway.send_email(
        dto.email,
        f"Démonstration Pineapple OS — {dto.institution_name}",
        applicant_html,
    )

    # Send Internal Notification to Sales Team
    internal_html = f"""
    <h2>🚀 NOUVELLE DEMANDE DE DÉMO RECEVUE !</h2>
    <ul>
        <li><b>Établissement :</b> {dto.institution_name}</li>
        <li><b>Responsable :</b> {dto.contact_name} ({dto.role})</li>
        <li><b>Email :</b> {dto.email}</li>
        <li><b>WhatsApp :</b> {dto.whatsapp_phone}</li>
        <li><b>Effectif :</b> {dto.student_count_range}</li>
        <li><b>Notes :</b> {dto.notes or 'Aucune'}</li>
        <li><b>IP :</b> {client_ip}</li>
    </ul>
    """
    await email_gateway.send_email(
        "contact@pineapple.cm",
        f"[DEMO LEAD] {dto.institution_name} ({dto.student_count_range})",
        internal_html,
    )

    return {
        "status": "success",
        "message": "Demande de démonstration enregistrée avec succès.",
        "request_id": str(req_id),
    }


@admin_router.get("")
async def list_demo_requests(
    status_filter: Optional[str] = None,
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Liste des demandes de démo pour la console Super-Admin."""
    stmt = select(DemoRequestModel).order_by(DemoRequestModel.created_at.desc())
    if status_filter:
        stmt = stmt.where(DemoRequestModel.status == status_filter.upper())

    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": str(r.id),
            "institution_name": r.institution_name,
            "contact_name": r.contact_name,
            "role": r.role,
            "email": r.email,
            "whatsapp_phone": r.whatsapp_phone,
            "student_count_range": r.student_count_range,
            "notes": r.notes,
            "status": r.status,
            "ip_address": r.ip_address,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@admin_router.get("/export.csv")
async def export_demo_requests_csv(
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Export CSV de toutes les demandes de démo pour le suivi commercial."""
    stmt = select(DemoRequestModel).order_by(DemoRequestModel.created_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID",
        "Date",
        "Etablissement",
        "Responsable",
        "Role",
        "Email",
        "WhatsApp",
        "Effectif",
        "Statut",
        "Notes",
    ])

    for r in records:
        writer.writerow([
            str(r.id),
            r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            r.institution_name,
            r.contact_name,
            r.role,
            r.email,
            r.whatsapp_phone,
            r.student_count_range,
            r.status,
            r.notes or "",
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=demo_requests_pineapple.csv"},
    )


@admin_router.patch("/{request_id}/status")
async def update_demo_request_status(
    request_id: str,
    dto: StatusUpdateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Mise à jour du statut d'une demande de démo (NEW -> CONTACTED -> QUALIFIED -> CONVERTED)."""
    req_uuid = uuid.UUID(request_id)
    stmt = select(DemoRequestModel).where(DemoRequestModel.id == req_uuid)
    res = await db.execute(stmt)
    demo_req = res.scalars().first()

    if not demo_req:
        raise HTTPException(status_code=404, detail="Demande de démo non trouvée")

    demo_req.status = dto.status.upper()
    await db.commit()

    return {"status": demo_req.status, "request_id": str(demo_req.id)}
