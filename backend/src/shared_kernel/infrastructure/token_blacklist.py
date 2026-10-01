import time
from typing import Set, Dict, Optional
from shared_kernel.infrastructure.redis_cache import CacheService

class TokenBlacklist:
    """
    Magasin centralisé de révocation immédiate des tokens JWT.
    Stocke les tokens/jti révoqués en mémoire locale et synchronise avec Redis.
    Permet la déconnexion instantanée, la révocation de session et l'invalidation suite à un bannissement.
    """

    def __init__(self):
        self._local_blacklist: Set[str] = set()
        self._user_revocation_timestamps: Dict[str, float] = {}

    async def revoke_token(self, token_jti: str, ttl_seconds: int = 86400) -> None:
        """Ajoute un jti de token à la liste noire."""
        self._local_blacklist.add(token_jti)
        try:
            await CacheService.set_json(f"blacklist:token:{token_jti}", "revoked", ttl_seconds)
        except Exception:
            pass

    async def is_token_revoked(self, token_jti: str, user_id: Optional[str] = None, token_issued_at: Optional[float] = None) -> bool:
        """Vérifie si le token a été individuellement révoqué ou émis avant la déconnexion globale de l'utilisateur."""
        if token_jti in self._local_blacklist:
            return True

        if user_id and user_id in self._user_revocation_timestamps:
            revocation_time = self._user_revocation_timestamps[user_id]
            if token_issued_at and token_issued_at < revocation_time:
                return True

        try:
            val = await CacheService.get_json(f"blacklist:token:{token_jti}")
            if val == "revoked":
                self._local_blacklist.add(token_jti)
                return True

            if user_id:
                user_rev_time = await CacheService.get_json(f"blacklist:user:{user_id}")
                if user_rev_time and token_issued_at and token_issued_at < float(user_rev_time):
                    return True
        except Exception:
            pass

        return False

    async def revoke_all_user_sessions(self, user_id: str) -> None:
        """Invalide immédiatement toutes les sessions actives d'un utilisateur (bannissement, reset mdp)."""
        now = time.time()
        self._user_revocation_timestamps[user_id] = now
        try:
            await CacheService.set_json(f"blacklist:user:{user_id}", str(now), 7 * 86400)
        except Exception:
            pass


token_blacklist = TokenBlacklist()
