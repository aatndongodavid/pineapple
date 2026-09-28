import uuid
from typing import Any, Callable, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from shared_kernel.config import settings

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Dépendance centralisée de décodage JWT.
    Vérifie la signature et retourne le payload utilisateur typé avec son rôle et tenant_id.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str: Optional[str] = payload.get("sub")
        tenant_id_str: Optional[str] = payload.get("tenant_id")
        role: str = payload.get("role", "STUDENT")
        scope: Optional[str] = payload.get("scope")

        if not user_id_str or not tenant_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification invalide (champs requis manquants)",
            )

        return {
            "user_id": uuid.UUID(user_id_str),
            "tenant_id": uuid.UUID(tenant_id_str),
            "role": role,
            "scope": scope,
            "raw_payload": payload,
        }
    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )


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
    Le token doit avoir scope="platform".
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
        return {
            "admin_id": uuid.UUID(payload["sub"]),
            "email": payload.get("email"),
            "scope": "platform",
            "raw_payload": payload,
        }
    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token platform admin invalide ou expiré",
        )
