#!/usr/bin/env bash
# scripts/rollback.sh — Single-Command Rollback Script (Gate O-2)

set -euo pipefail

PROD_COMPOSE="docker compose -f docker-compose.prod.yml"

echo "=== [Pineapple OS Rollback] Starting rollback sequence (Gate O-2) ==="

echo "--> 1. Rolling back last database migration (-1 step)..."
$PROD_COMPOSE run --rm backend alembic downgrade -1

echo "--> 2. Restarting backend and worker containers..."
$PROD_COMPOSE restart backend worker frontend

echo "--> 3. Checking health post-rollback..."
sleep 3
$PROD_COMPOSE ps

echo "=== [Pineapple OS Rollback] Rollback completed cleanly ==="
