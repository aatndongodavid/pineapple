# Implementation Plan — Master Prompt 06: Production et Performance en Réseau Faible

**Document Ref:** `docs/ops/IMPLEMENTATION_PLAN.md`  
**Target Completion:** Master Prompt 06  
**Status:** In Progress (Phase 0)  

---

## 1. Executive Summary & Validation Gates (O-1 to O-10)

This implementation plan establishes production readiness, observability, disaster recovery, and low-bandwidth optimization for Pineapple OS.

| Gate # | Validation Target | Description | Phase |
|---|---|---|---|
| **O-1** | Fresh Production Deployment | Deploy from scratch on clean VM following `DEPLOY.md` (HTTPS, migrations, no dev seed). | Phase P1 |
| **O-10** | Unsafe Production Guardrail | App refuses to start in `production` if `DEBUG=true`, dev secret used, or CORS `*`. | Phase P1 |
| **O-2** | Zero-Downtime Rollback | Deployment update without downtime and single-command rollback (`make rollback`). | Phase P2 |
| **O-4** | Redis Failure Degradation | Degraded graceful execution when Redis fails, closed fail on sensitive rate limits. | Phase P3 |
| **O-5** | Backend Outage Alert & Maintenance | Alert triggered on backend crash, maintenance page served by proxy, auto-restart. | Phase P3 |
| **O-3** | Disaster Recovery Restoration | Restore database from encrypted backup within RTO ($\le$ 4h), timed test passed. | Phase P4 |
| **O-8** | 10k User Load Test | p95 latency < 300ms on reads, error rate < 0.5% under simulated load (`PERFORMANCE.md`). | Phase P5 |
| **O-6** | CI Performance Budgets | CI fails on JS bundle > 170KB gzip or Lighthouse score < 85 on Slow 4G. | Phase P6 |
| **O-7** | Offline PWA Resynchronization | Offline PWA read capability & sync queue resync without duplicate items or infinite loops. | Phase P6 |
| **O-9** | Security & Container Scans | Zero critical vulnerabilities in container images & dependencies (`trivy`, `pip-audit`). | Phase P7 |

---

## 2. Phase-by-Phase Roadmap

### Phase P0: Audit & Planning
- [x] Baseline check & git branch `feature/production-et-reseau-faible` with tag `baseline-production-et-reseau-faible`.
- [x] Produce `HOSTING_DECISION.md` (Single VPS Hetzner/OVH recommended at ~15,000 FCFA/mo).
- [x] Produce `ARCHITECTURE_OPS.md`, `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`.
- [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`.

### Phase P1: Production Compose, NGINX Proxy/TLS & 12-Factor Guardrails
- [ ] Create `docker-compose.prod.yml` with non-root users, `HEALTHCHECK`, memory/CPU caps, internal networks.
- [ ] Configure NGINX (`nginx/nginx.conf`, `nginx/conf.d/pineapple.conf`) with Brotli/Gzip, HTTP/2, TLS 1.3, rate limiting.
- [ ] Implement production security guardrails in `backend/src/shared_kernel/config.py` (`validate_production_security()`).
- [ ] **Validation Gates O-1 & O-10**: Clean deployment test & startup block on dev secrets.

### Phase P2: CI/CD Pipeline, Zero-Downtime Migrations & One-Command Rollback
- [ ] Build GitHub Actions workflow (`.github/workflows/ci.yml`): lint, typecheck, pytest, trivy scan, docker build.
- [ ] Implement expand-migrate-contract migration wrapper and `make rollback` script.
- [ ] **Validation Gate O-2**: Test single-command rollback.

### Phase P3: Observability, Metrics & Alerting
- [ ] Implement real Prometheus metrics endpoint (`/metrics`) in FastAPI (latencies p50/p95/p99, errors, websocket connections, DB pool).
- [ ] Configure structured JSON logging with correlation IDs (`X-Correlation-ID`).
- [ ] Implement Redis outage graceful degradation & rate limiter closed failure.
- [ ] **Validation Gates O-4 & O-5**: Test Redis failure and backend crash maintenance page.

### Phase P4: Automated Encrypted Backups & Restoration Testing
- [ ] Create `scripts/backup.sh` (encrypted pg_dump with GPG, retention cleanup, S3 upload).
- [ ] Create `scripts/restore.sh` and `make restore-test`.
- [ ] **Validation Gate O-3**: Run timed database restoration test (Target RTO $\le$ 4h).

### Phase P5: Database Performance & Load Testing
- [ ] Enable `pg_stat_statements`, add missing indexes on hot tables.
- [ ] Create load testing script `tests/load_test_10k.py` simulating N concurrent users on Slow 4G.
- [ ] Produce `PERFORMANCE.md` with load test results and scaling procedure.
- [ ] **Validation Gate O-8**: Confirm p95 < 300ms on reads and error rate < 0.5%.

### Phase P6: Frontend Performance, PWA Offline & CI Budgets
- [ ] Add `.bundlewatchrc.json` (JS bundle cap 170KB gzip) and `lighthouserc.json`.
- [ ] Optimize PWA service worker (Stale-While-Revalidate API cache, `offlineQueueService` resync).
- [ ] Add Data Saver mode (`Save-Data` header detection & UI toggle).
- [ ] **Validation Gates O-6 & O-7**: Verify CI budget failure on regression & offline resync.

### Phase P7: Operational Security, Scans & Deliverables
- [ ] Run Trivy, pip-audit, npm audit, gitleaks security scans.
- [ ] Produce `DEPLOY.md`, `RUNBOOK.md`, `BACKUP_RESTORE.md`, updated `Makefile`, and final completion report.
- [ ] **Validation Gate O-9**: Confirm zero critical vulnerabilities.
