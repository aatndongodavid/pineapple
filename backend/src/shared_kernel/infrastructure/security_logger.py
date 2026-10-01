import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class SecurityLogger:
    """
    Journalisateur de sécurité dédié.
    Isole les événements de sécurité (échecs de connexion, refus 403, rate limiting, révocations)
    dans un journal distinct avec alertes de sécurité séparées du bruit applicatif.
    """

    def __init__(self, log_file: str = "logs/security.log"):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logger = logging.getLogger("pineapple.security")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding="utf-8")
            formatter = logging.logging.Formatter(
                "[%(asctime)s] [SECURITY] [%(levelname)s] %(message)s"
            ) if hasattr(logging, "logging") else logging.Formatter(
                "[%(asctime)s] [SECURITY] [%(levelname)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_failed_login(self, email: str, ip_address: Optional[str] = None, reason: str = "Invalid credentials") -> None:
        """Enregistre une tentative de connexion échouée."""
        self.logger.warning(
            f"EVENT=LOGIN_FAILED email={email} ip={ip_address or 'unknown'} reason='{reason}' timestamp={datetime.now(timezone.utc).isoformat()}"
        )

    def log_access_denied(self, user_id: str, role: str, resource: str, ip_address: Optional[str] = None) -> None:
        """Enregistre un refus d'autorisation (403 Forbidden)."""
        self.logger.warning(
            f"EVENT=ACCESS_DENIED user_id={user_id} role={role} resource='{resource}' ip={ip_address or 'unknown'} timestamp={datetime.now(timezone.utc).isoformat()}"
        )

    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str) -> None:
        """Enregistre un dépassement de quota (429 Rate Limit)."""
        self.logger.warning(
            f"EVENT=RATE_LIMIT_EXCEEDED ip={ip_address} endpoint='{endpoint}' timestamp={datetime.now(timezone.utc).isoformat()}"
        )

    def log_token_revoked(self, token_jti: str, user_id: str, reason: str) -> None:
        """Enregistre la révocation explicite d'un token ou d'une session."""
        self.logger.info(
            f"EVENT=TOKEN_REVOKED jti={token_jti} user_id={user_id} reason='{reason}' timestamp={datetime.now(timezone.utc).isoformat()}"
        )


security_logger = SecurityLogger()
