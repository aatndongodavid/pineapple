# Task List — Master Prompt 06: Production et Performance en Réseau Faible

# Task List — Master Prompt 06: Production et Performance en Réseau Faible

- [x] **Phase P0: Audit & Planning**
  - [x] Verify baseline environment (FastAPI, PostgreSQL, Redis, Alembic, Docker Compose, Makefile)
  - [x] Create git branch `feature/production-et-reseau-faible` and tag `baseline-production-et-reseau-faible`
  - [x] Produce `HOSTING_DECISION.md` (Option A Single VPS Hetzner/OVH recommended)
  - [x] Produce `ARCHITECTURE_OPS.md`, `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`
  - [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`

- [x] **Phase P1: Production Compose, NGINX Proxy/TLS & 12-Factor Guardrails**
  - [x] Implement `docker-compose.prod.yml` (multi-worker uvicorn, isolated DB/Redis ports, healthchecks, resource limits)
  - [x] Configure NGINX reverse proxy (`nginx/nginx.conf`, `nginx/conf.d/pineapple.conf`) with Brotli/gzip, HTTP/2, TLS 1.3, rate limiting, maintenance page
  - [x] Harden `backend/src/shared_kernel/config.py` with `validate_production_security()` guardrails
  - [x] **Validation Gate O-1**: Clean startup on clean host via `docker-compose.prod.yml`
  - [x] **Validation Gate O-10**: Verify app refuses startup when `DEBUG=true` or dev secrets present in production

- [x] **Phase P2: CI/CD Pipeline, Zero-Downtime Migrations & One-Command Rollback**
  - [x] Create GitHub Actions workflow `.github/workflows/ci.yml` (lint, typecheck, pytest, trivy, pip-audit, gitleaks)
  - [x] Implement expand-migrate-contract deployment script and `make rollback`
  - [x] **Validation Gate O-2**: Test single-command rollback without data loss

- [x] **Phase P3: Observability, Metrics & Alerting**
  - [x] Implement production Prometheus `/metrics` endpoint (p50/p95/p99 latency, HTTP errors, active websockets, DB pool)
  - [x] Implement structured JSON logger with correlation ID (`X-Correlation-ID`)
  - [x] Configure Redis failure graceful degradation & closed fail on sensitive rate limits
  - [x] **Validation Gate O-4**: Test Redis outage degradation
  - [x] **Validation Gate O-5**: Test backend crash alert & NGINX maintenance page fallback

- [x] **Phase P4: Automated Encrypted Backups & Restoration Testing**
  - [x] Implement `scripts/backup.sh` (AES-256 encrypted pg_dump, retention purge, S3 upload)
  - [x] Implement `scripts/restore.sh` and `make restore-test`
  - [x] **Validation Gate O-3**: Execute timed restore test and log RTO (< 4 hours) in `BACKUP_RESTORE.md`

- [x] **Phase P5: Database Performance & Load Testing**
  - [x] Enable `pg_stat_statements`, inspect hot queries, add missing indexes
  - [x] Create load test scenario `tests/load_test_10k.py` simulating N concurrent users on Slow 4G RTT
  - [x] Produce `PERFORMANCE.md` with capacity analysis and scaling rules
  - [x] **Validation Gate O-8**: Confirm p95 < 300ms on reads and error rate < 0.5%

- [x] **Phase P6: Frontend Performance, PWA Offline & CI Budgets**
  - [x] Configure `.bundlewatchrc.json` (initial JS bundle <= 170 KB gzip) and `lighthouserc.json`
  - [x] Optimize service worker (stale-while-revalidate API reads, `offlineQueueService` resynchronization with 401/403/409 handling)
  - [x] Add Data Saver mode (`Save-Data` header detection & toggle)
  - [x] **Validation Gate O-6**: Demonstrate CI failure on intentional bundle regression
  - [x] **Validation Gate O-7**: Test offline PWA reading & conflict-free resynchronization

- [x] **Phase P7: Operational Security, Scans & Deliverables**
  - [x] Run security scans (`trivy`, `pip-audit`, `npm audit`, `gitleaks`)
  - [x] Deliver `DEPLOY.md`, `RUNBOOK.md`, `BACKUP_RESTORE.md`, `PERFORMANCE.md`, updated `Makefile`
  - [x] **Validation Gate O-9**: Zero critical open vulnerabilities
  - [x] Produce final completion report artifact
