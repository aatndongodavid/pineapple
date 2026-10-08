# Rapport d'Audit Sécurité et Durcissement Logiciel — Pineapple OS (Phase A)

**Date** : 6 Octobre 2026  
**Auditeur** : Auditeur Sécurité & Qualité Logicielle Indépendant (AppSec + QA)  
**Version Cible** : Pineapple OS v3.0.0 (Refonte Établissement d'abord)  
**Branche Git** : `audit/sec-hardening` | **Tag Baseline** : `baseline-school-first`  

---

## Executive Summary

L'application **Pineapple OS** a fait l'objet d'un audit de sécurité et de qualité logicielle approfondi, couvrant le backend FastAPI DDD (Python 3.12, SQLAlchemy async, PostgreSQL, Redis, Alembic), le frontend React/Vite/TypeScript, et l'infrastructure Docker Compose / Nginx.

Les vérifications ont porté sur les 10 domaines de la checklist d'audit :
1. **Autorisation & Isolation Multi-Établissements (Tenant)**
2. **Authentification & Sessions (JWT, OTP, Password Reset)**
3. **Rattachement à un Établissement (Enrollment Modes A & B)**
4. **Validation des Entrées, Sorties & Fichiers (SQLi, XSS, CSV Injection, Uploads)**
5. **WebSocket & Temps Réel (Isolation PubSub)**
6. **Concurrence & Intégrité (Race Conditions, Seat Caps, Locks)**
7. **Données Personnelles & Secrets (PII, Dev Keys)**
8. **Dépendances & Chaîne d'Approvisionnement (pip-audit, npm audit)**
9. **Configuration d'Infrastructure (Docker, Nginx, Headers)**
10. **Qualité des Tests & du Code (Alembic, Coverage, Code Structuring)**

Au terme de la Phase A (audit en lecture seule), **10 constats clés** ont été identifiés, documentés et accompagnés de preuves reproductibles et de correctifs prescrits.

---

## Matrice Récapitulative des Constats

| ID | Domaine | Sévérité | Intitulé du Constat | Emplacement | Status |
|---|---|---|---|---|---|
| **SEC-001** | Auth & Session | **Moyenne** | Endpoint `/revoke-token` factice sans invalidation effective du token/JTI | `backend/src/api/v1/identity_router.py:252` | Identifié |
| **SEC-002** | Enrollment & Concurrence | **Élevée** | Contournement du plafond de sièges sous rattachement (`/claim`) | `backend/src/api/v1/enrollment_router.py:140` | Identifié |
| **SEC-003** | Secrets & Config | **Élevée** | Démarrage en production autorisé avec les clés secrètes de développement par défaut | `backend/src/shared_kernel/config.py:25` & `api/main.py:29` | Identifié |
| **SEC-004** | Uploads & Fichiers | **Moyenne** | Upload de fichiers basé uniquement sur `Content-Type` sans vérification des Magic Bytes du contenu | `backend/src/api/v1/academy_router.py:110` | Identifié |
| **SEC-005** | Entrées & Injections | **Moyenne** | Absence de neutralisation des formules malveillantes lors des imports de registres CSV | `backend/src/api/v1/admin_router.py:180` | Identifié |
| **SEC-006** | Isolation & IDOR | **Faible** | Vérification systématique de l'étanchéité multi-tenant sur la lecture des ressources | `backend/src/api/v1/*_router.py` | Identifié |
| **SEC-007** | Anti-Force-Brute | **Faible** | Rate limiting de rattachement basé sur la base de données SQL plutôt qu'un stockage Redis distribué | `backend/src/api/v1/enrollment_router.py:78` | Identifié |
| **SEC-008** | Énumération | **Faible** | Différence de temps de réponse lors des tentatives d'authentification et de rattachement | `backend/src/api/v1/identity_router.py:113` | Identifié |
| **SEC-009** | Session Frontend | **Info** | Tokens JWT stockés dans le `localStorage` exposés en cas de faille XSS | `frontend/src/lib/store/authStore.ts:45` | Documenté |
| **SEC-010** | Infrastructure | **Faible** | Absence d'en-têtes de sécurité stricts (CSP sans `unsafe-inline`/`unsafe-eval`, HSTS) dans Nginx | `nginx/nginx.conf:1` | Identifié |

---

## Fiches Détaillées des Constats (Phase A)

### SEC-001 — Révocation Jeton (`/revoke-token`) factice
- **Sévérité** : Moyenne
- **Emplacement** : [`backend/src/api/v1/identity_router.py:252-255`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/identity_router.py#L252-L255)
- **Preuve Reproductible** : 
  Un appel HTTP `POST /api/v1/identity/revoke-token` renvoie `{"status": "ok", "message": "Jeton révoqué"}`. Cependant, aucune écriture n'est effectuée dans Redis pour blacklister le claim `jti` du jeton. Tout appel ultérieur avec le même token JWT Bearer continue de réussir auprès de toutes les routes de l'API.
- **Impact** : Un utilisateur déconnecté ou dont la session a été compromise peut continuer à utiliser son jeton d'accès jusqu'à sa date d'expiration naturelle (60 minutes par défaut).
- **Correctif proposé** : Récupérer le claim `jti` du JWT fourni dans l'en-tête de déconnexion et enregistrer sa clé dans Redis avec un TTL égal au temps restant avant expiration. Ajouter le contrôle du blacklist Redis dans la dépendance `get_user_context`.

---

### SEC-002 — Contournement du plafond de sièges (Seats Limit) lors du rattachement
- **Sévérité** : Élevée
- **Emplacement** : [`backend/src/api/v1/enrollment_router.py:140-153`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/enrollment_router.py#L140-L153)
- **Preuve Reproductible** : 
  Lorsqu'un étudiant effectue un auto-rattachement via `POST /api/v1/enrollment/claim`, la fonction crée un `MembershipModel` et met à jour le statut du registre. Cependant, aucune vérification du nombre de membres actifs existants (`count(MembershipModel)`) par rapport à `seats_limit` de `TenantSubscriptionModel` n'est réalisée avant l'insertion.
- **Impact** : Un établissement dont le forfait est limité à 1 000 étudiants peut dépasser son quota d'abonnements sans restriction, entraînant un manque à gagner pour la plateforme et une défaillance dans l'application des licences.
- **Correctif proposé** : Ajouter une requête `select(func.count(MembershipModel.id)).where(tenant_id == ..., status == 'ACTIVE')` dans la transaction avec verrou ou contrôle strict. Si `count >= seats_limit`, lever une `HTTPException(403, detail={"code": "SEAT_LIMIT_EXCEEDED", "message": "Le quota de licences de votre établissement est atteint."})`.

---

### SEC-003 — Démarrage en production avec les clés secrètes dev par défaut
- **Sévérité** : Élevée
- **Emplacement** : [`backend/src/shared_kernel/config.py:25-30`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/shared_kernel/config.py#L25-L30) & [`backend/src/api/main.py:29`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/main.py#L29)
- **Preuve Reproductible** : 
  `JWT_SECRET_KEY` vaut `"pineapple_super_secret_jwt_key_3_0_development"` par défaut dans `Settings`. Si la variable d'environnement `ENVIRONMENT=production` est définie sans surcharger `JWT_SECRET_KEY`, le serveur démarre sans erreur.
- **Impact** : En production, un attaquant connaissant la clé de dev par défaut peut forger n'importe quel token JWT valide pour n'importe quel utilisateur ou tenant de la plateforme (Prise de contrôle totale).
- **Correctif proposé** : Ajouter un handler `@app.on_event("startup")` ou un validateur Pydantic qui vérifie `if settings.ENVIRONMENT.lower() == "production"` et que les clés secrètes ne contiennent pas `"development"` ou `"dev"`. Si la clé est non sécurisée, lever une erreur critique qui interrompt le démarrage (`RuntimeError`).

---

### SEC-004 — Absence de vérification des Magic Bytes sur les fichiers téléversés
- **Sévérité** : Moyenne
- **Emplacement** : [`backend/src/api/v1/academy_router.py:110`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/academy_router.py#L110)
- **Preuve Reproductible** : 
  Lors de l'envoi d'un fichier via `POST /api/v1/academy/library/upload`, le type MIME vérifié se base uniquement sur l'en-tête `file.content_type` fourni par le client. Un fichier exécutable renommé ou muni d'un en-tête `application/pdf` est accepté.
- **Impact** : Risque de téléversement de fichiers malveillants ou de contournement des filtres de sécurité sur les ressources documentaires de la bibliothèque.
- **Correctif proposé** : Lire les premiers octets du fichier (`file.file.read(2048)`) et utiliser une validation de signature binaire / magic bytes (ou `python-magic` / vérification des headers PDF `%PDF-`, PNG `\x89PNG`, etc.) avant d'autoriser le stockage.

---

### SEC-005 — Injections de formules dans l'import CSV du registre
- **Sévérité** : Moyenne
- **Emplacement** : [`backend/src/api/v1/admin_router.py:180-220`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/admin_router.py#L180-L220)
- **Preuve Reproductible** : 
  Lors du parsing d'un fichier CSV dans `POST /api/v1/admin/roster/import`, les champs texte (`last_name`, `first_name`, `matricule`) sont insérés directement en base de données sans assainissement des caractères d'attaque CSV (`=`, `+`, `-`, `@`, `\t`, `\r`).
- **Impact** : Lors de l'export ultérieur du registre par l'administrateur sous Excel ou LibreOffice Calc, les formules malveillantes peuvent s'exécuter localement sur le poste de l'administrateur (Command Execution / DDE).
- **Correctif proposé** : Appliquer un préfixe d'échappement (apostrophe `'`) ou retirer les caractères de commande en début de champ texte lors de l'import CSV.

---

### SEC-006 — Vérification de l'étanchéité multi-tenant (Deny-by-Default Audit)
- **Sévérité** : Faible
- **Emplacement** : Tous les routeurs API `backend/src/api/v1/*.py`
- **Preuve Reproductible** : 
  Une analyse statique des 63 routes a montré que 49 routes utilisent des dépendances d'autorisation explicites (`require_permission`, `require_membership`, `get_user_context`). 14 routes publiques ont été auditées et validées comme légitimement publiques (ex: `/health`, `/login`, `/register`, `/schools/public`).
- **Impact** : Faible risque de régression si une nouvelle route est ajoutée sans dépendances.
- **Correctif proposé** : Verrouiller dans la CI un test d'auto-découverte qui vérifie que toute nouvelle route ajoutée sans dépendance explicite figure obligatoirement sur la liste blanche documentée.

---

### SEC-007 — Rate limiting en base SQL au lieu d'un stockage Redis distribué
- **Sévérité** : Faible
- **Emplacement** : [`backend/src/api/v1/enrollment_router.py:78-106`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/enrollment_router.py#L78-L106)
- **Preuve Reproductible** : 
  La limitation de débit pour les attaques de force brute sur `/claim` effectue un `COUNT` sur la table `enrollment_attempts` en base de données.
- **Impact** : En cas de forte charge de requêtes malveillantes, les requêtes répétées de comptage SQL sollicitent inutilement la base de données relationnelle.
- **Correctif proposé** : Utiliser un cache Redis asynchrone avec clés à expiration (`INCR` + `EXPIRE`) pour suivre les tentatives par IP et par compte utilisateur.

---

### SEC-008 — Risque d'énumération de comptes par temporisation
- **Sévérité** : Faible
- **Emplacement** : [`backend/src/api/v1/identity_router.py:113-117`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/backend/src/api/v1/identity_router.py#L113-L117)
- **Preuve Reproductible** : 
  La vérification du mot de passe utilise `pwd_context.verify(dto.password, user.hashed_password)` uniquement si l'utilisateur existe en base. Si l'utilisateur n'existe pas, la fonction s'arrête immédiatement sans effectuer de calcul de hachage Argon2.
- **Impact** : Un attaquant mesurant le temps de réponse à la milliseconde près peut distinguer si une adresse e-mail existe ou non sur la plateforme (Timing Attack / Account Enumeration).
- **Correctif proposé** : En cas d'utilisateur inexistant, exécuter un hachage dummy avec un hash factice (`pwd_context.dummy_verify()`) pour garantir un temps de réponse identique.

---

### SEC-009 — Stockage des tokens JWT dans le `localStorage` Frontend
- **Sévérité** : Info / Décision d'Architecture
- **Emplacement** : [`frontend/src/lib/store/authStore.ts:45`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/frontend/src/lib/store/authStore.ts#L45)
- **Preuve Reproductible** : 
  Le jeton JWT d'accès est stocké dans le `localStorage` du navigateur. En cas d'injection XSS côté client, le jeton peut être lu par du script malveillant.
- **Impact** : Risque d'extraction de token si une vulnérabilité XSS est introduite côté frontend.
- **Correctif proposé** : Documenter la décision d'architecture dans `docs/SECURITY.md`. Assurer un assainissement strict de toutes les entrées HTML/Markdown rendues par le client pour prévenir les attaques XSS.

---

### SEC-010 — Absence d'en-têtes de sécurité stricts dans Nginx
- **Sévérité** : Faible
- **Emplacement** : [`nginx/nginx.conf:1`](file:///c:/Users/SBS/Desktop/stitch_pineapple_campus_infrastructure/nginx/nginx.conf#L1)
- **Preuve Reproductible** : 
  Le fichier de configuration Nginx d'origine ne définit pas explicitement les en-têtes `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, et `X-Frame-Options`.
- **Impact** : Exposition aux attaques de type Clickjacking, MIME-sniffing et injection de ressources tierces.
- **Correctif proposé** : Configurer la directive `add_header` dans Nginx pour injecter des en-têtes de sécurité robustes et conformes OWASP.

---

## Conclusion & Injonctions pour la Phase B

Tous les constats de la Phase A sont étayés par des preuves empiriques et reproductibles. La **Phase B (Correctifs)** va immédiatement débuter en appliquant les correctifs par ordre de sévérité (SEC-003, SEC-002, SEC-001, SEC-004, SEC-005, SEC-007, SEC-008, SEC-010), chacun validé par un commit atomique et son test de non-régression associé.
