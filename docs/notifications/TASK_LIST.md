# Task List - Master Prompt 04: Notifications Multicanal

- [x] **Phase 0: Audit & Planning**
  - [x] Verify baseline environment (FastAPI, SQLAlchemy async, PostgreSQL/SQLite, Alembic, JWT, permissions, Redis, Frontend React/TS/Zustand)
  - [x] Create git branch `feature/notifications-multicanal` and git tag `baseline-notifications-multicanal`
  - [x] Produce `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`, and `PROVIDERS.md`
  - [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`

- [x] **Phase 1: Database Schema & Migration (`0004_notifications_multicanal.py`)**
  - [x] Implement database models in `backend/src/notification_context/infrastructure/persistence/models.py`:
    - `OutboxEventModel`
    - `NotificationTemplateModel`
    - `NotificationModel`
    - `NotificationDeliveryModel`
    - `NotificationPreferenceModel`
    - `QuietHoursModel`
    - `PushSubscriptionModel`
    - `ChannelQuotaModel`
    - `BroadcastModel`
  - [x] Create Alembic migration script `alembic/versions/0004_notifications_multicanal.py` with `upgrade()` and `downgrade()`
  - [x] Implement Outbox Worker (`backend/src/notification_context/worker.py`) & Docker compose `worker` service
  - [x] **Validation Gate M4 & M5**: Test Outbox persistence transaction & Worker crash resilience (`tests/unit/test_outbox_worker.py`)

- [x] **Phase 2: Preference Engine, Template Renderer & Deduplication**
  - [x] Implement `AudienceResolver` (tenant, class group, single user)
  - [x] Implement `PreferenceEngine` (category x channel matrix, quiet hours check, `CRITICAL` bypass, SMS consent, quota check)
  - [x] Implement `TemplateRenderer` (Jinja2 / string format, French/English localization)
  - [x] Implement `DeduplicationEngine` (dedup_key & short-window digest)
  - [x] **Validation Gate M2, M3, M6, M10**: Unit tests for user preferences disabling, quiet hours delay, SMS quota skipping & digest grouping (`tests/unit/test_notification_preferences_and_digest.py`)

- [x] **Phase 3: Channels Implementation (In-App, WebSocket & Email)**
  - [x] Implement `InAppChannelAdapter`: DB notification creation & real-time WebSocket push (`ws_manager`)
  - [x] Implement `EmailGatewayAdapter`: HTML + text template rendering, `List-Unsubscribe` header, unsubscribe token handler
  - [x] **Validation Gate M1, M9**: Test class announcement audience delivery & one-click email unsubscribe (`tests/unit/test_notification_channels.py`)

- [x] **Phase 4: Web Push VAPID Channel & Service Worker Integration**
  - [x] Implement `WebPushChannelAdapter`: VAPID key generation, payload encryption, `410 Gone` expired subscription auto-cleanup
  - [x] Integration in Service Worker (`sw-custom.js`) & Web Push registration endpoint
  - [x] **Validation Gate M7**: Test Web Push 410 expired token auto-revocation (`tests/unit/test_web_push.py`)

- [x] **Phase 5: SMS Channel & WhatsApp Adapter**
  - [x] Implement `SmsGatewayAdapter`: SMS consent check, 160 char limit, tenant SMS quota tracking, simulated provider for dev/test
  - [x] Implement `WhatsAppChannelAdapter`: Simulated adapter behind port with `TODO(externe)`
  - [x] **Validation Gate M6**: Test SMS quota enforcement & fallback to Email/Push (`tests/unit/test_sms_and_whatsapp_adapters.py`)

- [x] **Phase 6: Broadcasts System & Business Domain Event Triggers**
  - [x] Implement `BroadcastService`: Admin all-tenant broadcast vs Delegate single class broadcast (`IMPORTANT` category, max 5/day per delegate, permission check `class.announce`)
  - [x] Wire domain events to Outbox: Class announcements, Timetable exceptions, Membership claims, Invoices due, Security alerts, Election results
  - [x] **Validation Gate M8**: Test delegate broadcast authorization restriction (`tests/unit/test_broadcasts_and_security.py`)

- [x] **Phase 7: Frontend Center, Preference Matrix & Admin Analytics UI**
  - [x] Refactor `NotificationCenter` (list, unread count badge, category filters, deep-link navigation, PWA offline cache)
  - [x] Implement `NotificationPreferencesPage`: Category x Channel matrix, quiet hours picker, SMS consent toggle
  - [x] Implement `AdminNotificationDashboard`: Analytics (sent/delivered/failed/skipped), SMS quota gauge, Dead-Letter retry queue
  - [x] Update API endpoints in `frontend/src/lib/api/endpoints.ts`

- [x] **Phase 8: Load Testing, Security Audit & Final Report**
  - [x] High-throughput load test (50 outbox messages batch processing)
  - [x] PII masking audit in logs & multi-tenant isolation test (**Gate M11**) (`tests/unit/test_notifications_load_and_pii.py`)
  - [x] Final documentation report `docs/notifications/FINAL_REPORT.md`
