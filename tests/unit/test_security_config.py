# tests/unit/test_security_config.py
import pytest
from shared_kernel.config import Settings

def test_sec_003_production_refuses_default_secret_key():
    """SEC-003: En production, la plateforme doit refuser de démarrer avec une clé secrète par défaut."""
    # Test setting validation function
    dev_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="pineapple_super_secret_jwt_key_3_0_development"
    )
    
    with pytest.raises(RuntimeError, match="PROD_SECRET_KEY_INVALID"):
        dev_settings.validate_production_security()
