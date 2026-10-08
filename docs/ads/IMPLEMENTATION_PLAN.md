# Implementation Plan — Master Prompt 05: Régie Publicitaire pour les Visiteurs

**Pineapple OS — AdTech Platform for Visitors**  
**Branch**: `feature/regie-publicitaire-visiteurs`  
**Tag**: `baseline-regie-publicitaire-visiteurs`  
**Timezone**: `Africa/Douala` (WAT) | **Currency**: XAF (FCFA) integers  

---

## Phase Breakdown

### Phase 0: Audit & Baseline Verification
- Verify backend DDD architecture, database connection, Alembic setup, FastAPI dependencies, JWT security, and PaymentProvider infrastructure.
- Validate git branch `feature/regie-publicitaire-visiteurs` and tag `baseline-regie-publicitaire-visiteurs`.
- Produce `POLICY.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`, and Phase 0 artifact `phase0_audit_and_plan.md`.

### Phase 1: Data Model, Immutable Wallet Engine & Alembic Migration (`0005_regie_publicitaire_visiteurs.py`)
- Implement domain models in `backend/src/monetization_context/infrastructure/persistence/models.py`:
  - `AdvertiserModel` & `AdvertiserUserModel`
  - `AdWalletModel` & `WalletTransactionModel`
  - `AdCampaignModel` & `AdTargetingRuleModel`
  - `AdCreativeModel` & `AdReviewEventModel`
  - `AdImpressionRawModel` & `AdStatsDailyModel`
  - `AdUserFeedbackModel` & `AdPolicyRuleModel`
- Write reversible Alembic migration `alembic/versions/0005_regie_publicitaire_visiteurs.py` with `upgrade()` and `downgrade()`.
- Implement immutable prepaid wallet domain service (`AdWalletService`): deposits, atomic delivery debits, refunds, balance integrity assertion (`sum(transactions) == balance_xaf`).
- **Validation Gate R10**: Unit test for concurrent wallet debits and transaction journal consistency (`tests/unit/test_ad_wallet_engine.py`).

### Phase 2: Moderation Workflow, Automated Policy & Creative Review
- Implement `AdPolicyEngine`: keyword blacklist, URL protocol validation, prohibited categories.
- Implement `CreativeReviewService`: `PENDING_REVIEW` -> `APPROVED` / `REJECTED` state transitions with review event logging.
- Implement image security processing (file extension validation, MIME check, size limit, EXIF metadata stripping).
- **Validation Gate R3 & R6**: Unit test for unapproved creative exclusion and malicious target URL rejection (`tests/unit/test_ad_moderation_and_policy.py`).

### Phase 3: Visitor Ad Delivery Engine, Pacing & Frequency Capping
- Implement `AdDeliveryEngine` in `backend/src/monetization_context/domain/services/ad_delivery_engine.py`:
  - Server-side active membership check (`has_active_membership` -> returns empty list `[]` for school members).
  - Visitor targeting rule evaluation (city/region, language, device, hour).
  - Pacing budget calculations (`hourly_budget = daily_budget_xaf / 24`).
  - Session frequency capping (max N impressions per session/creative).
  - Weighted priority auction (effective CPM/CPC ranking + exploration). No consecutive creatives from same campaign.
- **Validation Gate R1, R2, R4, R7, R8**: Unit test for server-side school member exclusion, visitor targeting, budget exhaustion auto-stop, frequency capping, and pacing (`tests/unit/test_ad_delivery_engine.py`).

### Phase 4: Impression/Click Tracking, Signed Tokens & Daily Aggregation
- Implement `AdTokenService`: HMAC-signed single-use impression & click tokens.
- Implement `GET /api/v1/ads/click/{token}`: server-side token validation, single-click tracking, open-redirect prevention (strict protocol & domain whitelist check).
- Implement `AdStatsAggregatorService`: rolls up raw impressions/clicks into `ad_stats_daily`.
- **Validation Gate R5 & R12**: Unit test for single-use token replay prevention and daily stats rollup accuracy (`tests/unit/test_ad_tracking_and_aggregation.py`).

### Phase 5: Self-Service Advertiser Workspace API & Payment Top-Up
- Implement `AdvertiserRouter` (`backend/src/api/v1/advertiser_router.py`):
  - Advertiser registration & profile management.
  - Wallet top-up via `PaymentProvider` integration.
  - Campaign creation wizard (objective, billing model, budget, targeting).
  - Creative submission, status tracking, pause/resume.
  - Advertiser analytics report with CSV export endpoint.
- **Validation Gate R9**: Unit test for IDOR security protection (Advertiser A cannot view/modify Advertiser B's campaign) (`tests/unit/test_advertiser_workspace_security.py`).

### Phase 6: Platform Admin Console, User Feedback & Anti-Fraud
- Implement `AdminAdConsoleRouter`:
  - Moderation queue endpoint (list pending, approve, reject with standard reason).
  - User feedback handling (`GET /api/v1/ads/feedback`): reporting, hiding.
  - Automatic suspension trigger (> 5 flags triggers auto-pause) (**Gate R11**).
  - Wallet manual adjustment endpoint with mandatory audit log.
- **Validation Gate R11**: Unit test for high-flag auto-suspension trigger (`tests/unit/test_ad_feedback_and_antifraud.py`).

### Phase 7: Visitor UI, i18n & Final Verification
- Refactor visitor feed components, ad card display with "Sponsorisé" badge, "Pourquoi cette annonce ?", "Masquer / Signaler" dialog.
- Update frontend API endpoints in `frontend/src/lib/api/endpoints.ts`.
- Run full pytest test suite, verify clean Alembic migration state, produce `FINAL_REPORT.md` and complete artifact summary.
