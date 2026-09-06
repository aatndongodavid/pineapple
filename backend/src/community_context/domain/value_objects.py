from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import UUID


class AudienceScope(str, Enum):
    """Portée de diffusion d'une publication."""
    LOCAL = "LOCAL"                # Établissement uniquement
    EXTENDED = "EXTENDED"          # Réseau Pineapple (multi-établissements)
    SPONSORED = "SPONSORED"        # Visibilité payante, toujours étiquetée
    PUBLIC = "PUBLIC"              # Réservé à certains contenus autorisés


class PostType(str, Enum):
    """Type de contenu d'une publication."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    EVENT = "EVENT"
    PROJECT = "PROJECT"


class OrganizationType(str, Enum):
    """Catégorie d'organisation."""
    CLUB = "CLUB"
    ASSOCIATION = "ASSOCIATION"
    MOVEMENT = "MOVEMENT"


class RoomStatus(str, Enum):
    """État d'une salle déclaré par un délégué."""
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    TO_CONFIRM = "TO_CONFIRM"


@dataclass(frozen=True)
class AudiencePolicy:
    """
    Politique d'audience d'une publication.
    Détermine qui peut voir le contenu en fonction de la portée et des tenants ciblés.
    """
    scope: AudienceScope
    target_tenant_ids: List[UUID] = field(default_factory=list)

    def can_be_viewed_by(self, user_tenant_id: UUID) -> bool:
        """
        Vérifie si un utilisateur appartenant à `user_tenant_id` peut voir la publication.

        Règles :
        - LOCAL : visible uniquement si le tenant correspond à l'établissement d'origine.
        - EXTENDED / SPONSORED : visible si le tenant fait partie des cibles explicites.
        - PUBLIC : visible par tous.
        """
        if self.scope == AudienceScope.PUBLIC:
            return True
        if self.scope == AudienceScope.LOCAL:
            # Le tenant d'origine n'est pas stocké ici ; on suppose que
            # le tenant cible est implicite et géré par le contexte d'appel.
            # Pour LOCAL, on considère que l'utilisateur est dans le même tenant
            # que la publication (à valider au niveau du service).
            # Ici, on ne peut pas connaître le tenant d'origine, donc on
            # délègue la logique au service qui possède l'info.
            # On pourrait ajouter un champ origin_tenant_id, mais pour l'instant
            # on laisse la méthode indéterminée pour LOCAL.
            # Pour éviter une erreur, on renvoie False par défaut.
            # Mieux : on suppose que target_tenant_ids contient le tenant d'origine
            # pour LOCAL aussi ? Mais l'énoncé ne le précise pas.
            # On interprète : pour LOCAL, on renvoie True si user_tenant_id est dans target_tenant_ids,
            # sinon False. L'appelant doit fournir la cible (l'établissement).
            return user_tenant_id in self.target_tenant_ids

        # EXTENDED ou SPONSORED : ciblage explicite
        return user_tenant_id in self.target_tenant_ids