# backend/src/shared_kernel/infrastructure/blob_storage.py

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger("pineapple.blob_storage")


class AzureBlobStorageProvider:
    """
    Implémentation officielle du stockage d'objets sur Microsoft Azure Blob Storage.
    Gère les 4 conteneurs dédiés de Pineapple OS :
    - academy-documents : Fichiers académiques et corrigés
    - certification-documents : Justificatifs de certification d'identité
    - tenant-exports : Archives ZIP d'export de données souveraines par établissement
    - org-logos : Logos d'organisations et photos de profil
    """

    CONTAINER_ACADEMY = "academy-documents"
    CONTAINER_CERTIFICATION = "certification-documents"
    CONTAINER_EXPORTS = "tenant-exports"
    CONTAINER_LOGOS = "org-logos"

    def __init__(self, connection_string: Optional[str] = None, account_name: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = account_name or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self._blob_service_client = None

    def _get_client(self):
        if self._blob_service_client:
            return self._blob_service_client

        if not self.connection_string and not self.account_name:
            logger.debug("Azure Blob Storage non configuré (AZURE_STORAGE_CONNECTION_STRING absent). Fallback mémoire/dummy active.")
            return None

        try:
            from azure.storage.blob import BlobServiceClient
            if self.connection_string:
                self._blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            else:
                from azure.identity import DefaultAzureCredential
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self._blob_service_client = BlobServiceClient(account_url, credential=DefaultAzureCredential())
            return self._blob_service_client
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le client Azure Blob Storage : {e}")
            return None

    def upload_file(
        self,
        file_bytes: bytes,
        blob_name: str,
        container_name: str = CONTAINER_ACADEMY,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Téléverse un fichier binaire vers le conteneur Azure Blob Storage spécifié.
        Retourne la clé unique/URL du blob.
        """
        client = self._get_client()
        if not client:
            return f"local_mock_{blob_name}"

        try:
            from azure.storage.blob import ContentSettings
            container_client = client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container(public_access=None)  # Privé par défaut

            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                file_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
            logger.info(f"Fichier téléversé avec succès sur Azure Blob Storage [{container_name}/{blob_name}]")
            return f"{container_name}/{blob_name}"
        except Exception as e:
            logger.error(f"Erreur lors du téléversement vers Azure Blob Storage : {e}")
            raise

    async def generate_presigned_url(
        self,
        blob_path: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """
        Génère une URL signée SAS (Shared Access Signature) temporaire pour l'accès sécurisé à un blob privé.
        """
        client = self._get_client()
        if not client or not self.connection_string:
            return f"https://storage.pineapple.cm/{blob_path}?mock_token=signed"

        try:
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            parts = blob_path.split("/", 1)
            container_name = parts[0] if len(parts) > 1 else self.CONTAINER_ACADEMY
            blob_name = parts[1] if len(parts) > 1 else parts[0]

            account_key = client.credential.account_key if hasattr(client.credential, "account_key") else None
            if not account_key:
                return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}"

            sas_token = generate_blob_sas(
                account_name=client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds),
            )

            return f"https://{client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        except Exception as e:
            logger.warning(f"Erreur génération URL SAS Azure Blob : {e}")
            return f"https://storage.pineapple.cm/{blob_path}"


azure_blob_storage = AzureBlobStorageProvider()
