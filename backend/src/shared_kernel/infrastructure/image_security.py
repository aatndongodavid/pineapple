# backend/src/shared_kernel/infrastructure/image_security.py

import io
import logging
from PIL import Image

logger = logging.getLogger("pineapple.security.image")

MAX_IMAGE_DIMENSION = 4096  # Max 4096px de largeur/hauteur
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB max


class UnsafeImageError(Exception):
    """Exception levée lorsqu'une image ne satisfait pas les critères de sécurité."""
    pass


def sanitize_and_process_image(file_bytes: bytes, target_format: str = "PNG") -> bytes:
    """
    Sanitise et re-encode de façon sécurisée une image envoyée par un utilisateur:
    1. Vérification de la taille du fichier.
    2. Inspection du contenu réel via Pillow (neutralise les payloads malveillants).
    3. Protection contre les Decompression Bombs (limitation de résolution).
    4. Suppression systématique des métadonnées EXIF (données personnelles/géolocalisation).
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise UnsafeImageError("La taille de l'image dépasse la limite maximale autorisée de 10 MB.")

    try:
        image_stream = io.BytesIO(file_bytes)
        with Image.open(image_stream) as img:
            img.verify()  # Valide l'intégrité de la structure d'image

        # Re-ouvrir pour la manipulation (verify() ferme la lecture)
        image_stream.seek(0)
        with Image.open(image_stream) as img:
            width, height = img.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise UnsafeImageError(
                    f"Résolution trop élevée ({width}x{height}). Max {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}px."
                )

            # Re-créer une image propre sans métadonnées EXIF
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(list(img.getdata()))

            output_stream = io.BytesIO()
            fmt = target_format.upper()
            if fmt == "JPG":
                fmt = "JPEG"
                if clean_img.mode in ("RGBA", "P"):
                    clean_img = clean_img.convert("RGB")

            clean_img.save(output_stream, format=fmt, optimize=True)
            return output_stream.getvalue()

    except UnsafeImageError:
        raise
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise UnsafeImageError("Format ou contenu d'image invalide ou corrompu.")
