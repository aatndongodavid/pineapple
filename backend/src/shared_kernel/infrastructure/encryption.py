import base64
import hashlib
import re
import unicodedata
from typing import Optional

from shared_kernel.config import settings


def _get_derived_key() -> bytes:
    """Dérive une clé de 32 octets à partir de JWT_SECRET_KEY."""
    secret = settings.JWT_SECRET_KEY.encode('utf-8')
    return hashlib.sha256(secret).digest()


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """Chiffre une chaîne de caractères au repos (Fernet / AES simulation déterministe/réversible)."""
    if plaintext is None:
        return None
    key = _get_derived_key()
    data_bytes = plaintext.encode('utf-8')
    # XOR stream cipher avec clé SHA256 pour chiffrement léger et réversible sans dépendance externe lourde
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data_bytes))
    return "ENC:" + base64.b64encode(encrypted).decode('utf-8')


def decrypt_field(ciphertext: Optional[str]) -> Optional[str]:
    """Déchiffre une chaîne de caractères chiffrée par encrypt_field."""
    if ciphertext is None:
        return None
    if not ciphertext.startswith("ENC:"):
        return ciphertext  # Valeur non chiffrée (ex: données existantes)
    raw_b64 = ciphertext[4:]
    try:
        encrypted = base64.b64decode(raw_b64.encode('utf-8'))
        key = _get_derived_key()
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
        return decrypted.decode('utf-8')
    except Exception:
        return ciphertext


def normalize_text(text: Optional[str]) -> str:
    """Normalise un texte pour comparaison : minuscules, sans diacritiques/accents, espaces réduits, trim."""
    if not text:
        return ""
    # NFD decomposition pour séparer les accents
    nfd = unicodedata.normalize('NFD', text)
    without_accents = "".join(c for c in nfd if unicodedata.category(c) != 'Mn')
    lowered = without_accents.lower()
    # Remplacer tirets et espaces multiples par un seul espace
    cleaned = re.sub(r'[\s\-]+', ' ', lowered)
    return cleaned.strip()


def normalize_matricule(matricule: Optional[str]) -> str:
    """Normalise un matricule : majuscules, suppression de tous les espaces et tirets."""
    if not matricule:
        return ""
    cleaned = re.sub(r'[\s\-]+', '', matricule.upper())
    return cleaned.strip()


def sanitize_csv_cell(val: Optional[str]) -> str:
    """Neutralise les injections de formules CSV (OWASP CSV Injection)."""
    if not val:
        return ""
    stripped = val.strip()
    if stripped.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + stripped
    return stripped

