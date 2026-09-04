import io
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.ports import (
    LibraryRepositoryPort,
    PurchaseRepositoryPort,
    WatermarkEnginePort,
)
from academy_context.domain.value_objects import DocumentType, WatermarkMetadata
from academy_context.infrastructure.persistence.models import (
    LibraryDocumentModel,
    PurchaseModel,
)
from shared_kernel.domain.value_objects import Money


class PostgresLibraryRepository(LibraryRepositoryPort):
    """Implémentation PostgreSQL du port LibraryRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: LibraryDocumentModel) -> LibraryDocument:
        return LibraryDocument(
            id=model.id,
            tenant_id=model.tenant_id,
            title=model.title,
            document_type=model.document_type,
            s3_key=model.s3_key,
            is_premium=model.is_premium,
            price=Money(amount=Decimal(model.price_amount), currency="XAF"),
            faculty=model.faculty,
            filiere=model.filiere,
            academic_level=model.academic_level,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(doc: LibraryDocument) -> LibraryDocumentModel:
        return LibraryDocumentModel(
            id=doc.id,
            tenant_id=doc.tenant_id,
            title=doc.title,
            document_type=doc.document_type,
            s3_key=doc.s3_key,
            is_premium=doc.is_premium,
            price_amount=int(doc.price.amount),
            faculty=doc.faculty,
            filiere=doc.filiere,
            academic_level=doc.academic_level,
            created_at=doc.created_at,
        )

    async def save_document(self, doc: LibraryDocument) -> LibraryDocument:
        async with self._session_factory() as session:
            model = self._to_model(doc)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return doc

    async def get_document_by_id(self, doc_id: UUID, tenant_id: UUID) -> Optional[LibraryDocument]:
        async with self._session_factory() as session:
            stmt = select(LibraryDocumentModel).where(
                LibraryDocumentModel.id == doc_id,
                LibraryDocumentModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_documents(
        self,
        tenant_id: UUID,
        faculty: Optional[str],
        level: Optional[str],
        doc_type: Optional[DocumentType],
    ) -> List[LibraryDocument]:
        async with self._session_factory() as session:
            stmt = select(LibraryDocumentModel).where(
                LibraryDocumentModel.tenant_id == tenant_id
            )
            if faculty:
                stmt = stmt.where(LibraryDocumentModel.faculty == faculty)
            if level:
                stmt = stmt.where(LibraryDocumentModel.academic_level == level)
            if doc_type:
                stmt = stmt.where(LibraryDocumentModel.document_type == doc_type)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresPurchaseRepository(PurchaseRepositoryPort):
    """Implémentation PostgreSQL du port PurchaseRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: PurchaseModel) -> PremiumPurchase:
        return PremiumPurchase(
            id=model.id,
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            document_id=model.document_id,
            price_paid=Money(amount=Decimal(model.price_paid), currency="XAF"),
            purchased_at=model.purchased_at,
            is_active=True,  # Le modèle ne stocke pas is_active, on suppose True
        )

    @staticmethod
    def _to_model(purchase: PremiumPurchase) -> PurchaseModel:
        return PurchaseModel(
            id=purchase.id,
            tenant_id=purchase.tenant_id,
            user_id=purchase.user_id,
            document_id=purchase.document_id,
            price_paid=int(purchase.price_paid.amount),
            purchased_at=purchase.purchased_at,
        )

    async def save_purchase(self, purchase: PremiumPurchase) -> PremiumPurchase:
        async with self._session_factory() as session:
            model = self._to_model(purchase)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return purchase

    async def get_user_purchases(self, user_id: UUID) -> List[PremiumPurchase]:
        async with self._session_factory() as session:
            stmt = select(PurchaseModel).where(PurchaseModel.user_id == user_id)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]

    async def has_purchased(self, user_id: UUID, document_id: UUID) -> bool:
        async with self._session_factory() as session:
            stmt = select(PurchaseModel).where(
                PurchaseModel.user_id == user_id,
                PurchaseModel.document_id == document_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None


class PyPDFWatermarkEngine(WatermarkEnginePort):
    """Implémentation du filigrane dynamique avec pypdf et reportlab."""

    async def apply_dynamic_watermark(self, pdf_bytes: bytes, metadata: WatermarkMetadata) -> bytes:
        """
        Applique un filigrane diagonal semi-transparent sur chaque page du PDF.
        Le texte contient le matricule, l'ID utilisateur, la date et une mention légale.
        """
        # Lire le PDF source
        reader = PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(reader.pages)

        # Créer un PDF overlay avec reportlab
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)

        # Couleur rouge semi-transparent
        red_color = Color(1, 0, 0, alpha=0.3)  # Rouge avec opacité 30%

        # Texte du filigrane
        watermark_text = (
            f"Propriété exclusive de {metadata.matricule} - Ne pas diffuser\n"
            f"Utilisateur: {metadata.user_id} - Date: {metadata.timestamp.isoformat()}\n"
            f"IP: {metadata.ip_address}"
        )

        # Pour chaque page du PDF original, on dessine le filigrane en diagonale
        for page_num in range(num_pages):
            c.setFillColor(red_color)
            c.setFont("Helvetica", 14)
            # Rotation pour effet diagonal
            c.saveState()
            c.translate(300, 400)  # Position centrale approximative
            c.rotate(45)
            # Dessiner le texte centré
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
            c.showPage()  # Passer à la page suivante de l'overlay

        c.save()
        overlay_buffer.seek(0)

        # Fusionner l'overlay avec le PDF source
        overlay_reader = PdfReader(overlay_buffer)
        writer = PdfWriter()

        for i in range(num_pages):
            page = reader.pages[i]
            overlay_page = overlay_reader.pages[i]
            page.merge_page(overlay_page)
            writer.add_page(page)

        # Écrire le PDF résultant dans un buffer
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.getvalue()