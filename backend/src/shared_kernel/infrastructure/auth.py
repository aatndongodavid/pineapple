import uuid
from typing import Any, Callable, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from shared_kernel.config import settings

from shared_kernel.infrastructure.token_blacklist import token_blacklist
from shared_kernel.infrastructure.security_logger import security_logger

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Dépendance centralisée de décodage JWT.
    Vérifie la signature (avec support de rotation de clé), la validité temporelle,
    et la liste noire de révocation des tokens.
    """
    if not credentials:
        security_logger.log_failed_login(email="anonymous", reason="Missing bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = None

    # Tente de décoder avec la clé principale, puis la clé précédente (rotation)
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        if settings.JWT_SECRET_KEY_PREVIOUS:
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY_PREVIOUS,
                    algorithms=[settings.JWT_ALGORITHM],
                )
            except JWTError:
                pass

    if not payload:
        security_logger.log_failed_login(email="unknown", reason="Invalid JWT signature or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )

    user_id_str: Optional[str] = payload.get("sub")
    tenant_id_str: Optional[str] = payload.get("tenant_id")
    role: str = payload.get("role", "STUDENT")
    scope: Optional[str] = payload.get("scope")
    token_jti: Optional[str] = payload.get("jti", token[:16])
    token_iat: Optional[float] = payload.get("iat")

    if not user_id_str or not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification invalide (champs requis manquants)",
        )

    # Vérification de révocation explicite
    is_revoked = await token_blacklist.is_token_revoked(
        token_jti=token_jti,
        user_id=user_id_str,
        token_issued_at=token_iat,
    )
    if is_revoked:
        security_logger.log_token_revoked(token_jti=token_jti, user_id=user_id_str, reason="Attempted use of revoked token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ce token ou cette session a été révoqué(e). Veuillez vous re-connecter.",
        )

    return {
        "user_id": uuid.UUID(user_id_str),
        "tenant_id": uuid.UUID(tenant_id_str),
        "role": role,
        "scope": scope,
        "jti": token_jti,
        "raw_payload": payload,
    }


def require_role(*allowed_roles: str) -> Callable:
    """
    Factory de dépendance RBAC multi-tenant.
    Vérifie que le rôle de l'utilisateur courant fait partie des rôles autorisés.
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "STUDENT")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle insuffisant pour cette action. Rôles autorisés: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


async def require_platform_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Dépendance de sécurité pour le rôle Super Administrateur de la plateforme (Gemula).
    Le token doit avoir scope="platform" et ne doit pas être révoqué.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification platform admin manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("scope") != "platform":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès réservé aux super-administrateurs de la plateforme",
            )
        token_jti = payload.get("jti", token[:16])
        user_id_str = payload.get("sub")
        token_iat = payload.get("iat")

        is_revoked = await token_blacklist.is_token_revoked(
            token_jti=token_jti,
            user_id=user_id_str,
            token_issued_at=token_iat,
        )
        if is_revoked:
            security_logger.log_token_revoked(token_jti=token_jti, user_id=user_id_str, reason="Attempted use of revoked platform admin token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ce token ou cette session super-admin a été révoqué(e).",
            )

        return {
            "admin_id": uuid.UUID(payload["sub"]),
            "email": payload.get("email"),
            "scope": "platform",
            "jti": token_jti,
            "raw_payload": payload,
        }
    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token platform admin invalide ou expiré",
        )
