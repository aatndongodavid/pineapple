# Task List - Master Prompt 05: Régie Publicitaire pour les Visiteurs

# Task List - Master Prompt 05: Régie Publicitaire pour les Visiteurs

- [x] **Phase 0: Audit & Planning**
  - [x] Verify baseline environment (FastAPI, SQLAlchemy async, PostgreSQL/SQLite, Alembic, JWT, permissions, PaymentProvider)
  - [x] Create git branch `feature/regie-publicitaire-visiteurs` and git tag `baseline-regie-publicitaire-visiteurs`
  - [x] Produce `POLICY.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_PLAN.md`, and `TASK_LIST.md`
  - [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`

- [x] **Phase 1: Database Schema & Migration (`0005_regie_publicitaire_visiteurs.py`)**
  - [x] Implement database models in `backend/src/monetization_context/infrastructure/persistence/models.py`:
    - `AdvertiserModel` & `AdvertiserUserModel`
    - `AdWalletModel` & `WalletTransactionModel`
    - `AdCampaignModel` & `AdTargetingRuleModel`
    - `AdCreativeModel` & `AdReviewEventModel`
    - `AdImpressionRawModel` & `AdStatsDailyModel`
    - `AdUserFeedbackModel` & `AdPolicyRuleModel`
  - [x] Create Alembic migration script `alembic/versions/0005_regie_publicitaire_visiteurs.py` with `upgrade()` and `downgrade()`
  - [x] Implement `AdWalletService` (immutable transaction journal, balance integrity, atomic debit)
  - [x] **Validation Gate R10**: Test concurrent wallet debits & journal sum equality (`tests/unit/test_ad_wallet_engine.py`)

- [x] **Phase 2: Moderation Workflow, Automated Policy & Creative Review**
  - [x] Implement `AdPolicyEngine` (blacklisted keywords, prohibited categories, URL scheme check)
  - [x] Implement `CreativeReviewService` (`PENDING_REVIEW` -> `APPROVED` / `REJECTED`, review event history)
  - [x] Implement image security check (type verification, EXIF metadata stripping, dimensions)
  - [x] **Validation Gate R3 & R6**: Test unapproved creative filter & malicious `javascript:` URL rejection (`tests/unit/test_ad_moderation_and_policy.py`)

- [x] **Phase 3: Visitor Ad Delivery Engine, Pacing & Frequency Capping**
  - [x] Implement `AdDeliveryEngine`:
    - Server-side active school membership check (`has_active_membership` -> return `[]`)
    - Coarse visitor targeting filter (city/region, language, device, hour)
    - Budget pacing calculation (`hourly_budget = daily_budget_xaf / 24`)
    - Session frequency capping
    - Priority-weighted auction selection & non-consecutive campaign constraint
  - [x] **Validation Gate R1, R2, R4, R7, R8**: Test server-side school member exclusion, visitor feed targeting, budget exhaustion auto-stop, frequency capping, pacing (`tests/unit/test_ad_delivery_engine.py`)

- [x] **Phase 4: Impression/Click Tracking, Signed Tokens & Aggregation**
  - [x] Implement `AdTokenService`: HMAC signed impression/click tokens with short TTL
  - [x] Implement `GET /api/v1/ads/click/{token}`: single-use token verification, click recording, open-redirect protection
  - [x] Implement `AdStatsAggregatorService`: daily stats rollup
  - [x] **Validation Gate R5 & R12**: Test single-use token replay prevention & CSV export accuracy (`tests/unit/test_ad_tracking_and_aggregation.py`)

- [x] **Phase 5: Self-Service Advertiser Workspace & Payment Top-Up**
  - [x] Implement `AdvertiserRouter` (`backend/src/api/v1/advertiser_router.py`):
    - Registration & login with `ADVERTISER` role
    - Wallet top-up via `PaymentProvider`
    - Campaign creation wizard (objective, model, budget, targeting)
    - Creative upload & review status tracking
    - Daily performance reports with CSV export
  - [x] **Validation Gate R9**: Test IDOR protection between advertisers (`tests/unit/test_advertiser_workspace_security.py`)

- [x] **Phase 6: Platform Admin Console & Anti-Fraud**
  - [x] Implement `AdminAdConsoleRouter`:
    - Moderation queue endpoint (approve/reject with reason)
    - User feedback endpoint (hide/report)
    - Auto-suspension trigger (> 5 reports) (**Gate R11**)
    - Manual wallet adjustment with audit log
  - [x] **Validation Gate R11**: Test high-report auto-suspension trigger (`tests/unit/test_ad_feedback_and_antifraud.py`)

- [x] **Phase 7: Visitor UI, i18n & Final Report**
  - [x] Update frontend visitor feed cards with "Sponsorisé" badge, "Pourquoi cette annonce ?", "Masquer / Signaler" dialog
  - [x] Update API endpoints in `frontend/src/lib/api/endpoints.ts`
  - [x] Run full test suite, produce `FINAL_REPORT.md`
