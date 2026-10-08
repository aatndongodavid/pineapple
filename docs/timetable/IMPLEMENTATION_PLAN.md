# Implementation Plan - Master Prompt 03: Emploi du Temps et Gestion Intelligente des Salles

## 1. Overview & Objectives

The goal of this module is to provide a complete, robust, offline-capable, real-time Timetable & Room Management system tailored for higher education in Cameroon (local time `Africa/Douala`, zero-decimal XAF currency, low-bandwidth mobile optimization).

Key requirements:
1. **Weekly Recurrence Model + Exceptions (T1)**: Weekly rules computed via `rrule` / dateutil logic. Targeted exceptions stored separately (`CANCELLED`, `MOVED`, `ROOM_CHANGED`, `TEACHER_CHANGED`).
2. **UTC in DB, `Africa/Douala` display & wall-clock representation (T2)**.
3. **Room Availability Priority Rule (T3)**:
   1. Active delegate declaration (`room_status_declarations`, unexpired)
   2. Approved room reservation (`room_reservations`, status=APPROVED)
   3. Scheduled course occurrence (`timetable_rules` active for day & time, unless exception CANCELLED)
   4. Default `FREE`
   *Note*: A delegate "FREE" declaration during a scheduled course is shown as "announced free by delegate" (course not held), not absolute certainty.
4. **Blocking Conflict Detection (T4)**: Double booking of room, teacher, or class group blocked on creation/update, unless explicit admin override with audit log motif.
5. **Role-Based Workflows (T5)**: Admins/Staff modify schedules (`admin.timetable.manage`). Teachers submit change requests (`timetable_change_requests`) for admin approval.
6. **ICS Calendar Subscription**: Public secret tokens per user/class with revocable access (`/api/v1/timetable/ics/{token}.ics`).
7. **Offline Support & Student UI**: "Mon Emploi du Temps" (day/week view), "Prochain Cours" widget, "Où est ma salle ?", PWA offline cache.
8. **Delegate Incident Integration**: Admin can convert a validated delegate incident (`class_incidents`) into a `timetable_exception`.
9. **Admin Statistics & Analytics**: Precomputed room utilization heatmaps, underused rooms, cancellation metrics, teacher workload.

---

## 2. Architecture & Data Model Design (Bounded Context: `academy_context`)

### Database Schemas & Models (Alembic Migration 0003_timetable_and_rooms.py)
- **`academic_terms`**: `id`, `tenant_id`, `name` (e.g. "Semestre 1 2026-2027"), `academic_year`, `start_date`, `end_date`, `is_active`, timestamps.
- **`calendar_exceptions`**: `id`, `tenant_id`, `term_id`, `title`, `exception_type` (`HOLIDAY`, `VACATION`, `EXAM_PERIOD`), `start_date`, `end_date`, timestamps.
- **`subjects`**: `id`, `tenant_id`, `code` (e.g. "INF301"), `name` ("Algorithmique & Data Structures"), `credits`, timestamps.
- **`course_offerings`**: `id`, `tenant_id`, `term_id`, `subject_id`, `class_group_id`, `teacher_id` (FK users.id), `color_code`, timestamps.
- **`timetable_rules`**: `id`, `tenant_id`, `course_offering_id`, `room_id`, `day_of_week` (0=Monday..6=Sunday), `start_time` (Time), `end_time` (Time), `start_date` (Date), `end_date` (Date), `recurrence_rule` (RRULE string, default FREQ=WEEKLY), timestamps.
- **`timetable_exceptions`**: `id`, `tenant_id`, `rule_id`, `target_date` (Date), `exception_type` (`CANCELLED`, `MOVED`, `ROOM_CHANGED`, `TEACHER_CHANGED`), `new_room_id`, `new_teacher_id`, `new_start_time`, `new_end_time`, `reason`, `author_id`, timestamps.
- **`room_features`**: `id`, `tenant_id`, `room_id`, `feature_name` (e.g. "PROJECTOR", "AC", "POWER_OUTLETS", "COMPUTERS"), `quantity`.
- **`room_reservations`**: `id`, `tenant_id`, `room_id`, `requester_id`, `title`, `purpose`, `reservation_date` (Date), `start_time` (Time), `end_time` (Time), `status` (`PENDING`, `APPROVED`, `REJECTED`), `approved_by_id`, `rejection_reason`, timestamps.
- **`timetable_change_requests`**: `id`, `tenant_id`, `teacher_id`, `rule_id`, `target_date`, `requested_type`, `proposed_room_id`, `proposed_start_time`, `proposed_end_time`, `reason`, `status` (`PENDING`, `APPROVED`, `REJECTED`), timestamps.
- **`ics_tokens`**: `id`, `tenant_id`, `user_id`, `class_group_id`, `token` (String unique index), `is_revoked`, `created_at`, `revoked_at`.

