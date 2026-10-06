# backend/src/shared_kernel/infrastructure/file_security.py
import re
import os
from fastapi import HTTPException, status

def sanitize_filename(filename: str) -> str:
    """Nettoie le nom de fichier pour prévenir les attaques de traversée de chemin (Path Traversal)."""
    basename = os.path.basename(filename)
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', basename)
    return cleaned.lstrip('.') or "uploaded_file"

def validate_file_magic_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Vérifie les premiers octets (Magic Bytes) d'un fichier binaire téléversé.
    Retourne le type MIME réel validé ou lève une HTTPException(400) si invalide/dangereux.
    """
    if len(file_bytes) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE", "message": "Fichier vide ou corrompu."},
        )

    # Check PDF magic bytes
    if file_bytes.startswith(b"%PDF-"):
        return "application/pdf"
        
    # Check PNG magic bytes
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
        
    # Check JPEG magic bytes
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
        
    # Check GIF magic bytes
    if file_bytes.startswith(b"GIF87a") or file_bytes.startswith(b"GIF89a"):
        return "image/gif"
        
    # Check WEBP magic bytes
    if len(file_bytes) >= 12 and file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "INVALID_FILE_TYPE", "message": "Format de fichier non autorisé. Seuls les documents PDF et images sont acceptés."},
    )
