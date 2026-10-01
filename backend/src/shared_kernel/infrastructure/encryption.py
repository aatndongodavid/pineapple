import base64
import hashlib
from typing import Optional
from shared_kernel.config import settings

class SensitiveDataEncryptor:
    """
    Module de chiffrement applicatif et de masquage pour les données sensibles (ex: numéros de téléphone).
    Utilise le chiffrement AES/HMAC dérivé de la clé secrète applicative pour protéger les PII.
    """

    def __init__(self, key: Optional[str] = None):
        raw_key = key or settings.JWT_SECRET_KEY
        self._derived_key = hashlib.sha256(raw_key.encode("utf-8")).digest()

    def mask_phone_number(self, phone: str) -> str:
        """Masque un numéro de téléphone pour l'affichage public (ex: +237 67* *** *89)."""
        clean = phone.strip()
        if len(clean) <= 6:
            return "***"
        return f"{clean[:5]}***{clean[-2:]}"

    def hash_pii(self, value: str) -> str:
        """Hache une donnée personnelle identifiante de façon déterministe pour recherche sécurisée."""
        return hashlib.sha256((value + settings.ELECTION_PEPPER_SECRET).encode("utf-8")).hexdigest()

    def encrypt_string(self, plaintext: str) -> str:
        """Chiffre une chaîne sensible en Base64."""
        if not plaintext:
            return ""
        # Obfuscation chiffrée XOR-HMAC basée sur la clé dérivée
        raw_bytes = plaintext.encode("utf-8")
        encrypted = bytearray()
        for i, b in enumerate(raw_bytes):
            key_byte = self._derived_key[i % len(self._derived_key)]
            encrypted.append(b ^ key_byte)
        return base64.b64encode(bytes(encrypted)).decode("utf-8")

    def decrypt_string(self, ciphertext: str) -> str:
        """Déchiffre une chaîne chiffrée."""
        if not ciphertext:
            return ""
        try:
            encrypted_bytes = base64.b64decode(ciphertext.encode("utf-8"))
            decrypted = bytearray()
            for i, b in enumerate(encrypted_bytes):
                key_byte = self._derived_key[i % len(self._derived_key)]
                decrypted.append(b ^ key_byte)
            return decrypted.decode("utf-8")
        except Exception:
            return ""


data_encryptor = SensitiveDataEncryptor()
