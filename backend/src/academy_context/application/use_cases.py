import uuid
from datetime import datetime
from decimal import Decimal

from academy_context.application.dtos import DocumentUploadDTO, PurchaseRequestDTO
from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.value_objects import WatermarkMetadata
from shared_kernel.domain.value_objects import Money


class DocumentNotFoundError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class PaymentError(Exception):
    pass


class UploadLibraryDocumentUseCase:
    def __init__(self, library_repo, file_storage):
        self._library_repo = library_repo
        self._file_storage = file_storage

    async def execute(
        self,
        tenant_id: uuid.UUID,
        uploader_id: uuid.UUID,
        dto: DocumentUploadDTO,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str,
    ) -> LibraryDocument:
        file_key = await self._file_storage.upload_file(file_bytes, original_filename, mime_type)
        document = LibraryDocument(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            uploader_id=uploader_id,
            title=dto.title,
            document_type=dto.document_type,
            faculty=dto.faculty,
            filiere=dto.filiere,
            academic_level=dto.academic_level,
            file_key=file_key,
            is_premium=dto.is_premium,
            price=Money(Decimal(dto.price_fcfa)),
            created_at=datetime.utcnow(),
        )
        return await self._library_repo.save_document(document)


class PurchasePremiumDocumentUseCase:
    def __init__(self, library_repo, purchase_repo):
        self._library_repo = library_repo
        self._purchase_repo = purchase_repo

    async def execute(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, dto: PurchaseRequestDTO
    ) -> PremiumPurchase:
        document = await self._library_repo.get_document(dto.document_id, tenant_id)
        if document is None:
            raise DocumentNotFoundError()
        purchase = PremiumPurchase(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            document_id=document.id,
            amount=document.price,
            purchased_at=datetime.utcnow(),
        )
        return await self._purchase_repo.save_purchase(purchase)


class StreamToPineappleReaderUseCase:
    def __init__(self, library_repo, purchase_repo, file_storage, watermark_engine):
        self._library_repo = library_repo
        self._purchase_repo = purchase_repo
        self._file_storage = file_storage
        self._watermark_engine = watermark_engine

    async def execute(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
        user_matricule: str,
        user_ip: str,
    ) -> bytes:
        document = await self._library_repo.get_document(document_id, tenant_id)
        if document is None:
            raise DocumentNotFoundError()
        if document.is_premium and not await self._purchase_repo.has_purchase(user_id, document_id, tenant_id):
            raise AccessDeniedError()
        pdf_bytes = await self._file_storage.get_file_bytes(document.file_key)
        return await self._watermark_engine.apply_watermark(
            pdf_bytes,
            WatermarkMetadata(
                user_matricule=user_matricule,
                ip_address=user_ip,
                timestamp=datetime.utcnow().isoformat(),
            ),
        )
