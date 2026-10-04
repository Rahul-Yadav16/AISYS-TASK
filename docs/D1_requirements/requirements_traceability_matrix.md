# Deliverable D1: Requirements Traceability Matrix (RTM)

This matrix maps every functional requirement (FR 01 to FR 12), non-functional requirement (NFR 01 to NFR 09), and priority acceptance scenario (AC 01 to AC 10) to corresponding architectural modules, API endpoints, source files, and automated test suites.

---

## 1. Functional Requirements Traceability (FR 01 to FR 12)

| Req ID | Requirement Description | Implementation Module & Layer | API / Service Endpoint | Test Suite / Evidence | Status |
|---|---|---|---|---|---|
| **FR 01** | Core ILMS: acquisition, cataloguing, serials, circulation, OPAC, barcode/spine labels, reporting | Application / Data Layer: `CataloguingService`, `CirculationService` | `POST /api/catalog/items`, `GET /api/catalog/spine-label/{id}`, `GET /api/reports/circulation` | `tests/test_core_ilms.py` | Complete |
| **FR 02** | Web & search: Web UI, full-text search, real-time indexing, net cataloguing, virtual bookshelf | Application & User Layer: `SearchService` (SQLite FTS5), `src/static/` | `GET /api/catalog/search`, `GET /api/catalog/bookshelf`, `POST /api/catalog/net-catalogue` | `tests/test_core_ilms.py` | Complete |
| **FR 03** | RFID interoperability: staff station, handheld, gate, smart card, NCIP 2.0 & SIP2 boundary | RFID Middleware & Interoperability: `RFIDManager`, `NCIPAdapter`, `SIP2Adapter` | `POST /api/rfid/read`, `POST /api/ncip/v2`, `POST /api/sip2/message` | `tests/test_rfid_middleware.py`, `tests/test_ncip_sip2.py` | Complete |
| **FR 04** | Circulation: check-out, check-in, renewal, member blocking, fine limits, role-based circulation rights | Application Layer: `CirculationService`, `FinesService`, `SecurityService` | `POST /api/circulation/checkout`, `POST /api/circulation/checkin`, `POST /api/circulation/renew` | `tests/test_circulation_and_fines.py` | Complete |
| **FR 05** | Tagging: validate title/member, associate RFID tag with item/member, tag monitoring | RFID Middleware & Application Layer: `StaffStationService`, `RFIDManager` | `POST /api/rfid/tag-item`, `POST /api/rfid/tag-member`, `GET /api/rfid/tags` | `tests/test_rfid_middleware.py` | Complete |
| **FR 06** | Inventory: stock verification, shelf management, missing/misplaced detection, handheld audible/visible events | RFID Middleware & Application Layer: `InventoryService`, `HandheldReader` | `POST /api/inventory/audit`, `POST /api/inventory/scan-burst`, `GET /api/inventory/{id}/report` | `tests/test_rfid_middleware.py` | Complete |
| **FR 07** | Security gate events: unauthorized item alarm, offline EAS reading, accession logging, CCTV photo, email notification | RFID Middleware & Integration: `SecurityGateService`, `CameraAdapter`, `NotificationAdapter` | `POST /api/gate/event`, `GET /api/gate/events`, `GET /api/gate/cctv/{filename}` | `tests/test_security_gate_events.py` | Complete |
| **FR 08** | Dashboard & reports: tagged items, members, circulation turnover, operators, RFID clients, gate events | Application Layer: `ReportService` | `GET /api/reports/dashboard`, `GET /api/reports/gate-events`, `GET /api/reports/operators` | `tests/test_core_ilms.py` | Complete |
| **FR 09** | Notifications: configurable email, SMS, print notifications via provider-neutral adapters | Integration Layer: `NotificationAdapter` | `POST /api/notifications/queue`, `GET /api/notifications/outbox` | `tests/test_circulation_and_fines.py` | Complete |
| **FR 10** | Data migration: import ~20,000 spreadsheet records, validation, duplicate handling, reconciliation, rollback | Data Layer & Migration Service: `MigrationService` | `POST /api/migration/upload`, `POST /api/migration/validate`, `POST /api/migration/commit`, `POST /api/migration/rollback` | `tests/test_data_migration_20k.py` | Complete |
| **FR 11** | Administration: user & role management, system configuration, audit logs, software versioning, system health | Operations & Application Layer: `AdminService`, `AuditService` | `GET /api/admin/health`, `GET /api/admin/audit-logs`, `GET /api/admin/version`, `POST /api/admin/users` | `tests/test_security_and_audit.py` | Complete |
| **FR 12** | Offline lifecycle: offline activation, updates, patches, installable update package with rollback instructions | Operations Layer: `tools/offline_installer.py`, `tools/offline_updater.py` | CLI & `POST /api/admin/apply-update`, `POST /api/admin/rollback-update` | `tests/test_offline_update_rollback.py` | Complete |

---

