# Task List - Master Prompt 03: Emploi du Temps et Gestion Intelligente des Salles

- [x] **Phase 0: Audit & Planning**
  - [x] Verify baseline environment (FastAPI, SQLAlchemy async, PostgreSQL/SQLite, Alembic, JWT, permissions, Redis, Frontend React/TS/Zustand)
  - [x] Run baseline pytest suite and fix pre-existing environment issues (`pytest.ini`)
  - [x] Create git branch `feature/timetable-rooms` and git tag `baseline-timetable-rooms`
  - [x] Produce `IMPLEMENTATION_PLAN.md` and `TASK_LIST.md`

- [x] **Phase 1: Modèle de Données & Migrations Alembic**
  - [x] Implement database models in `backend/src/academy_context/infrastructure/persistence/models.py`:
    - `AcademicTermModel`
    - `CalendarExceptionModel`
    - `SubjectModel`
    - `CourseOfferingModel`
    - `TimetableRuleModel`
    - `TimetableExceptionModel`
    - `RoomFeatureModel`
    - `RoomReservationModel`
    - `TimetableChangeRequestModel`
    - `IcsTokenModel`
  - [x] Create Alembic migration `0003_timetable_and_rooms.py` with `upgrade()` and `downgrade()`
  - [x] **Validation Gate E3**: Write and execute async concurrency test for simultaneous booking attempts

- [x] **Phase 2: Moteur de Récurrence, Exceptions et Détection de Conflits**
  - [x] Implement `RecurrenceEngine` (`rrule` dateutil) in `backend/src/academy_context/domain/services/recurrence_engine.py`
  - [x] Implement `ConflictDetectorService` in `backend/src/academy_context/domain/services/conflict_detector.py`
  - [x] Add suggestion engine (alternative free rooms, alternative time slots)
  - [x] Implement Property-Based Tests (`hypothesis`) for conflict detection
  - [x] **Validation Gate E1 & E2**: Test course occurrence generation excluding holidays; test double-booking rejection & admin override audit

- [x] **Phase 3: APIs REST, Import CSV/XLSX & Réservations**
  - [x] Implement DTOs and API router `backend/src/api/v1/timetable_router.py`
  - [x] Endpoints for Term, Subject, Course Offering, Timetable Rule CRUD
  - [x] CSV/XLSX import endpoint with dry-run report and downloadable sample template
  - [x] Teacher change request submission & approval workflow
  - [x] Room reservation endpoints (`PENDING/APPROVED/REJECTED`)
  - [x] Delegate incident to exception conversion endpoint
  - [x] **Validation Gate E4**: Test CSV import dry-run listing conflicts and partial valid import

- [x] **Phase 4: Disponibilité Temps Réel, Cache Redis & Notification Publisher**
  - [x] Implement priority engine T3 (Delegate declaration > Reservation > Scheduled course > Free) in `RoomAvailabilityService`
  - [x] Implement `GET /api/v1/timetable/rooms/availability` endpoint with filtering (duration, capacity, features)
  - [x] Implement Redis short cache (30s TTL) with instant invalidation on state changes
  - [x] Implement WebSocket room availability status broadcast in `RoomAvailabilityWebSocketManager`
  - [x] **Validation Gate E6**: Test delegate declaration priority & real-time WebSocket broadcasting (`test_room_availability_ws.py`)

- [x] **Phase 5: Interface Utilisateur & ICS Stream Export**
  - [x] Implement ICS Export Service & Router (`/api/v1/timetable/ics/{token}.ics`) with timezone `Africa/Douala`
  - [x] Implement ICS token generation & revocation (`IcsTokenModel`)
  - [x] **Validation Gates E7, E8, E9**: Test ICS calendar RFC 5545 parsing, Douala timezone, and token security (`test_timetable_ics_and_analytics.py`)

- [x] **Phase 6: Statistiques Admin, Sécurisation Multi-Tenant & Rapport Final**
  - [x] Implement admin analytics endpoints (`GET /api/v1/timetable/analytics/occupancy`)
  - [x] Verify multi-tenant isolation and security permission matrix across all endpoints
  - [x] Run full test suite (`pytest tests/unit/` -> 50/50 passing)
  - [x] **Validation Gate E10**: Complete multi-tenant permission matrix verification (`test_gate_e10_multitenant_isolation_and_analytics`)
