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


settings = Settings()