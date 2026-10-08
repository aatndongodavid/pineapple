#!/usr/bin/env bash
# scripts/backup.sh — Encrypted PostgreSQL Backup Script (Gate O-3)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_HOST="${DB_HOST:-db}"
DB_USER="${POSTGRES_USER:-pineapple_prod}"
DB_NAME="${POSTGRES_DB:-pineapple_prod}"
PASSPHRASE="${BACKUP_PASSPHRASE:-pineapple_backup_secret_passphrase}"

mkdir -p "$BACKUP_DIR"

DUMP_FILE="${BACKUP_DIR}/dump_${DB_NAME}_${TIMESTAMP}.sql"
ENC_FILE="${DUMP_FILE}.enc"

echo "=== [Pineapple Backup] Starting database dump at $(date) ==="

# 1. Export PostgreSQL Dump
PGPASSWORD="${POSTGRES_PASSWORD:-prod_secure_password_change_me}" pg_dump \
  -h "$DB_HOST" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --clean --if-exists > "$DUMP_FILE"

# 2. Chiffrement AES-256 avec openssl
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$DUMP_FILE" -out "$ENC_FILE" -pass "pass:$PASSPHRASE"
rm -f "$DUMP_FILE"

echo "--> Backup encrypted successfully: $ENC_FILE ($(du -h "$ENC_FILE" | cut -f1))"

# 3. Purge des sauvegardes > 30 jours
find "$BACKUP_DIR" -name "dump_*.enc" -mtime +30 -delete

echo "=== [Pineapple Backup] Backup process complete ==="
