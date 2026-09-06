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
- **Python 3.11** pour le backend FastAPI
- **Node.js 20** pour le frontend React / Vite
- **PostgreSQL 16** et **Redis** (fournis via Docker)

---

## Démarrage rapide (Quickstart)

### 1. Cloner le dépôt

```bash
git clone https://github.com/aatndongodavid/pineapple.git
cd pineapple
```

### 2. Lancer l'infrastructure

```bash
make up
```

Cette commande démarre PostgreSQL, Redis, le backend FastAPI et le frontend Nginx.

### 3. Appliquer les migrations

```bash
make migrate
```

### 4. Injecter les données de démonstration

```bash
make seed
```

### 5. Accéder à l'application

- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/docs

---

## Tests

```bash
make test-backend      # Lance les tests unitaires et d'intégration
make test-frontend     # Lance les tests du frontend (Cypress)
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