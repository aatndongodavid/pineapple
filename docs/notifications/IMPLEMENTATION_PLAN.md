# Implementation Plan - Master Prompt 04: Notifications Multicanal

## Architecture Overview & Hexagonal Strategy
The Unified Multi-channel Notification System follows a transactional Outbox pattern to guarantee event publication reliability without blocking HTTP request execution.

```
+-------------------------------------------------------------------------------+
|                             DOMAINS / BOUNDED CONTEXTS                        |
| (Academy, Identity, Monetization, Democracy, Community, Class Delegates)       |
+-------------------------------------------------------------------------------+
                                    |
                    Write Business State & Domain Event
                                    v
                       +-------------------------+
                       |      outbox_events      | (Same DB Transaction)
                       +-------------------------+
                                    |
                         Async Outbox Worker
                                    v
+-------------------------------------------------------------------------------+
|                            NOTIFICATION CONTEXT                               |
|                                                                               |
|  1. Audience Resolver -> 2. Preference Engine -> 3. Template Engine           |
|                                                                               |
|                            4. Deduplication & Digest                          |
|                                                                               |
|                            5. Channel Dispatchers                             |
|       +--------------+------------+------------+---------------+              |
|       |              |            |            |               |              |
|       v              v            v            v               v              |
|   InApp/WS        Web Push       Email        SMS           WhatsApp          |
|  (WebSocket)      (VAPID)       (SMTP)    (Provider/Mock) (Simulated/API)     |
+-------------------------------------------------------------------------------+
```

---

## Data Model Specifications (`notification_context`)

1. `outbox_events`:
   - `id`: UUID (PK)
   - `tenant_id`: UUID (FK tenants.id)
   - `event_type`: String(100) (ex: `CLASS_ANNOUNCEMENT_PUBLISHED`, `COURSE_CANCELLED`, `MEMBERSHIP_CLAIM_REVIEWED`, `SECURITY_ALERT`)
   - `payload`: JSONB (versioned payload)
   - `status`: Enum (`PENDING`, `PROCESSING`, `PROCESSED`, `FAILED`)
   - `attempts`: Integer (default 0)
   - `last_error`: Text
   - `created_at`: DateTime(timezone=True)
   - `processed_at`: DateTime(timezone=True)

2. `notification_templates`:
   - `id`: UUID (PK)
   - `tenant_id`: UUID (nullable for system defaults)
   - `code`: String(100) (ex: `template.class_announcement`, `template.course_cancelled`)
   - `channel`: Enum (`IN_APP`, `PUSH`, `EMAIL`, `SMS`, `WHATSAPP`)
   - `language`: String(10) (`fr` default, `en`)
   - `subject_template`: String(255)
   - `body_template`: Text (supports variable interpolation `{{ user.first_name }}`, `{{ course.name }}`)
   - `version`: Integer (default 1)
   - `is_active`: Boolean (default True)

3. `notifications`:
   - `id`: UUID (PK)
   - `tenant_id`: UUID (FK tenants.id)
   - `user_id`: UUID (FK users.id)
   - `category`: Enum (`CRITICAL`, `IMPORTANT`, `INFO`)
   - `criticality`: Enum (`CRITICAL`, `IMPORTANT`, `INFO`)
   - `title`: String(255)
   - `body`: Text
   - `deep_link`: String(500) (ex: `/timetable`, `/finance/invoices/123`)
   - `read_at`: DateTime(timezone=True) (nullable)
   - `created_at`: DateTime(timezone=True)
   - `dedup_key`: String(255) (unique composite: `event_type:user_id:channel:window`)

4. `notification_deliveries`:
   - `id`: UUID (PK)
   - `notification_id`: UUID (FK notifications.id)
   - `channel`: Enum (`IN_APP`, `PUSH`, `EMAIL`, `SMS`, `WHATSAPP`)
   - `status`: Enum (`QUEUED`, `SENT`, `DELIVERED`, `FAILED`, `SKIPPED`, `DEAD_LETTER`)
   - `skipped_reason`: String(255) (nullable: `DISABLED_BY_USER`, `QUIET_HOURS`, `QUOTA_EXCEEDED`, `NO_SMS_CONSENT`)
   - `provider_name`: String(100)
   - `provider_ref`: String(255)
   - `attempts`: Integer (default 0)
   - `last_error`: Text
   - `created_at`: DateTime(timezone=True)
   - `updated_at`: DateTime(timezone=True)

5. `notification_preferences`:
   - `id`: UUID (PK)
   - `user_id`: UUID (FK users.id)
   - `tenant_id`: UUID (FK tenants.id)
   - `category`: String(50)
   - `channel`: String(50)
   - `is_enabled`: Boolean (default True)
   - `updated_at`: DateTime(timezone=True)

6. `quiet_hours`:
   - `id`: UUID (PK)
   - `user_id`: UUID (FK users.id)
   - `tenant_id`: UUID (FK tenants.id)
   - `start_hour`: Integer (0-23, default 21)
   - `end_hour`: Integer (0-23, default 6)
   - `is_enabled`: Boolean (default False)
   - `updated_at`: DateTime(timezone=True)

