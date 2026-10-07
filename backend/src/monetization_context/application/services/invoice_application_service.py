import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from monetization_context.application.dtos import InvoiceDTO, InvoiceLineDTO
from monetization_context.infrastructure.persistence.models import (
    InvoiceModel,
    InvoiceLineModel,
    BillingSettingsModel,
)
from identity_context.infrastructure.persistence.models import TenantModel
from monetization_context.infrastructure.adapters.pdf_invoice_generator import PdfInvoiceGeneratorAdapter


class InvoiceApplicationService:
    """Service d'application pour la gestion des factures et l'export PDF."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pdf_adapter = PdfInvoiceGeneratorAdapter()

    async def get_tenant_invoices(
        self, tenant_id: uuid.UUID, status_filter: Optional[str] = None
    ) -> List[InvoiceDTO]:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.lines))
            .where(InvoiceModel.tenant_id == tenant_id)
            .order_by(InvoiceModel.issue_date.desc())
        )
        if status_filter:
            stmt = stmt.where(InvoiceModel.status == status_filter.upper())

        result = await self.session.execute(stmt)
        invoices = result.scalars().all()

        return [self._map_to_dto(inv) for inv in invoices]

    async def get_invoice_by_id(
        self, invoice_id: uuid.UUID, requesting_tenant_id: Optional[uuid.UUID] = None, is_super_admin: bool = False
    ) -> InvoiceModel:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.lines))
            .where(InvoiceModel.id == invoice_id)
        )
        result = await self.session.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable")

        if not is_super_admin and requesting_tenant_id and invoice.tenant_id != requesting_tenant_id:
            # Rejet d'accès inter-tenant (B10)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à la facture de cet établissement")

        return invoice

    async def generate_invoice_pdf(
        self, invoice_id: uuid.UUID, requesting_tenant_id: Optional[uuid.UUID] = None, is_super_admin: bool = False
    ) -> bytes:
        invoice = await self.get_invoice_by_id(invoice_id, requesting_tenant_id, is_super_admin)

        # Récupérer les infos de l'établissement
        tenant_stmt = select(TenantModel).where(TenantModel.id == invoice.tenant_id)
        tenant_res = await self.session.execute(tenant_stmt)
        tenant = tenant_res.scalar_one_or_none()

        # Récupérer les paramètres globaux de facturation
        settings_stmt = select(BillingSettingsModel).limit(1)
        settings_res = await self.session.execute(settings_stmt)
        b_settings = settings_res.scalar_one_or_none()

        invoice_data = {
            "invoice_number": invoice.number,
            "issue_date": invoice.issue_date.strftime("%Y-%m-%d"),
            "due_date": invoice.due_date.strftime("%Y-%m-%d"),
            "status": invoice.status,
            "company_name": b_settings.company_name if b_settings else "Pineapple OS SARL",
            "company_address": b_settings.company_address if b_settings else "Douala, Cameroun",
            "tax_id_number": b_settings.tax_id_number if b_settings else None,
            "tenant_name": tenant.name if tenant else "Établissement",
            "tenant_code": tenant.code if tenant else "TENANT",
            "tenant_contact_email": invoice.billing_contact_email or (tenant.contact_email if tenant else None),
            "line_items": [
                {
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price_xaf": line.unit_price_xaf,
                    "total_xaf": line.total_xaf,
                }
                for line in invoice.lines
            ],
            "subtotal_xaf": invoice.subtotal_xaf,
            "tax_rate_percent": invoice.tax_rate_percent,
            "tax_xaf": invoice.tax_xaf,
            "total_xaf": invoice.total_xaf,
            "legal_notice": b_settings.legal_notice if b_settings else "Facture payable en XAF FCFA.",
            "current_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

        return self.pdf_adapter.generate_pdf(invoice_data)

    def _map_to_dto(self, inv: InvoiceModel) -> InvoiceDTO:
        return InvoiceDTO(
            id=inv.id,
            tenant_id=inv.tenant_id,
            number=inv.number,
            academic_year=inv.academic_year,
            status=inv.status,
            subtotal_xaf=inv.subtotal_xaf,
            tax_rate_percent=inv.tax_rate_percent,
            tax_xaf=inv.tax_xaf,
            total_xaf=inv.total_xaf,
            issue_date=inv.issue_date,
            due_date=inv.due_date,
            paid_at=inv.paid_at,
            pdf_url=inv.pdf_url,
            billing_contact_email=inv.billing_contact_email,
            lines=[
                InvoiceLineDTO(
                    id=line.id,
                    description=line.description,
                    quantity=line.quantity,
                    unit_price_xaf=line.unit_price_xaf,
                    total_xaf=line.total_xaf,
                )
                for line in (inv.lines or [])
            ],
        )
