# Deliverable D6: Automated and Manual Test Plan

## 1. Test Strategy and Objectives
The AISYS testing strategy guarantees full verification of functional requirements (FR 01 to FR 12), nonfunctional qualities (NFR 01 to NFR 09), and priority acceptance scenarios (AC 01 to AC 10) in an isolated, offline-ready test harness.

---

## 2. Test Classification Matrix

| Test Level | Scope | Tools / Framework | Automation Status |
|---|---|---|---|
| **Unit & Logic** | PBKDF2 hashing, RBAC permissions, SIP2 checksums, FTS5 queries | `pytest` | 100% Automated |
| **Functional & API** | Cataloguing, Circulation, Tagging, Members, Gate Events, Health | `pytest`, `httpx`, `FastAPI TestClient` | 100% Automated |
| **Interoperability** | 3M SIP2 frame protocols, NISO NCIP 2.0 XML & JSON adapters | `pytest`, `xml.etree` | 100% Automated |
| **Data Migration** | 20,000 record streaming ingestion, validation, duplicate handling, rollback | `pytest`, `src/services/migration_service.py` | 100% Automated |
| **Resilience & DR** | Hot backup, integrity check, simulated failure, restore verification | `pytest`, `tools/db_backup_restore.py` | 100% Automated |
| **Offline Lifecycle** | Pre-update snapshot, patch application, update rollback | `pytest`, `tools/offline_updater.py` | 100% Automated |
| **User Acceptance (UAT)** | Web user interface journeys, visible/audible confirmations | Browser SPA, Web Audio API, Mock Station | Manual & E2E Verified |

---

## 3. Test Environment Specifications
- **Operating System**: Windows 11 Enterprise (64-bit) / Windows Server 2022
- **Python Engine**: Python 3.12 64-bit
- **Database Engine**: SQLite 3.45+ with WAL mode and FTS5 enabled
- **Network Setting**: Disconnected / Localhost loopback (100% air-gapped verified)
- **Data Source**: 100% synthetic dataset (`data/sample_import_20000.csv`)
