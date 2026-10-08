# tests/unit/test_production_security_guardrails.py

import pytest
from shared_kernel.config import Settings


def test_gate_o10_development_environment_allows_defaults():
    """
    Gate O-10: En mode développement, les configurations par défaut sont acceptées.
    """
    s = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        JWT_SECRET_KEY="pineapple_super_secret_jwt_key_3_0_development",
        ELECTION_PEPPER_SECRET="pineapple_election_pepper_secret_dev",
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
    )
    # Ne doit lever aucune exception
    s.validate_production_security()


def test_gate_o10_production_blocks_debug_mode():
    """
    Gate O-10: En mode production, DEBUG=true provoque une erreur de démarrage.
    """
    s = Settings(
        ENVIRONMENT="production",
        DEBUG=True,
        JWT_SECRET_KEY="x9fK2mP7qR4vW1zN8bL3jH6tC5yU0iO2_production_token_valide",
        ELECTION_PEPPER_SECRET="valid_pepper_key_16chars",
        DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/prod_db",
    )
    with pytest.raises(RuntimeError, match="PROD_DEBUG_ACTIVE"):
        s.validate_production_security()


def test_gate_o10_production_blocks_unsafe_jwt_secret():
    """
    Gate O-10: En mode production, un secret JWT de dev provoque une erreur de démarrage.
    """
    s = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET_KEY="pineapple_super_secret_jwt_key_3_0_development",
        ELECTION_PEPPER_SECRET="valid_pepper_key_16chars",
        DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/prod_db",
    )
    with pytest.raises(RuntimeError, match="PROD_SECRET_KEY_INVALID"):
        s.validate_production_security()


def test_gate_o10_production_blocks_default_database_password():
    """
    Gate O-10: En mode production, un mot de passe DB dev par défaut provoque une erreur de démarrage.
    """
    s = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET_KEY="x9fK2mP7qR4vW1zN8bL3jH6tC5yU0iO2_production_token_valide",
        ELECTION_PEPPER_SECRET="valid_pepper_key_16chars",
        DATABASE_URL="postgresql+asyncpg://pineapple:pineapple_dev_password@db:5432/pineapple",
    )
    with pytest.raises(RuntimeError, match="PROD_DATABASE_URL_INVALID"):
        s.validate_production_security()


def test_gate_o10_production_passes_with_valid_secure_config():
    """
    Gate O-10: En mode production avec des identifiants valides et chiffrés, le démarrage réussit.
    """
    s = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET_KEY="x9fK2mP7qR4vW1zN8bL3jH6tC5yU0iO2_production_secure_token",
        ELECTION_PEPPER_SECRET="secure_pepper_prod_16ch",
        DATABASE_URL="postgresql+asyncpg://prod_user:StrongPass987654321@db:5432/pineapple_prod",
    )
    s.validate_production_security()
