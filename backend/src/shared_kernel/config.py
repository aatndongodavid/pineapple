from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisée de Pineapple 3.0 chargée depuis les variables d'environnement ou .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Pineapple OS"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # --- Infrastructure ---
    DATABASE_URL: str
    REDIS_URL: str

    # --- Sécurité / Authentification ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Sécurité électorale ---
    ELECTION_PEPPER_SECRET: str

    # --- Stockage objet ---
    AWS_S3_BUCKET_NAME: str


settings = Settings()