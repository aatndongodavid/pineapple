# tests/unit/test_csv_sanitization.py
from shared_kernel.infrastructure.encryption import sanitize_csv_cell

def test_sec_005_csv_formula_injection_escaped():
    """SEC-005: Les cellules CSV débutant par =, +, -, @ sont préfixées par une apostrophe pour neutraliser l'exécution de formule."""
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("+1+1") == "'+1+1"
    assert sanitize_csv_cell("-10") == "'-10"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"

def test_sec_005_normal_text_unchanged():
    """SEC-005: Les chaînes de texte ordinaires ne sont pas modifiées."""
    assert sanitize_csv_cell("KOUAM") == "KOUAM"
    assert sanitize_csv_cell("Jean-Paul") == "Jean-Paul"
