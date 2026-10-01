# backend/src/shared_kernel/infrastructure/secrets_manager.py

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("pineapple.secrets_manager")


class SecretsManager:
    """
    Gestionnaire centralisé des secrets Pineapple (Microsoft Azure Key Vault).
    Tente de récupérer les secrets depuis Azure Key Vault si AZURE_KEY_VAULT_URL est configuré,
    ou bascule sur les variables d'environnement / .env en environnement local.
    """

    def __init__(self):
        self._cached_secrets: Dict[str, Any] = {}
        self._loaded_azure = False

    def load_azure_secrets(self) -> Dict[str, Any]:
        """Tente de charger les secrets depuis Azure Key Vault via DefaultAzureCredential."""
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")

        if not vault_url or self._loaded_azure:
            return self._cached_secrets

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            # Charger les propriétés des secrets du vault
            for secret_properties in client.list_properties_of_secrets():
                secret_name = secret_properties.name
                secret = client.get_secret(secret_name)
                env_key = secret_name.replace("-", "_").upper()
                self._cached_secrets[env_key] = secret.value
                self._cached_secrets[secret_name] = secret.value

            self._loaded_azure = True
            logger.info("Secrets Azure Key Vault chargés avec succès.")
        except Exception as e:
            # Fallback silencieux vers les variables d'environnement locales
            logger.debug(f"Azure Key Vault non joignable ({e}). Fallback vers variables d'environnement locales.")
            pass

        return self._cached_secrets

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Récupère une valeur de secret par sa clé avec chaîne de fallback."""
        if not self._loaded_azure:
            self.load_azure_secrets()

        if key in self._cached_secrets:
            return str(self._cached_secrets[key])

        return os.getenv(key, default)


secrets_manager = SecretsManager()
