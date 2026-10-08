#!/usr/bin/env bash
# scripts/restore.sh — Database Restoration & Timed Test Script (Gate O-3)

set -euo pipefail

BACKUP_FILE="${1:-}"
DB_HOST="${DB_HOST:-db}"
DB_USER="${POSTGRES_USER:-pineapple_prod}"
DB_NAME="${POSTGRES_DB:-pineapple_prod}"
PASSPHRASE="${BACKUP_PASSPHRASE:-pineapple_backup_secret_passphrase}"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <path_to_encrypted_backup_file.enc>"
  exit 1
fi

echo "=== [Pineapple Restore] Starting restoration process (Gate O-3) ==="
START_TIME=$(date +%s)

TEMP_SQL="/tmp/restore_temp_$$.sql"

echo "--> 1. Decrypting backup file..."
openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP_FILE" -out "$TEMP_SQL" -pass "pass:$PASSPHRASE"

echo "--> 2. Restoring PostgreSQL database schema and data..."
PGPASSWORD="${POSTGRES_PASSWORD:-prod_secure_password_change_me}" psql \
  -h "$DB_HOST" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -f "$TEMP_SQL" > /dev/null

rm -f "$TEMP_SQL"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "=== [Pineapple Restore] Restoration complete in ${DURATION} seconds (RTO Target <= 14400s) ==="
