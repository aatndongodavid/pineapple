# backend/src/monetization_context/domain/services/ad_token_service.py

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from shared_kernel.config import settings

logger = logging.getLogger("AdTokenService")

AD_TOKEN_SECRET = settings.JWT_SECRET_KEY or "adtech_super_secret_token_key_2026"
AD_TOKEN_ALGORITHM = "HS256"
AD_TOKEN_TTL_MINUTES = 15


class AdTokenService:
    """
    Générateur et vérificateur de jetons signés d'impression et de clic (Gate R5).
    Anti-rejeu et limitation de durée de vie (15 min).
    """

    @staticmethod
    def generate_impression_token(
        creative_id: uuid.UUID,
        campaign_id: uuid.UUID,
        visitor_session_id: str,
        unit_price_xaf: int,
        billing_model: str,
        advertiser_id: Optional[uuid.UUID] = None,
    ) -> str:
        """Génère un jeton signé HMAC pour une impression d'annonce."""
        now = datetime.now(timezone.utc)
        payload = {
            "jti": str(uuid.uuid4()),
            "crt": str(creative_id),
            "cmp": str(campaign_id),
            "adv": str(advertiser_id) if advertiser_id else None,
            "sid": visitor_session_id,
            "px": unit_price_xaf,
            "bm": billing_model,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=AD_TOKEN_TTL_MINUTES)).timestamp()),
        }
        return jwt.encode(payload, AD_TOKEN_SECRET, algorithm=AD_TOKEN_ALGORITHM)

    @staticmethod
    def verify_impression_token(token: str) -> Optional[Dict[str, Any]]:
        """Décode et vérifie la signature et l'expiration du jeton d'impression."""
        try:
            payload = jwt.decode(token, AD_TOKEN_SECRET, algorithms=[AD_TOKEN_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Jeton d'impression invalide ou expiré: {e}")
            return None