## 2. Non-Functional Requirements Traceability (NFR 01 to NFR 09)

| Req ID | Requirement Summary | Implementation Approach | Evidence / Artifact |
|---|---|---|---|
| **NFR 01** | Data integrity & non-destructive integration | Zero `DROP`/corrupt legacy records; automated pre-migration hot backup; staging schema; rollback | `src/services/migration_service.py`, `tests/test_backup_restore_resilience.py` |
| **NFR 02** | Security, privacy & least privilege | RBAC (`ADMIN`, `LIBRARIAN`, `CATALOGUER`, `CIRCULATION`), PBKDF2 hashing, audit logging, input validation | `src/core/security.py`, `src/core/audit.py`, `tests/test_security_and_audit.py` |
| **NFR 03** | Compatibility (Win 11 / Server 2022 / Isolated LAN) | Pure Python 3.12, zero-install SQLite, local static HTML5/ES6, no external internet needed | `scripts/run_dev.ps1`, `docs/D7_deployment/environment_checklist.md` |
| **NFR 04** | Licensing & pinned dependencies | Pinned `requirements.txt`, Software Bill of Materials with licenses and offline distribution notes | `requirements.txt`, `SBOM.json`, `LICENSE` |
| **NFR 05** | Testability | Automated test suite covering functional, integration, performance, migration, security, and rollback | `tests/`, Pytest automated test run |
| **NFR 06** | Maintainability | Layered architecture, versioned SQL migrations (`data/migrations/`), external JSON config, structured JSON logs | `config/sample_config.json`, `data/migrations/`, `src/core/logger.py` |
| **NFR 07** | Supportability | Health check endpoint (`/api/admin/health`), structured JSON logs, diagnostic runbooks | `docs/D8_operational/troubleshooting_runbook.md` |
| **NFR 08** | Documentation | Comprehensive D1 to D9 markdown packages, API documentation (Swagger/OpenAPI), runbooks | `docs/D1_requirements/` through `docs/D9_demonstration/` |
| **NFR 09** | Delivery lifecycle | SOP compliance D0 to D10; feature branch Git workflow; clear verification evidence | Git commit history, tagged release, complete acceptance report |

---

## 3. Priority Acceptance Scenarios Traceability (AC 01 to AC 10)

| Acceptance ID | Scenario Summary | Code Location | Test Suite Verification | Verification Status |
|---|---|---|---|---|
| **AC 01** | Import supplied spreadsheet into staging, reject invalid rows, detect duplicates, migrate valid records, reconcile counts | `src/services/migration_service.py` | `tests/test_data_migration_20k.py::test_migration_20k_reconciliation` | Verified |
| **AC 02** | Create/locate bib item, validate, associate mock RFID tag, display tag-to-item relationship | `src/middleware/staff_station.py` | `tests/test_rfid_middleware.py::test_tag_association_and_query` | Verified |
| **AC 03** | Check out, renew, check in through mocked NCIP or SIP2 flow preserving auditable history | `src/adapters/ncip_adapter.py`, `src/adapters/sip2_adapter.py` | `tests/test_ncip_sip2.py::test_sip2_and_ncip_checkout_checkin` | Verified |
| **AC 04** | Block circulation for reference item, blocked member, or fine exceeding configurable limit | `src/services/circulation_service.py` | `tests/test_circulation_and_fines.py::test_circulation_restrictions` | Verified |
| **AC 05** | Handheld-reader mock shelf inventory, report missing & misplaced items with visible & audible confirmation | `src/middleware/handheld_reader.py`, `src/static/js/audio.js` | `tests/test_rfid_middleware.py::test_handheld_inventory_misplaced_and_missing` | Verified |
| **AC 06** | Unauthorized removal event from gate mock, record accession number, attach mock CCTV image, queue email | `src/middleware/security_gate.py`, `src/adapters/camera_adapter.py` | `tests/test_security_gate_events.py::test_gate_alarm_cctv_and_email_flow` | Verified |
| **AC 07** | Staff smart-card login through mock credential provider and enforce role-based permissions | `src/middleware/smart_card.py`, `src/core/security.py` | `tests/test_security_and_audit.py::test_smart_card_rbac_login` | Verified |
| **AC 08** | Generate dashboard statistics and filterable reports for tagged items, members, circulation, operators, gate events | `src/services/report_service.py` | `tests/test_core_ilms.py::test_dashboard_and_filterable_reports` | Verified |
| **AC 09** | Install & run without internet access, apply offline update package, complete documented rollback | `tools/offline_installer.py`, `tools/offline_updater.py` | `tests/test_offline_update_rollback.py::test_offline_update_and_rollback` | Verified |
| **AC 10** | Restore from backup after simulated failed migration or integration change and prove original data remains intact | `tools/db_backup_restore.py`, `src/services/migration_service.py` | `tests/test_backup_restore_resilience.py::test_restore_after_failed_migration` | Verified |