### Overlap & Concurrency Control
- PostgreSQL transactional locking `SELECT ... FOR UPDATE` on room, teacher, and class_group when inserting/updating timetable rules & reservations, combined with SQLAlchemy validation services.
- Database index on `(tenant_id, room_id, day_of_week)` and `(tenant_id, course_offering_id)`.

---

## 3. Domain Services & Application Logic

1. **`ConflictDetectorService`** (Pure Domain Service):
   - Given a rule or reservation proposal (room, teacher, class_group, day_of_week, start_time, end_time, start_date, end_date), checks for overlaps against existing rules, exceptions, and approved reservations.
   - Generates exact conflict descriptions and smart alternatives ("Free room at same time: B12", "Teacher free window: ...").
   - Property-based tests (`hypothesis`) for symmetry, self-conflict freedom, and deterministic output.
2. **`RecurrenceEngine`**:
   - Computes effective occurrences for any given date range `[start_date, end_date]`.
   - Filters out calendar holiday exceptions.
   - Applies targeted `timetable_exceptions` (replacing room, teacher, time, or marking cancelled).
3. **`RoomAvailabilityService`**:
   - Evaluates priority T3: Delegate Declaration > Approved Reservation > Scheduled Course > Free.
   - Cached in Redis (30s TTL), invalidated on rule/exception/reservation/declaration updates.
   - Publishes WebSocket events on status changes.
4. **`NotificationPublisher` Port**:
   - Decoupled interface for schedule updates (in-app adapter for now, ready for future notification service).
5. **`ICSExportService`**:
   - Generates RFC 5545 valid `.ics` streams with timezone `Africa/Douala`, user/class filtering, secret token validation (404 on revoked).

---

## 4. Phased Execution Plan & Validation Gates

- **Phase 0**: Pre-flight audit & planning artifacts creation (`IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`).
- **Phase 1**: Database schema, models & Alembic migration `0003_timetable_and_rooms.py` (*Gate E3*: Concurrency test).
- **Phase 2**: Core domain logic, recurrence engine, conflict detector & exceptions (*Gates E1, E2*, `hypothesis` tests).
- **Phase 3**: REST API endpoints, CSV/XLSX import with dry-run, room reservations & teacher change requests (*Gate E4*).
- **Phase 4**: Real-time room availability calculation, priority T3 engine, Redis caching & WebSocket broadcasting (*Gate E6*).
- **Phase 5**: Frontend UI (Admin Timetable Grid, Student/Teacher Schedule, ICS Export, Offline PWA mode) (*Gates E7, E8, E9*).
- **Phase 6**: Admin Statistics, Security Audit, Hardening & Final Documentation (*Gate E10*).

---

## 5. Verification Matrix & Acceptance Test Mapping

| Acceptance Test | Description | Verification Method |
|---|---|---|
| **E1** | Creation of course without conflict | Unit test checking generated occurrences across term excluding holidays |
| **E2** | Two courses in same room/slot | Unit test verifying conflict rejection with suggestions, admin override audit |
| **E3** | Concurrent requests for same slot | Async concurrency test verifying database lock prevents duplicate booking |
| **E4** | CSV Import with conflicts | API test verifying dry-run error report and clean partial/valid import |
| **E5** | Occurrence cancellation | Test verifying occurrence hidden for class and room freed for that date |
| **E6** | Delegate room declaration during free slot | Test verifying T3 priority output and automatic expiration |
| **E7** | Offline schedule viewing | Frontend PWA test checking Zustand offline persistent cache & banner |
| **E8** | ICS Stream export | Test parsing `.ics` output in `Africa/Douala` timezone |
| **E9** | ICS Token revocation | Test verifying revoked token returns 404 |
| **E10**| Multi-tenant isolation & permission matrix | Security test suite checking role matrix (admin, staff, teacher, student, delegate) |
