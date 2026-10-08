# Makefile pour Pineapple 3.0

DOCKER_COMPOSE = docker compose
PROD_COMPOSE = docker compose -f docker-compose.prod.yml

GREEN = \033[0;32m
NC = \033[0m

.PHONY: help up up-build down logs ps prod-up prod-down prod-logs prod-ps migrate seed test lint gen-api e2e clean restart deploy rollback backup restore-test test-load

help: ## Affiche l'aide
	@echo "Commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

up: ## Démarre l'application locale complète
	$(DOCKER_COMPOSE) up -d

up-build: ## Reconstruit puis démarre l'application locale complète
	$(DOCKER_COMPOSE) up --build -d

down: ## Arrête l'application locale
	$(DOCKER_COMPOSE) down

logs: ## Affiche les logs locaux
	$(DOCKER_COMPOSE) logs -f

ps: ## Affiche l'état des conteneurs locaux
	$(DOCKER_COMPOSE) ps

prod-up: ## Démarre l'application avec docker-compose.prod.yml
	$(PROD_COMPOSE) up --build -d

prod-down: ## Arrête l'application lancée avec docker-compose.prod.yml
	$(PROD_COMPOSE) down

prod-logs: ## Affiche les logs de production
	$(PROD_COMPOSE) logs -f

prod-ps: ## Affiche l'état des conteneurs de production
	$(PROD_COMPOSE) ps

deploy: ## Lance le déploiement de production sans interruption
	bash ./scripts/deploy.sh

rollback: ## Exécute le retour arrière automatique (-1 migration)
	bash ./scripts/rollback.sh

backup: ## Déclenche une sauvegarde chiffrée AES-256 de la base de données
	bash ./scripts/backup.sh

restore-test: ## Exécute un test chronométré de restauration post-sinistre (Gate O-3)
	bash ./scripts/restore.sh

test-load: ## Exécute le test de charge et de latence p95 sur le backend (Gate O-8)
	pytest tests/load_test_10k.py

migrate: ## Applique les migrations Alembic dans le conteneur backend
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

seed: ## Injecte les données de démonstration dans le conteneur backend
	$(DOCKER_COMPOSE) exec backend python -m scripts.seed_data

test: ## Exécute les tests unitaires et d'intégration
	pytest tests

lint: ## Vérifie le code avec ruff/eslint/tsc
	$(DOCKER_COMPOSE) exec backend ruff check .
	cd frontend && npm run lint && npx tsc --noEmit

gen-api: ## Génère le schéma TypeScript depuis l'OpenAPI FastAPI
	cd frontend && npm run gen:api

e2e: ## Exécute les tests E2E Cypress
	cd frontend && npm run e2e

clean: ## Nettoie les fichiers temporaires et conteneurs
	$(DOCKER_COMPOSE) down -v
	rm -rf frontend/dist frontend/node_modules/.cache backend/.pytest_cache

restart: ## Redémarre les services locaux
	$(DOCKER_COMPOSE) restart
