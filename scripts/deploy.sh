#!/usr/bin/env bash
# scripts/deploy.sh — Production Zero-Downtime Deployment Script (Pineapple OS)

set -euo pipefail

PROD_COMPOSE="docker compose -f docker-compose.prod.yml"

echo "=== [Pineapple OS Deployment] Starting deployment sequence ==="

# 1. Verification des variables d'environnement de production
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
fi

echo "--> 1. Pre-flight security verification..."
python3 -c "
from shared_kernel.config import settings
settings.validate_production_security()
print('Production security guardrails: OK')
" || { echo "CRITICAL: Production security guardrails failed!"; exit 1; }

echo "--> 2. Building production container images..."
$PROD_COMPOSE build --no-cache

echo "--> 3. Running database migrations (Expand phase)..."
$PROD_COMPOSE run --rm backend alembic upgrade head

echo "--> 4. Updating application containers with zero downtime..."
$PROD_COMPOSE up -d --no-deps backend worker frontend

echo "--> 5. Verifying service health..."
sleep 5
$PROD_COMPOSE ps

echo "=== [Pineapple OS Deployment] Deployment finished successfully ==="
