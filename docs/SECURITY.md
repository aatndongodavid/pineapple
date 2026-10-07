# Politiques & Modèle de Sécurité — Pineapple OS

## 1. Modèle de Menaces (Threat Model)

Pineapple OS est le système d'exploitation numérique des établissements scolaires et universitaires (Cameroun, zone CEMAC, Afrique centrale).
Le modèle de menaces couvre :
- **Attaquants externes** : Tentatives de force brute sur le rattachement d'étudiants (`/claim`, `/activate`), falsification de jetons JWT, énumération de comptes, injections SQL/CSV.
- **Utilisateurs malveillants internes** : Élévation de privilèges (étudiant se faisant passer pour délégué ou admin), contournement du quota de sièges d'un établissement, falsification d'en-tête `X-Tenant-ID` (IDOR inter-tenants).
- **Infrastructures hôtes vulnérables** : Exécution de scripts malveillants via upload de fichiers, démarrage du serveur avec des clés secrètes de développement par défaut en environnement de production.

---

## 2. Décisions d'Architecture & Gestion des Sessions

### A. Format & Cycle de Vie des Jetons JWT
- **Algorithme** : Verrouillé à `HS256` (HMAC-SHA256 avec clé minimale 256 bits).
- **Claims obligatoires** :
  - `sub` : Identifiant UUID unique de l'utilisateur.
  - `tid` : UUID de l'établissement (tenant) actif.
  - `mid` : UUID de l'appartenance (membership) active.
  - `role` : Rôle calculé (`VISITOR`, `STUDENT`, `DELEGATE`, `TEACHER`, `STAFF`, `TENANT_ADMIN`, `PLATFORM_SUPER_ADMIN`).
  - `jti` : Identifiant unique de jeton (UUIDv4) pour la révocation.
  - `exp` : Expiration (60 minutes par défaut).

### B. Révocation & Blacklist (SEC-001)
- Lors de l'appel à `POST /api/v1/identity/revoke-token`, le claim `jti` est enregistré dans la liste noire (`_REVOKED_JTIS` / Redis).
- La dépendance `get_user_context` rejette immédiatement (HTTP 401) tout jeton dont le `jti` figure dans la liste noire.

### C. Protection contre l'Énumération & Temporisation (SEC-008)
- Les tentatives d'authentification (`/login`) sur des comptes inexistants exécutent une vérification Argon2 avec un hash factice (`DUMMY_HASH`) pour garantir des temps de réponse stricts et constants, empêchant les attaques par temporisation (Timing Attacks).

### D. Stockage Frontend des Tokens (SEC-009)
- Le jeton JWT est conservé dans le `localStorage` pour permettre le support hors-ligne progressif (PWA) sur les réseaux mobiles à faible débit.
- **Atténuation XSS** : Toutes les entrées HTML et Markdown saisies par les utilisateurs sont rigoureusement échappées et assainies côté client.

---

## 3. Checklist de Revue de Sécurité pour les Chantiers Futurs

Toute nouvelle fonctionnalité ou modification d'API doit satisfaire cette checklist avant fusion :

- [ ] **Auth & Scope** : La route utilise-t-elle une dépendance `require_permission(...)` ou `get_user_context` ?
- [ ] **Tenant Isolation** : Toutes les requêtes SQL filtrent-elles explicitement sur `tenant_id == ctx.tenant_id` ?
- [ ] **Seats Quota** : La création de nouveaux membres vérifie-t-elle `active_members_count < seats_limit` ?
- [ ] **Injections** : Les entrées utilisateur sont-elles validées (Pydantic `extra="forbid"`) et les imports CSV assainis (`sanitize_csv_cell`) ?
- [ ] **Uploads** : Les fichiers téléversés font-ils l'objet d'une vérification des Magic Bytes (`validate_file_magic_bytes`) et du nom de fichier (`sanitize_filename`) ?
- [ ] **Non-Régression** : Des tests positifs et négatifs ont-ils été ajoutés et exécutés avec succès (`pytest`) ?
