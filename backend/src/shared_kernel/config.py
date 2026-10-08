import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisée de Pineapple 3.0 chargée depuis les variables d'environnement ou .env."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Pineapple OS"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # --- Infrastructure ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Sécurité / Authentification ---
    JWT_SECRET_KEY: str = "pineapple_super_secret_jwt_key_3_0_development"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Sécurité électorale ---
    ELECTION_PEPPER_SECRET: str = "pineapple_election_pepper_secret_dev"

    # --- Stockage objet ---
    AWS_S3_BUCKET_NAME: str = "pineapple-dev-bucket"

    def validate_production_security(self) -> None:
        """
        Vérifie qu'en environnement de production, aucune configuration non sécurisée ou clé de dev n'est utilisée (Gate O-10).
        L'application refuse catégoriquement de démarrer si une faille ou configuration non sécurisée est détectée.
        """
        if self.ENVIRONMENT.lower() in ("production", "prod"):
            # 1. DEBUG doit obligatoirement être False
            if self.DEBUG:
                raise RuntimeError("PROD_DEBUG_ACTIVE: DEBUG=true est interdit en environnement de production.")

            # 2. Clé secrète JWT sécurisée (>= 32 caractères, sans mot-clé dev)
            jwt_lower = self.JWT_SECRET_KEY.lower()
            if any(bad in jwt_lower for bad in ["dev", "secret", "change_me", "pineapple"]) or len(self.JWT_SECRET_KEY) < 32:
                raise RuntimeError("PROD_SECRET_KEY_INVALID: Clé JWT secrète non sécurisée ou utilisant un défaut de dev en production.")

            # 3. Secret d'élection sécurisé (>= 16 caractères, sans mot-clé dev)
            pepper_lower = self.ELECTION_PEPPER_SECRET.lower()
            if any(bad in pepper_lower for bad in ["dev", "secret", "change_me"]) or len(self.ELECTION_PEPPER_SECRET) < 16:
                raise RuntimeError("PROD_PEPPER_SECRET_INVALID: Secret d'élection non sécurisé ou de développement en production.")

            # 4. URL de base de données de production (pas de SQLite, ni mot de passe dev par défaut)
            db_lower = self.DATABASE_URL.lower()
            if "sqlite" in db_lower or "pineapple_dev_password" in db_lower:
                raise RuntimeError("PROD_DATABASE_URL_INVALID: URL de base de données non sécurisée ou utilisant un mot de passe dev par défaut en production.")


settings = Settings()