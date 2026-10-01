import base64
import hashlib
import hmac
import os
import struct
import time
from typing import Optional


def generate_totp_secret() -> str:
    """Génère une clé secrète TOTP encodée en Base32 (RFC 4648)."""
    random_bytes = os.urandom(20)
    return base64.b32encode(random_bytes).decode("utf-8").replace("=", "")


def get_totp_uri(secret: str, email: str, issuer: str = "Pineapple OS") -> str:
    """Génère l'URI otpauth:// pour la configuration des applications Authenticator."""
    clean_secret = secret.replace(" ", "").upper()
    return f"otpauth://totp/{issuer}:{email}?secret={clean_secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


def _generate_totp_code_for_counter(secret: str, counter: int) -> str:
    """Calcule le code à 6 chiffres TOTP pour une valeur de compteur donnée (RFC 6238)."""
    clean_secret = secret.replace(" ", "").upper()
    # Handle padding
    missing_padding = len(clean_secret) % 8
    if missing_padding:
        clean_secret += "=" * (8 - missing_padding)

    key = base64.b32decode(clean_secret, casefold=True)
    msg = struct.pack(">Q", counter)

    hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    code_int = (struct.unpack(">I", hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code_int:06d}"


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Vérifie la validité d'un code TOTP à 6 chiffres saisi par l'utilisateur.
    Autorise une fenêtre de tolérance temporelle de +/- valid_window pas de 30 secondes.
    """
    if not secret or not code or len(code.strip()) != 6 or not code.strip().isdigit():
        return False

    clean_code = code.strip()
    current_counter = int(time.time() // 30)

    for offset in range(-valid_window, valid_window + 1):
        target_counter = current_counter + offset
        if _generate_totp_code_for_counter(secret, target_counter) == clean_code:
            return True

    return False
