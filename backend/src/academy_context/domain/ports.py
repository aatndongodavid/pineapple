import uuid
from abc import ABC, abstractmethod

from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.value_objects import DocumentType, WatermarkMetadata


class LibraryRepositoryPort(ABC):
    @abstractmethod
    async def list_documents(
        self,
        tenant_id: uuid.UUID,
        faculty: str | None = None,
        level: str | None = None,
        doc_type: DocumentType | None = None,
    ) -> list[LibraryDocument]:
        raise NotImplementedError

    @abstractmethod
    async def get_document(self, document_id: uuid.UUID, tenant_id: uuid.UUID) -> LibraryDocument | None:
        raise NotImplementedError

    @abstractmethod
    async def save_document(self, document: LibraryDocument) -> LibraryDocument:
        raise NotImplementedError


class PurchaseRepositoryPort(ABC):
    @abstractmethod
    async def save_purchase(self, purchase: PremiumPurchase) -> PremiumPurchase:
        raise NotImplementedError

    @abstractmethod
    async def has_purchase(self, user_id: uuid.UUID, document_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        raise NotImplementedError


class FileStoragePort(ABC):
    @abstractmethod
    async def upload_file(self, file_bytes: bytes, filename: str, mime_type: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_file_bytes(self, file_key: str) -> bytes:
        raise NotImplementedError


class WatermarkEnginePort(ABC):
    @abstractmethod
    async def apply_watermark(self, pdf_bytes: bytes, metadata: WatermarkMetadata) -> bytes:
        raise NotImplementedError
