# tests/unit/test_backup_restore_integrity.py

import os
import shutil
import subprocess
import tempfile
import pytest


def test_gate_o3_backup_scripts_exist():
    """
    Gate O-3: Vérification de l'existence et de l'exécutabilité des scripts de sauvegarde et de restauration.
    """
    assert os.path.exists("scripts/backup.sh")
    assert os.path.exists("scripts/restore.sh")


def test_gate_o3_backup_encryption_decryption_roundtrip():
    """
    Gate O-3: Vérification de l'intégrité du chiffrement AES-256 et du déchiffrement des sauvegardes.
    Si openssl est disponible dans le système (ex: Linux CI / conteneur), exécute le cycle complet.
    """
    openssl_bin = shutil.which("openssl")
    if not openssl_bin:
        pytest.skip("OpenSSL CLI non trouvé sur cette machine hôte (disponible dans conteneurs Linux)")

    passphrase = "pineapple_test_passphrase_123"
    original_data = b"CREATE TABLE test_table (id INT); INSERT INTO test_table VALUES (1);"

    with tempfile.NamedTemporaryFile(delete=False) as f_in, \
         tempfile.NamedTemporaryFile(delete=False) as f_enc, \
         tempfile.NamedTemporaryFile(delete=False) as f_dec:

        in_path = f_in.name
        enc_path = f_enc.name
        dec_path = f_dec.name

        try:
            f_in.write(original_data)
            f_in.close()
            f_enc.close()
            f_dec.close()

            # 1. Chiffrement AES-256 (openssl enc -aes-256-cbc)
            cmd_enc = [
                openssl_bin, "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
                "-in", in_path, "-out", enc_path, "-pass", f"pass:{passphrase}"
            ]
            res_enc = subprocess.run(cmd_enc, capture_output=True)
            assert res_enc.returncode == 0, f"Encryption failed: {res_enc.stderr.decode()}"

            # 2. Déchiffrement
            cmd_dec = [
                openssl_bin, "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                "-in", enc_path, "-out", dec_path, "-pass", f"pass:{passphrase}"
            ]
            res_dec = subprocess.run(cmd_dec, capture_output=True)
            assert res_dec.returncode == 0, f"Decryption failed: {res_dec.stderr.decode()}"

            with open(dec_path, "rb") as f:
                decrypted_data = f.read()

            assert decrypted_data == original_data

        finally:
            for p in (in_path, enc_path, dec_path):
                if os.path.exists(p):
                    os.remove(p)
