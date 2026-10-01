import os
import json
from typing import Optional, Dict, Any

class SecretsManager:
    """
    Gestionnaire centralisé des secrets Pineapple.
    Tente de récupérer les secrets depuis AWS Secrets Manager si disponible en production,
    ou bascule sur les variables d'environnement / .env en environnement local.
    """

    def __init__(self):
        self._cached_secrets: Dict[str, Any] = {}
        self._loaded_aws = False

    def load_aws_secrets(self) -> Dict[str, Any]:
        """Tente de charger les secrets depuis AWS Secrets Manager si AWS_SECRETS_NAME est configuré."""
        secret_name = os.getenv("AWS_SECRETS_NAME")
        region_name = os.getenv("AWS_REGION", "eu-west-3")

        if not secret_name or self._loaded_aws:
            return self._cached_secrets

        try:
            import boto3
            client = boto3.client("secretsmanager", region_name=region_name)
            response = client.get_secret_value(SecretId=secret_name)
            if "SecretString" in response:
                secrets_dict = json.loads(response["SecretString"])
                self._cached_secrets.update(secrets_dict)
                self._loaded_aws = True
        except Exception:
            # Fallback silencieux vers les variables d'environnement locales
            pass

        return self._cached_secrets

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Récupère une valeur de secret par sa clé avec chaîne de fallback."""
        if not self._loaded_aws:
            self.load_aws_secrets()

        if key in self._cached_secrets:
            return str(self._cached_secrets[key])

        return os.getenv(key, default)


secrets_manager = SecretsManager()
