# backend/src/monetization_context/domain/services/ad_policy_engine.py

import logging
import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse

logger = logging.getLogger("AdPolicyEngine")

DEFAULT_FORBIDDEN_KEYWORDS = [
    "cigarett", "tabac", "vape", "nicotine", "alcool", "biere", "whisky", "vodka",
    "poker", "casino", "parie", "betting", "1xbet", "pari foot",
    "sexe", "porno", "adult", "rencontre coquine",
    "arme", "pistolet", "fusil", "munition",
    "produit miracle", "guerison miracle", "perdre 10kg en 2 jours",
    "pret immediat", "enrichissement rapide", "pyramide", "crypto miracle",
    "diplome sans examen", "faux diplome", "usurpation",
]

ALLOWED_URL_SCHEMES = {"http", "https"}


class AdPolicyEngine:
    """
    Moteur de modération automatique des créations publicitaires.
    Vérifie les catégories interdites, les mots-clés bannis et la sécurité de l'URL cible.
    """

    def __init__(self, custom_keywords: Optional[List[str]] = None):
        self.forbidden_keywords = [k.lower() for k in (custom_keywords or DEFAULT_FORBIDDEN_KEYWORDS)]

    def validate_target_url(self, url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Vérifie la sécurité de l'URL de destination (Gate R6).
        Seuls les protocoles http:// et https:// sont autorisés.
        Rejette javascript:, data:, file:, etc.
        """
        if not url:
            return True, None

        url_str = url.strip()
        parsed = urlparse(url_str)
        scheme = parsed.scheme.lower()

        if scheme not in ALLOWED_URL_SCHEMES:
            return False, f"Protocole URL non autorisé ('{scheme}'). Seuls http et https sont acceptés."

        if not parsed.netloc:
            return False, "Nom d'hôte invalide dans l'URL de destination."

        return True, None

    def evaluate_content(self, headline: str, body_text: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie le titre et le texte contre la liste noire de mots-clés et catégories interdites (Gate R3).
        """
        full_text = f"{headline} {body_text}".lower()

        for kw in self.forbidden_keywords:
            if kw in full_text:
                logger.warning(f"Modération auto: mot-clé interdit décelé '{kw}'")
                return False, f"Contenu interdit détecté : mot-clé '{kw}' non conforme à la politique publicitaire."

        return True, None
