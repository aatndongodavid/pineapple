# Decision Document — Hosting & Infrastructure Options (Pineapple OS)

**Document Ref:** `docs/ops/HOSTING_DECISION.md`  
**Target Region:** Cameroun (Douala / Yaoundé)  
**Currency:** XAF (FCFA) & USD / EUR  

---

## 1. Context & Objectives

Pineapple OS is designed for educational institutions in Cameroon and Central Africa. The hosting infrastructure must meet the following criteria:
1. **Low latency** for mobile networks (2G/3G/4G) in Douala and Yaoundé.
2. **Predictable & Low Cost** in local currency (XAF FCFA).
3. **Operational Simplicity** for a lean team (Single-command deployment, automated backups, clear runbooks).
4. **Data Sovereignty & Security** (GDPR/Local privacy compliance, encrypted backups, 12-factor secrets management).

---

## 2. Comparison of Hosting Options

| Criterion | Option A: VPS Dedicated / Cloud (Hetzner / OVH EU) + Docker Compose | Option B: Managed European PaaS (Scaleway / Render + Managed Postgres) | Option C: AWS South Africa Region (`af-south-1` Cape Town) |
|---|---|---|---|
| **Architecture** | Single VPS (4 vCPU / 8-16 GB RAM / 160 GB NVMe) + Docker Compose + Local Postgres | App on PaaS / VM + Managed Postgres DB + Redis | AWS ECS / EKS + RDS Postgres + ElastiCache Redis in Cape Town |
| **Measured Latency (Douala/Yde)** | ~90 – 120 ms (via Equiano/WACS/MainOne subsea fiber cables to Western Europe) | ~100 – 130 ms | ~180 – 240 ms (Network routing from West Africa to South Africa often routes via Europe!) |
| **Monthly Cost (XAF / USD)** | **~12,000 – 20,000 XAF/mo** ($20 – $30 USD / €15 – €25) | **~45,000 – 75,000 XAF/mo** ($70 – $120 USD) | **~150,000 – 350,000 XAF/mo** ($240 – $550+ USD) |
| **Operational Complexity** | **Very Low** (`docker compose up -d`, single server runbook) | **Low** (Managed DB maintenance, PaaS CLI) | **High** (AWS VPC, IAM, NAT Gateways, ECS task definitions, ECR) |
| **Backup & Disaster Recovery** | Automated daily pg_dump + WAL continuous sync to S3 / Backblaze B2 | Managed DB snapshots + S3 export | AWS Automated RDS Snapshots + Cross-region S3 replication |
| **Exit Strategy** | Standard Docker containers & Postgres SQL dumps (Zero lock-in) | Standard Docker & Postgres (Zero lock-in) | Proprietary AWS services (Moderate refactoring needed) |

---

## 3. Key Findings on Network Routing in Central Africa

Counter-intuitively, latency from Douala/Yaoundé to South Africa (`af-south-1`) is **higher** than latency to Western Europe (Frankfurt, Paris, Lisbon):
- Subsea fiber optics (Equiano, WACS, MainOne, SAT-3) connect Douala directly to European landing stations (Lisbon, Marseille, London) with **90-110 ms round-trip time (RTT)**.
- Intra-African internet routing between West/Central Africa and Southern Africa frequently traverses European IXPs (Internet Exchange Points), resulting in RTTs of **180-240 ms**.

---

## 4. Recommended Target Architecture

### Primary Recommendation: **Option A (VPS Dedicated / Cloud EU - Hetzner / OVH)**

- **Compute**: Hetzner CX32 / CPX31 (4 vCPU AMD EPYC, 8 GB RAM, 160 GB NVMe SSD) @ €14.50/month (~9,500 XAF/month).
- **Off-site Backup Storage**: Backblaze B2 / Scaleway Object Storage @ $1-3/month (~1,500 XAF/month).
- **Reverse Proxy & TLS**: NGINX + Certbot (Let's Encrypt TLS 1.3, HTTP/2, Brotli compression, rate limiting).
- **Database & Cache**: Postgres 16 + Redis 7 in isolated internal Docker networks (not exposed to host public IP).
- **Total Monthly Cost**: **~12,000 to 15,000 FCFA / month ($20 - $25 USD)**.

### Growth & Scaling Strategy (Migration Path)
- **Phase 1 (0 – 10 Schools, < 5,000 active students)**: Option A (Single VPS with Docker Compose).
- **Phase 2 (10 – 50 Schools, 5,000 – 50,000 active students)**: Separate Postgres onto a dedicated database VPS (Hetzner / Scaleway Managed Postgres) + load balancer.
- **Phase 3 (50+ Schools, > 50,000 active students)**: Migrate to Kubernetes / Multi-node cluster or AWS if enterprise SLAs require multi-AZ failover.

---

## 5. Security & Data Protection Decisions

1. **Strict 12-Factor Configuration**: Production application refuses to start if `DEBUG=True`, if `JWT_SECRET_KEY` uses a development default, or if CORS uses `*`.
2. **Isolated Database Access**: Postgres and Redis ports (`5432`, `6379`) are **NEVER** published to host interface in production (`ports` excluded from `docker-compose.prod.yml`).
3. **Encrypted Backups**: Daily automated dumps chiffrés avec GPG / AES-256 transmis vers S3 / Backblaze B2.
