# Architecture Operations & Production Engineering (Pineapple OS)

**Document Ref:** `docs/ops/ARCHITECTURE_OPS.md`  
**Target OS / Env:** Linux / Docker Compose / NGINX / PostgreSQL 16 / Redis 7  
**Timezone / Region:** `Africa/Douala` (GMT+1) | Cameroun  

---

## 1. Overview & Operational Principles

This document defines the production engineering standards for Pineapple OS. The platform is optimized for **low-bandwidth mobile networks (Slow 3G / 4G)** and **low-end Android mobile devices** commonly used across Cameroon.

### Core Pillars
1. **12-Factor Compliance**: Strict environment variable configuration. Startup guards block execution if production settings are unsafe.
2. **Zero-Downtime Migrations**: Expand $\rightarrow$ Migrate $\rightarrow$ Contract schema evolution pattern enforced via Alembic.
3. **Automated & Tested Backups**: Daily encrypted Postgres backups with automated monthly restoration tests.
4. **Resilient Offline-First PWA**: Service Worker caching with stale-while-revalidate for read endpoints, offline sync queue with anti-duplicate logic.
5. **Lightweight Frontend Budgets**: Bundle size caps (JS initial $\le$ 170 KB gzip), Brotli/Gzip compression, image optimization (WebP/AVIF with thumbnails).
6. **Observability & Alerting**: Structured JSON logs with correlation IDs, Prometheus metrics (`/metrics`), Sentry error tracking, and health checks.

---

## 2. Infrastructure Architecture & Docker Topology

```mermaid
graph TD
    Client["📱 Client (Mobile / PWA / Web)"] -->|HTTPS / WSS (Port 443)| Proxy["🛡️ NGINX Reverse Proxy + Let's Encrypt TLS"]
    
    subgraph "Internal Docker Network (pineapple_prod_net)"
        Proxy -->|HTTP (Brotli / Gzip)| StaticFront["🌐 Static Frontend (Nginx SPA)"]
        Proxy -->|HTTP / WS (Uvicorn Workers)| API["⚡ FastAPI Backend (Multi-Worker)"]
        API -->|Outbox Events / Tasks| Worker["⚙️ Async Notification Worker"]
        
        API -->|Async Engine| DB[("🐘 PostgreSQL 16 (Volume)")]
        Worker --> DB
        
        API -->|Cache / Rate Limit / Locks| Redis[("🔴 Redis 7 (Eviction & Persistence)")]
        Worker --> Redis
        
        BackupJob["📦 Backup Service (Cron / Dump / GPG)"] --> DB
    end
    
    BackupJob -->|AES-256 Encrypted Dumps| S3["☁️ Remote Object Storage (S3 / B2)"]
    API -->|Metrics| Prom["📊 Prometheus Scraper"]
```

---

## 3. Environment Isolation & Guardrails (12-Factor)

The backend (`backend/src/shared_kernel/config.py`) enforces strict validation at startup (`validate_production_security()`):
- **`ENVIRONMENT=production` Guardrails**:
  - `DEBUG` **MUST** be `false`.
  - `JWT_SECRET_KEY` **MUST NOT** be default or shorter than 32 characters.
  - `ELECTION_PEPPER_SECRET` **MUST NOT** be default.
  - `DATABASE_URL` **MUST NOT** contain `localhost` or default passwords (`pineapple_dev_password`).
  - CORS origins **MUST NOT** include wildcard `*`.
  - Rate limiting **MUST** run against Redis (in-memory fallback prohibited in production).

---

## 4. Zero-Downtime Migration Pattern (Expand → Migrate → Contract)

To prevent breaking active sessions during deployments:
1. **Expand**: Add new columns or tables as nullable or with defaults. Code supports both old and new schemas.
2. **Migrate**: Run `alembic upgrade head` before rolling out the new backend containers.
3. **Deploy**: Restart backend workers with zero downtime using rolling container updates (`docker compose up -d --no-deps --build backend`).
4. **Contract**: Remove legacy columns/tables in a subsequent version after all code dependencies are deprecated.

---

## 5. Backup & Disaster Recovery Strategy

| Metric | Target | Enforced Mechanism |
|---|---|---|
| **RPO (Recovery Point Objective)** | $\le$ 1 Hour (Target: 15 min WAL) | Daily full dump + WAL archiver |
| **RTO (Recovery Time Objective)** | $\le$ 4 Hours | Automated script `make restore-test` |
| **Retention Policy** | 30 Days daily + 12 Months monthly | S3 Lifecycle Rules |
| **Encryption** | AES-256 (GPG symmetrically encrypted) | Mandatory before S3 upload |

---

## 6. Frontend Performance & Low-Bandwidth Budgets

- **Initial JS Bundle Cap**: $\le$ 170 KB gzipped.
- **Lighthouse Performance Score**: $\ge$ 85 on Slow 4G / 4x CPU Throttling.
- **Service Worker Strategy**:
  - Assets: Cache-First (hashed versioning).
  - Stable API Reads: Stale-While-Revalidate with max-age.
  - Offline Writes: `offlineQueueService` with background sync & retry backoff.
- **Data Saver Mode**: Respects `Save-Data` HTTP header to disable prefetching and load low-res images.