7. `push_subscriptions`:
   - `id`: UUID (PK)
   - `user_id`: UUID (FK users.id)
   - `tenant_id`: UUID (FK tenants.id)
   - `endpoint`: Text (unique)
   - `p256dh`: Text
   - `auth`: Text
   - `user_agent`: String(255)
   - `is_active`: Boolean (default True)
   - `created_at`: DateTime(timezone=True)
   - `revoked_at`: DateTime(timezone=True)

8. `channel_quotas`:
   - `id`: UUID (PK)
   - `tenant_id`: UUID (FK tenants.id)
   - `channel`: String(50)
   - `period`: String(20) (`MONTHLY`, `DAILY`)
   - `max_limit`: Integer
   - `current_usage`: Integer (default 0)
   - `updated_at`: DateTime(timezone=True)

9. `broadcasts`:
   - `id`: UUID (PK)
   - `tenant_id`: UUID (FK tenants.id)
   - `author_id`: UUID (FK users.id)
   - `audience_type`: Enum (`TENANT_ALL`, `CLASS_GROUP`)
   - `class_group_id`: UUID (nullable)
   - `category`: String(50)
   - `title`: String(255)
   - `body`: Text
   - `deep_link`: String(500)
   - `status`: Enum (`DRAFT`, `PENDING`, `SENT`, `FAILED`)
   - `target_count`: Integer
   - `created_at`: DateTime(timezone=True)
   - `sent_at`: DateTime(timezone=True)

---

## Phase Execution Plan & Gate Criteria

### Phase 0: Audit, Environment & Providers Setup
- Audit existing events, database fixtures, `docker-compose.yml`, WebSocket manager.
- Create documentation: `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`, `PROVIDERS.md`.
- Produce Phase 0 artifact.

### Phase 1: Database Schema & Migration (`0004_notifications_multicanal.py`)
- Define SQLAlchemy models in `backend/src/notification_context/infrastructure/persistence/models.py`.
- Create Alembic migration script `alembic/versions/0004_notifications_multicanal.py`.
- **Validation Gate M4 & M5**: Test outbox persistence transaction & worker crash resilience (`tests/unit/test_outbox_worker.py`).

### Phase 2: Preference Engine, Template Renderer & Deduplication
- Implement `AudienceResolver` (tenant, class_group, single user).
- Implement `PreferenceEngine` (category x channel matrix, quiet hours check, `CRITICAL` bypass rules, SMS consent, quota check).
- Implement `TemplateRenderer` (Jinja2 / string format, French/English localization).
- Implement `DeduplicationEngine` (dedup_key & short-window digest).
- **Validation Gate M2, M3, M6, M10**: Unit tests for user preference disabling, quiet hours delay, SMS quota skipping & digest grouping (`tests/unit/test_notification_preferences_and_digest.py`).

### Phase 3: Channels Implementation (In-App, WebSocket & Email)
- `InAppChannelAdapter`: DB notification creation & real-time WebSocket push (`ws_manager`).
- `EmailGatewayAdapter`: HTML + text template rendering, `List-Unsubscribe` header, unsubscribe token handler.
- **Validation Gate M1, M9**: Test class announcement audience delivery & one-click email unsubscribe (`tests/unit/test_notification_channels.py`).

### Phase 4: Web Push VAPID Channel & Service Worker Integration
- `WebPushChannelAdapter`: VAPID key generation, encryption payload, `410 Gone` expired subscription auto-cleanup.
- Integration in Service Worker (`sw-custom.js`) & Web Push registration endpoint.
- **Validation Gate M7**: Test Web Push 410 expired token auto-revocation (`tests/unit/test_web_push.py`).

### Phase 5: SMS Channel & WhatsApp Adapter
- `SmsGatewayAdapter`: SMS consent check, 160 char limit, tenant SMS quota tracking, simulated provider for dev/test.
- `WhatsAppChannelAdapter`: Simulated adapter behind port with `TODO(externe)`.
- **Validation Gate M6**: Test SMS quota enforcement & fallback to Email/Push.

### Phase 6: Broadcasts System & Business Domain Event Triggers
- `BroadcastService`: Admin all-tenant broadcast vs Delegate single class broadcast (`IMPORTANT` category, max 5/day per delegate, permission check `class.announce`).
- Wire domain events to Outbox: Class announcements, Timetable exceptions, Membership claims, Invoices due, Security alerts, Election results.
- **Validation Gate M8**: Test delegate broadcast authorization restriction (`tests/unit/test_broadcasts_and_security.py`).

### Phase 7: Frontend Center, Preference Matrix & Admin Analytics UI
- Refactor `NotificationCenter` (list, unread count badge, category filters, deep-link navigation, PWA offline cache).
- `NotificationPreferencesPage`: Category x Channel matrix, quiet hours picker, SMS consent toggle.
- `AdminNotificationDashboard`: Analytics (sent/delivered/failed/skipped), SMS quota gauge, Dead-Letter retry queue.
- Regenerate OpenAPI TypeScript types (`npm run gen:api`).

### Phase 8: Load Testing, Security Audit & Final Report
- High-throughput load test (>= 500 notifications/min).
- PII masking audit in logs & multi-tenant isolation test (**Gate M11**).
- Final documentation report `docs/notifications/FINAL_REPORT.md`.
