
## Makefile

```makefile
# Makefile pour Pineapple 3.0

# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
DOCKER_COMPOSE = docker compose

# Couleurs (optionnel)
GREEN = \033[0;32m
NC = \033[0m

.PHONY: help up down logs test-backend test-frontend migrate seed build-front build-backend restart

help: ## Affiche l'aide
	@echo "Commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

up: ## Démarre l'infrastructure complète (Docker)
	$(DOCKER_COMPOSE) up -d

down: ## Arrête l'infrastructure
	$(DOCKER_COMPOSE) down

logs: ## Affiche les logs des services
	$(DOCKER_COMPOSE) logs -f

test-backend: ## Lance les tests backend avec couverture
	cd $(BACKEND_DIR) && pytest tests/unit tests/integration --cov=src --cov-report=term-missing

test-frontend: ## Lance les tests frontend (Cypress)
	cd $(FRONTEND_DIR) && npx cypress run

migrate: ## Applique les migrations Alembic
	cd $(BACKEND_DIR) && alembic upgrade head

seed: ## Injecte les données de démonstration
	cd $(BACKEND_DIR) && python -m src.scripts.seed_data

build-front: ## Compile le frontend PWA
	cd $(FRONTEND_DIR) && npm run build

build-backend: ## Compile l'image Docker du backend
	$(DOCKER_COMPOSE) build backend

restart: ## Redémarre les services
	$(DOCKER_COMPOSE) restart