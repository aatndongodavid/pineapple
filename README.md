# Pineapple — Plateforme B2B « Établissement d'abord »

> **Plateforme SaaS d'infrastructures et services d'établissement d'enseignement supérieur (écoles, facultés, universités).**

---

## 🌟 Vision Produit

Pineapple est une plateforme multi-tenant **réservée aux établissements d'enseignement**. 

1. **Vente aux établissements (Licence B2B)** : L'école s'abonne à la plateforme pour offrir des outils collaboratifs modernes à sa communauté (étudiants, délégués, enseignants, administration).
2. **Inscription publique en tant que VISITEUR** : Toute personne peut s'inscrire gratuitement. Un utilisateur `VISITOR` n'a accès qu'à un **fil d'actualité contenant exclusivement des publicités** et à l'assistant « Rejoindre mon établissement ». Aucun outil académique ou communautaire n'est déverrouillé sans appartenance.
3. **Appartenance et Rôles (`Membership`)** : Les outils (Salles, Annonces de classe, Délégués, Démocratie, Academy, Marketplace/Covoiturage, Opportunités, Messagerie) ne sont accessibles qu'aux utilisateurs rattachés à un établissement avec une licence active.
4. **Deux modes de rattachement** :
   - **Mode A (Auto-rattachement par état civil)** : Correspondance exacte à 100% sur 5 champs du registre officiel (*roster*) : Nom, Prénom, Matricule, Date de naissance, Lieu de naissance.
   - **Mode B (Invitation par l'administration)** : Génération par l'école d'un identifiant unique et d'un mot de passe temporaire envoyés par e-mail au destinataire officiel.
5. **Gestion des Salles par les Délégués** : Seuls les **délégués désignés** de chaque classe (`DELEGATE`) peuvent déclarer l'état d'une salle physique (`OCCUPIED` / `FREE`). Les autres étudiants voient l'état et peuvent uniquement signaler une incohérence au délégué et à l'administration.

---

## 🏗️ Architecture & Choix Techniques

- **Backend** : FastAPI, Python 3.11+, Architecture Hexagonale / Domain-Driven Design (DDD).
  - Source de vérité unique pour les migrations : Alembic (`alembic upgrade head`).
  - Chiffrement au repos des champs d'état civil sensibles (Fernet / AES-256).
  - Validation dynamique des permissions RBAC calculées à chaque requête.
- **Frontend** : React 18, Vite, TypeScript, Zustand, Tailwind CSS, PWA offline.
  - Source de vérité des contrats : Schéma TypeScript auto-généré via OpenAPI (`npm run gen:api`).
  - Filtrage dynamique des interfaces et menus selon les permissions backend (`can(permission)`).
- **Infrastructures & Services** :
  - **PostgreSQL 16** (Base de données relationnelle multi-tenant)
  - **Redis** (Rate-limiting & Caching)
  - **MailHog** (Serveur SMTP dev et console d'inspection des e-mails d'invitation)
  - **Nginx** (Reverse Proxy & Serveur Web Production PWA)

---

## 🚀 Démarrage Rapide (Local Docker)

### Prérequis
- Docker Desktop (avec Docker Compose v2)
- Node.js 20+ & Python 3.11+ (facultatif si vous utilisez Docker)

### 1. Lancer la stack complète
```bash
docker compose up --build -d
```
Cette commande unique démarre :
- `db` (Postgres 16 sur le port 5432)
- `redis` (Redis sur le port 6379)
- `mailhog` (SMTP sur 1025, Interface Web e-mails sur `http://localhost:8025`)
- `backend` (FastAPI sur `http://localhost:8000`, qui exécute automatiquement `alembic upgrade head` et l'injection du seed de test)
- `frontend` (PWA React servi sur `http://localhost:3000`)

### 2. Comptes de Démonstration (Seed)

| Rôle | E-mail | Mot de passe | Description |
|------|--------|--------------|-------------|
| **Super Admin Plateforme** | `admin@pineapple.cm` | `Admin123!` | Gestion globale des abonnements établissements |
| **Admin Établissement (ENSPD)** | `admin@enspd.cm` | `Admin123!` | Administrateur de l'ENSPD Douala |
| **Staff Scolarité** | `staff@enspd.cm` | `Staff123!` | Gestion du registre et invitations Mode B |
| **Enseignant** | `teacher@enspd.cm` | `Teacher123!` | Professeur certifié ENSPD |
| **Délégué Titulaire (GIT 3)** | `delegate.git3@enspd.cm` | `Delegate123!` | Délégué titulaire avec droits de déclaration de salle |
| **Étudiant Membre (GIT 3)** | `student.git3@enspd.cm` | `Student123!` | Étudiant membre actif ENSPD |
| **Visiteur Non-Rattaché** | `visitor@gmail.com` | `Visitor123!` | Compte visiteur (pubs uniquement, aucun outil) |
| **Admin Établissement Expiré** | `admin@demo-expired.cm` | `Admin123!` | Établissement avec licence suspendue (lecture seule) |

---

## 🛠️ Commandes utiles (Makefile)

```bash
make up          # Démarre la stack docker locale
make down        # Arrête la stack docker
make migrate     # Exécute alembic upgrade head
make seed        # Réinjecte les données de démonstration
make test        # Lance les 23 tests backend (unit + integration)
make lint        # Vérifie ruff (backend) et eslint/tsc (frontend)
make gen-api     # Génère les types TS depuis l'OpenAPI FastAPI
make clean       # Nettoie les caches et conteneurs
```

---

## 🔒 Matrice des Rôles & Permissions

| Rôle | Portée | Accès Outils Académiques | Déclaration de Salle | Administration Registre |
|------|--------|-------------------------|-----------------------|--------------------------|
| `VISITOR` | Aucun | ❌ (Pubs uniquement) | ❌ | ❌ |
| `STUDENT` | Établissement | ✅ | ❌ (Signalement uniquement) | ❌ |
| `DELEGATE` | Classe | ✅ | ✅ (Pour sa classe) | ❌ |
| `TEACHER` | Établissement | ✅ (Publication Academy) | ❌ | ❌ |
| `STAFF` | Établissement | ✅ | ❌ | ✅ (Registre & Invitations) |
| `TENANT_ADMIN` | Établissement | ✅ | ✅ | ✅ (Complet + Délégués + Paramètres) |
| `PLATFORM_SUPER_ADMIN` | Global | ✅ | ✅ | ✅ (Création d'établissements) |

---

## 📜 Licence & Conformité

Consultez `docs/REFACTOR_REPORT.md` pour le rapport d'architecture complet, les schémas de données ERD (Mermaid) et l'audit de sécurité et conformité des données personnelles.
