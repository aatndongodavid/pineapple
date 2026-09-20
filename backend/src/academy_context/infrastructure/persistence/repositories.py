import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.value_objects import DocumentType, WatermarkMetadata
from academy_context.infrastructure.persistence.models import (
    LibraryDocumentModel,
    PremiumPurchaseModel,
)
from shared_kernel.domain.value_objects import Money


def _document_to_entity(model: LibraryDocumentModel) -> LibraryDocument:
    return LibraryDocument(
        id=model.id,
        tenant_id=model.tenant_id,
        uploader_id=model.uploader_id,
        title=model.title,
        document_type=model.document_type,
        faculty=model.faculty,
        filiere=model.filiere,
        academic_level=model.academic_level,
        file_key=model.file_key,
        is_premium=model.is_premium,
        price=Money(Decimal(model.price_fcfa)),
        created_at=model.created_at,
    )


class PostgresLibraryRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def list_documents(
        self,
        tenant_id: uuid.UUID,
        faculty: str | None = None,
        level: str | None = None,
        doc_type: DocumentType | None = None,
    ) -> list[LibraryDocument]:
        async with self._session_factory() as session:
            stmt = select(LibraryDocumentModel).where(LibraryDocumentModel.tenant_id == tenant_id)
            if faculty:
                stmt = stmt.where(LibraryDocumentModel.faculty == faculty)
            if level:
                stmt = stmt.where(LibraryDocumentModel.academic_level == level)
            if doc_type:
                stmt = stmt.where(LibraryDocumentModel.document_type == doc_type)
            result = await session.execute(stmt)
            return [_document_to_entity(model) for model in result.scalars().all()]

    async def get_document(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> LibraryDocument | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(LibraryDocumentModel).where(
                    LibraryDocumentModel.id == document_id,
                    LibraryDocumentModel.tenant_id == tenant_id,
                )
            )
            model = result.scalar_one_or_none()
            return _document_to_entity(model) if model else None

    async def save_document(self, document: LibraryDocument) -> LibraryDocument:
        model = LibraryDocumentModel(
            id=document.id,
            tenant_id=document.tenant_id,
            uploader_id=document.uploader_id,
            title=document.title,
            document_type=document.document_type,
            faculty=document.faculty,
            filiere=document.filiere,
            academic_level=document.academic_level,
            file_key=document.file_key,
            is_premium=document.is_premium,
            price_fcfa=int(document.price.amount),
            created_at=document.created_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return document


class PostgresPurchaseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def save_purchase(self, purchase: PremiumPurchase) -> PremiumPurchase:
        model = PremiumPurchaseModel(
            id=purchase.id,
            tenant_id=purchase.tenant_id,
            user_id=purchase.user_id,
            document_id=purchase.document_id,
            amount_fcfa=int(purchase.amount.amount),
            purchased_at=purchase.purchased_at,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return purchase

    async def has_purchase(
        self, user_id: uuid.UUID, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PremiumPurchaseModel).where(
                    PremiumPurchaseModel.user_id == user_id,
                    PremiumPurchaseModel.document_id == document_id,
                    PremiumPurchaseModel.tenant_id == tenant_id,
                )
            )
            return result.scalar_one_or_none() is not None


class PyPDFWatermarkEngine:
    async def apply_watermark(self, pdf_bytes: bytes, metadata: WatermarkMetadata) -> bytes:
        return pdf_bytes
