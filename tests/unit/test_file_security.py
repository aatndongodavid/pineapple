# tests/unit/test_file_security.py
import pytest
from fastapi import HTTPException
from shared_kernel.infrastructure.file_security import validate_file_magic_bytes, sanitize_filename

def test_sec_004_valid_pdf_magic_bytes_accepted():
    """SEC-004: Un vrai document PDF avec magic bytes %PDF- est validé."""
    pdf_bytes = b"%PDF-1.5 %Fake PDF Header Content"
    mime = validate_file_magic_bytes(pdf_bytes, "cour_algebrique.pdf")
    assert mime == "application/pdf"

def test_sec_004_fake_pdf_executable_rejected():
    """SEC-004: Un fichier exécutable maquillé en PDF par son extension doit être rejeté."""
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00 DOS Header Simulation"
    with pytest.raises(HTTPException) as exc:
        validate_file_magic_bytes(exe_bytes, "virus.pdf")
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "INVALID_FILE_TYPE"

def test_sec_004_path_traversal_filename_sanitized():
    """SEC-004: Les attaques par traversée de chemin dans les noms de fichiers sont neutralisées."""
    dangerous = "../../../etc/passwd"
    clean = sanitize_filename(dangerous)
    assert ".." not in clean
    assert "/" not in clean
    assert "\\" not in clean
    assert clean == "passwd"
