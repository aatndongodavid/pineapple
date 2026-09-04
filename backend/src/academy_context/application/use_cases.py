from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from academy_context.application.dtos import (
    DocumentUploadDTO,
    PurchaseRequestDTO,
    ReaderAccessDTO,
)
from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.ports import (
    FileStoragePort,
    LibraryRepositoryPort,
    PurchaseRepositoryPort,
    WatermarkEnginePort,
)
from academy_context.domain.value_objects import (
    AccessStatus,
    DocumentType,
    WatermarkMetadata,
)
from shared_kernel.domain.value_objects import Money


class DocumentNotFoundError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class PaymentError(Exception):
    pass


class UploadLibraryDocumentUseCase:
    """Use case pour l'upload d'un document dans la bibliothèque."""

    def __init__(self, library_repo: LibraryRepositoryPort, file_storage: FileStoragePort):
        self._library_repo = library_repo
        self._file_storage = file_storage

    def execute(
        self,
        tenant_id: UUID,
        uploader_id: UUID,
        dto: DocumentUploadDTO,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str,
    ) -> LibraryDocument:
        # Upload du fichier et récupération de la clé S3
        s3_key = self._file_storage.upload_file(file_bytes, original_filename, mime_type)

        # Création de l'entité LibraryDocument
        doc = LibraryDocument(
            id=uuid4(),
            tenant_id=tenant_id,
            title=dto.title,
            document_type=dto.document_type,
            s3_key=s3_key,
            is_premium=dto.is_premium,
            price=Money(amount=Decimal(dto.price_fcfa), currency="XAF"),
            faculty=dto.faculty,
            filiere=dto.filiere,
            academic_level=dto.academic_level,
            downloads_count=0,
            created_at=datetime.utcnow(),
        )

        return self._library_repo.save_document(doc)


class PurchasePremiumDocumentUseCase:
    """Use case pour l'achat d'un document premium."""

    def __init__(
        self,
        library_repo: LibraryRepositoryPort,
        purchase_repo: PurchaseRepositoryPort,
    ):
        self._library_repo = library_repo
        self._purchase_repo = purchase_repo

    def execute(
        self,
        user_id: UUID,
        tenant_id: UUID,
        dto: PurchaseRequestDTO,
        payment_processor=None,  # dépendance optionnelle pour simuler le paiement
    ) -> PremiumPurchase:
        doc = self._library_repo.get_document_by_id(dto.document_id, tenant_id)
        if not doc:
            raise DocumentNotFoundError("Document not found")

        if not doc.is_premium:
            # Le document est gratuit, pas besoin d'achat
            raise PaymentError("Document is not premium")

        if self._purchase_repo.has_purchased(user_id, dto.document_id):
            raise PaymentError("User already purchased this document")

        # Simuler ou traiter le paiement (méthode de paiement fournie dans le DTO)
        # Ici on considère que le paiement est réussi.
        # Dans une vraie implémentation, on appellerait un service de paiement.

        purchase = PremiumPurchase(
            id=uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            document_id=doc.id,
            price_paid=doc.price,
            purchased_at=datetime.utcnow(),
            is_active=True,
        )

        return self._purchase_repo.save_purchase(purchase)


class StreamToPineappleReaderUseCase:
    """Use case pour le streaming sécurisé d'un document avec filigrane dynamique."""

    def __init__(
        self,
        library_repo: LibraryRepositoryPort,
        purchase_repo: PurchaseRepositoryPort,
        file_storage: FileStoragePort,
        watermark_engine: WatermarkEnginePort,
    ):
        self._library_repo = library_repo
        self._purchase_repo = purchase_repo
        self._file_storage = file_storage
        self._watermark_engine = watermark_engine

    def execute(
        self,
        user_id: UUID,
        tenant_id: UUID,
        document_id: UUID,
        user_matricule: str,
        user_ip: str,
    ) -> bytes:
        doc = self._library_repo.get_document_by_id(document_id, tenant_id)
        if not doc:
            raise DocumentNotFoundError("Document not found")

        # Vérification de l'accès
        if doc.is_premium:
            has_purchase = self._purchase_repo.has_purchased(user_id, document_id)
            if not has_purchase:
                raise AccessDeniedError("User has not purchased this premium document")

        # Récupération des bytes du document depuis le stockage
        file_bytes = self._file_storage.get_file_bytes(doc.s3_key)

        # Construction des métadonnées du filigrane
        watermark_meta = WatermarkMetadata(
            matricule=user_matricule,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            ip_address=user_ip,
        )

        # Application du filigrane dynamique
        watermarked_pdf = self._watermark_engine.apply_dynamic_watermark(
            file_bytes, watermark_meta
        )

        return watermarked_pdf