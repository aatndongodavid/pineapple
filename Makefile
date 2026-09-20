# Makefile pour Pineapple 3.0

DOCKER_COMPOSE = docker compose
PROD_COMPOSE = docker compose -f docker-compose.prod.yml

GREEN = \033[0;32m
NC = \033[0m

.PHONY: help up up-build down logs ps prod-up prod-down prod-logs prod-ps migrate seed restart

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

migrate: ## Applique les migrations Alembic dans le conteneur backend
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

seed: ## Injecte les données de démonstration dans le conteneur backend
	$(DOCKER_COMPOSE) exec backend python -m src.scripts.seed_data

restart: ## Redémarre les services locaux
	$(DOCKER_COMPOSE) restart
