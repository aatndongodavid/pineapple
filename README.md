## README.md

# Pineapple 3.0 : The Ultimate University Operating System

![Pineapple](https://img.shields.io/badge/Pineapple-3.0-%2310B981)
![Licence](https://img.shields.io/badge/Licence-Propriétaire-red)

> **Connecter. Collaborer. Grandir.**

Pineapple n'est pas une simple application universitaire.  
C'est le **système d'exploitation numérique des campus africains** : une couche transverse qui relie les étudiants, les enseignants, les clubs, les élections et les services administratifs au sein d'une expérience unifiée, sécurisée et souveraine.

---

## Vision

Pineapple combine **identité vérifiée**, **certification annuelle automatique**, **démocratie étudiante sécurisée** et **services du quotidien** pour faire de chaque campus un écosystème numérique vivant.

Le véritable avantage compétitif n'est pas une fonctionnalité isolée, mais la combinaison :

**Identité + Certification + Souveraineté + Democracy**

---

## Architecture Domain-Driven Design

Pineapple est conçu selon les principes **DDD** et **architecture hexagonale**, organisé en contextes bornés :

| Contexte           | Responsabilité                                                            |
|--------------------|---------------------------------------------------------------------------|
| **Identity**       | Comptes, matricules, certification annuelle, Pineapple ID                 |
| **Community**      | Feed, organisations, salles, portée d'audience                            |
| **Democracy**      | Élections, candidatures, vote chiffré, audit immuable (cœur stratégique)  |
| **Academy**        | Bibliothèque, formations, corrigés premium, Pineapple Reader              |
| **Opportunities**  | Projets, recherche, stages, startups                                      |
| **Campus Life**    | Marketplace, covoiturage, messagerie transversale                         |
| **Monetization**   | Sponsoring, abonnements clubs, licences établissements                    |
| **Trust & Safety** | Modération, signalements, sécurité transversale                           |

Chaque contexte possède ses couches `domain`, `application`, `infrastructure` et communique via des **ports** et des **adaptateurs**.

---

## Prérequis

- **Docker** et **Docker Compose** pour l'infrastructure locale
- **Make** pour utiliser les raccourcis du `Makefile`
- **Python 3.11** et **Node.js 20** ne sont pas nécessaires sur la machine si vous lancez le projet avec Docker
- **PostgreSQL 16** et **Redis** (fournis via Docker)

---

## Démarrage rapide (Quickstart)

### 1. Cloner le dépôt

```bash
git clone https://github.com/aatndongodavid/pineapple.git
cd pineapple
```

### 2. Préparer les variables d'environnement

Pour le lancement local avec `docker-compose.yml`, les variables utiles sont déjà définies dans Docker Compose.
Le fichier `.env` n'est donc pas obligatoire pour démarrer en local.

Pour préparer une configuration personnelle ou tester `docker-compose.prod.yml`, copiez le modèle :

```bash
cp .env.example .env
```

Ne commitez jamais le fichier `.env`.

### 3. Construire et lancer les conteneurs

```bash
# construit les images Docker
docker compose build --no-cache
```

```bash
# lance les conteneurs
docker compose up -d
```

```bash
# vérifie l'état des conteneurs
docker compose ps
```

```bash
# affiche les logs
docker compose logs -f
```

Vous pouvez aussi utiliser le Makefile :

```bash
make up-build
```

Cette commande démarre PostgreSQL, Redis, le backend FastAPI et le frontend Nginx.

### 4. Appliquer les migrations

```bash
make migrate
```

Cette commande exécute Alembic puis crée les tables SQLAlchemy nécessaires au projet local.

### 5. Injecter les données de démonstration

```bash
make seed
```

Le seed crée notamment des utilisateurs de démonstration, une élection, des mouvements et des salles.

### 6. Accéder à l'application

- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/docs

---

## Commandes utiles

```bash
make up          # démarre les conteneurs déjà construits
make up-build    # reconstruit puis démarre les conteneurs
make migrate     # crée/met à jour les tables
make seed        # injecte les données de démonstration
make logs        # affiche les logs
make ps          # affiche l'état des conteneurs
make down        # arrête les conteneurs
```

Après une modification du code backend ou frontend, reconstruisez l'image concernée :

```bash
docker compose build backend
docker compose up -d backend
```

```bash
docker compose build frontend
docker compose up -d frontend
```

Ou, plus simplement :

```bash
docker compose up --build -d
```

Si vous modifiez uniquement les données ou voulez repartir d'une base vide :

```bash
docker compose down -v
docker compose up --build -d
make migrate
make seed
```

Attention : `docker compose down -v` supprime les données PostgreSQL locales.

---

## Accès à PostgreSQL

Le conteneur PostgreSQL s'appelle `pineapple_db`.

Connexion depuis le terminal :

```bash
docker compose exec db psql -U pineapple -d pineapple
```

Identifiants locaux :

```text
Host: localhost
Port: 5432
Database: pineapple
User: pineapple
Password: pineapple_dev_password
```

Lister les tables :

```sql
\dt
```

Compter les utilisateurs seedés :

```sql
SELECT COUNT(*) FROM users;
```

Voir quelques utilisateurs :

```sql
SELECT email, first_name, last_name FROM users;
```

---

## État actuel de l'intégration

Le frontend et le backend sont lancés ensemble par Docker Compose.
Le frontend appelle l'API backend sur `http://localhost:8000`.

Fonctionnalités actuellement vérifiées :

- démarrage Docker complet ;
- création des tables avec `make migrate` ;
- insertion des données de démonstration avec `make seed` ;
- API `/health` opérationnelle ;
- frontend servi sur `http://localhost:3000`.

Certaines fonctionnalités métier restent encore à stabiliser selon les écrans et les use cases.
Si la création de compte échoue depuis l'interface, vérifiez d'abord :

- que `make migrate` a bien été exécuté ;
- que le backend est démarré avec `docker compose ps` ;
- que le navigateur appelle bien `http://localhost:8000` ;
- que la requête contient le header `X-Tenant-ID`.

Les tenants de démonstration utilisés par le frontend sont :

```text
ENSPD: 11111111-1111-1111-1111-111111111111
UDo:   22222222-2222-2222-2222-222222222222
ENS:   33333333-3333-3333-3333-333333333333
```

---

## Structure du dépôt

```
pineapple/
├── backend/
│   ├── src/
│   │   ├── api/                # Routeurs FastAPI
│   │   ├── identity_context/
│   │   ├── community_context/
│   │   ├── democracy_context/  # Cœur stratégique
│   │   ├── academy_context/
│   │   ├── opportunities_context/
│   │   ├── campus_life_context/
│   │   ├── monetization_context/
│   │   ├── trust_safety_context/
│   │   └── shared_kernel/      # Socle transverse
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── features/           # Écrans et composants métier
│   │   ├── components/         # UI réutilisable
│   │   ├── lib/                # Stores, API, WebSocket
│   │   └── routes/             # Protection et routage
├── docker-compose.yml
└── Makefile
```

---

## Sécurité & Souveraineté

- **Séparation stricte** entre identité et bulletin de vote (chiffrement asymétrique, voter hash).
- **Audit immuable** pour chaque événement critique.
- **Multi‑tenancy** : chaque établissement reste souverain sur ses données.
- **Pineapple Reader** : filigrane dynamique, pas de téléchargement brut.

---

## Licence

Logiciel propriétaire – © 2026 Gemula. Tous droits réservés.

---
*Conçu avec passion à Douala, Cameroun.*
