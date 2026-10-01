# backend/src/trust_safety_context/domain/content_moderation.py

import re
from typing import Optional, Tuple
from shared_kernel.infrastructure.image_security import sanitize_and_process_image, UnsafeImageError

BANNED_KEYWORDS = [
    "haine",
    "violence",
    "insulte",
    "arnaque",
    "fraude",
    "piratage",
    "drogue",
    "arme",
    "terrorisme",
]

BANNED_PATTERNS = [
    re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE) for word in BANNED_KEYWORDS
]


class ContentModerationService:
    """
    Service de modération préventive de premier niveau pour le contenu textuel et multimédia.
    
    Avertissement sur les limites (Documenté explicitement) :
    Ce filtrage basé sur des mots-clés et règles heuristiques constitue un premier niveau
    imparfait (risques de faux positifs et faux négatifs). Il complète le signalement humain
    a posteriori sans remplacer une solution complète de modération par IA/ML.
    """

    @staticmethod
    def inspect_text(text: str) -> Tuple[bool, Optional[str]]:
        """
        Analyse un texte public (post, commentaire, annonce).
        Retourne (is_flagged, matched_reason).
        Si is_flagged est True, le contenu passe en statut PENDING_REVIEW au lieu d'être publié.
        """
        if not text:
            return False, None

        for pattern in BANNED_PATTERNS:
            match = pattern.search(text)
            if match:
                return True, f"Détection préventive de terme sensible : '{match.group(0)}'"

        return False, None

    @staticmethod
    def inspect_image(image_bytes: bytes, max_size_bytes: int = 5 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
        """
        Analyse une image uploadée en réutilisant le module de sécurité Pillow.
        Vérifie la structure, l'en-tête et l'intégrité de l'image.
        
        Note sur le risque résiduel :
        L'analyse structurelle valide l'intégrité du fichier mais ne détecte pas le contenu visuel
        inapproprié complexe en l'absence d'un modèle d'IA de vision externe.
        """
        if not image_bytes:
            return False, None

        if len(image_bytes) > max_size_bytes:
            return True, "L'image dépasse la taille maximale autorisée de 5 Mo."

        try:
            sanitize_and_process_image(image_bytes)
            return False, None
        except UnsafeImageError as e:
            return True, str(e)
        except Exception as e:
            return True, f"Erreur de traitement d'image : {str(e)}"
