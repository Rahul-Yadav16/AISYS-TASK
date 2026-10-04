# AISYS RFID-Enabled Library Solution

An industrial-grade, RFID-enabled library management solution and middleware engine designed to integrate non-destructively with an existing Integrated Library Management Software (ILMS) system without changing, deleting, or corrupting existing records. Built strictly according to the AISYS Software Development SOP stages D0 through D10.

---

## 🌟 Key Highlights & Engineering Features

- **Non-Destructive Integration (NFR 01)**: Enforces read-only query boundaries (`PRAGMA query_only = ON;`) on existing ILMS databases, automated pre-change snapshots, and transactional staging isolation.
- **Controlled 20,000 Record Migration Utility (FR 10, AC 01)**: High-speed ingestion of spreadsheet datasets, row-level validation, duplicate detection against database keys, 100% transparent reconciliation reporting, and atomic one-click rollback.
- **RFID Middleware & Hardware Abstraction (FR 03, FR 05, FR 06, FR 07)**: Device-neutral event bus supporting Staff Stations, Handheld Wands, Security Gates, and Smart Card readers.
- **Offline Security Gate Resilience (FR 07, AC 06)**: Security gates independently inspect raw tag AFI/EAS bits (`0x00` = Armed, `0x01` = Disarmed) at the antenna plane even during network disconnection, triggering local sirens, accession logging, mock CCTV frame snapshots, and security email queues.
- **Ergonomic Audio/Visual Confirmations (FR 06, AC 05)**: Web Audio API tone synthesis emitting 880Hz confirmation chimes for valid items, 440Hz double pulses for misplaced shelf items, and 220Hz sirens for gate alarms without external audio files.
- **Interoperability (FR 03, AC 03)**: Standard 3M SIP2 frame processor (`11/12`, `09/10`, `29/30`, `63/64`, `99/98`) and NISO NCIP 2.0 XML/JSON service endpoints.
- **Strict Role-Based Access Control (NFR 02, AC 07)**: Salted PBKDF2 password hashing, immutable audit logging, and fast staff smart-card tap-login (`SC-ADMIN-001`, `SC-CIRC-004`).
- **Air-Gapped / Offline Lifecycle (FR 12, AC 09, NFR 03)**: 100% self-hosted static assets, pinned dependencies, pre-update snapshots, offline patch application, and automated rollback.

---

## 🏗️ 7-Layer Architecture Overview (SOP Section 6)

1. **User Layer**: Single-page web portal (Staff management, OPAC full-text search, virtual bookshelf, circulation desk, hardware simulator).
2. **Application Layer**: Cataloguing, circulation rule engine, member management, fines assessment, shelf inventory, and report generation.
3. **RFID Middleware Layer**: Device-neutral event bus, staff tag encoder, handheld inventory processor, security gate monitor, and smart card resolver.
4. **Interoperability Layer**: 3M SIP2 protocol parser and NISO NCIP 2.0 XML/JSON adapter.
5. **Data Layer**: Transactional SQLite 3 with Write-Ahead Logging (WAL), FTS5 full-text search engine, and migration staging area.
6. **Integration Layer**: Provider-neutral notification queues for Email, SMS, thermal receipt printing, and CCTV surveillance snapshots.
7. **Operations Layer**: Pinned dependencies, Software Bill of Materials (SBOM), health diagnostic probes, online hot backups, and offline updates.

---

## 🚀 Quick Start Guide

### 1. Launch the Application Server
Run using PowerShell:
```powershell
.\scripts\run_dev.ps1
```
Or using Command Prompt:
```cmd
scripts\run_dev.bat
```
Navigate to:
- **Web Application Portal**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI / Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Probe**: [http://localhost:8000/api/admin/health](http://localhost:8000/api/admin/health)

### 2. Run the Automated Test Suite (100% Pass Rate)
Execute all 20 automated tests verifying AC 01 to AC 10:
```powershell
.\scripts\run_tests.ps1
```
Or directly via pytest:
```powershell
.\.venv\Scripts\pytest -v
```

---

## 📋 Priority Acceptance Scenarios Verification (AC 01 to AC 10)

| ID | Acceptance Scenario | Verification Artifact & Evidence |
|---|---|---|
| **AC 01** | Import 20k spreadsheet into staging, reject invalid rows, detect duplicates, migrate valid records, reconcile counts | Verified by `tests/test_data_migration_20k.py` and Web UI Migration Wizard. |
| **AC 02** | Create/locate bib item, validate it, associate mock RFID tag, display tag-to-item relationship | Verified by `tests/test_rfid_middleware.py` and Web UI RFID Staff Station. |
| **AC 03** | Check out, renew, check in through mocked NCIP or SIP2 flow while preserving auditable history | Verified by `tests/test_ncip_sip2.py` and `src/adapters/sip2_adapter.py`. |
| **AC 04** | Block circulation for reference item, blocked member, or member whose fine exceeds limit | Verified by `tests/test_circulation_and_fines.py` and Circulation Desk. |
| **AC 05** | Handheld-reader mock shelf inventory, report missing & misplaced items with visible & audible confirmation | Verified by `tests/test_rfid_middleware.py` and Handheld Inventory Wand. |
| **AC 06** | Unauthorized removal event from gate mock, record accession number, attach mock CCTV image, queue email | Verified by `tests/test_security_gate_events.py` and Security Gate Monitor. |
| **AC 07** | Staff smart-card login through mock credential provider and enforce role-based permissions | Verified by `tests/test_security_and_audit.py` and Topbar Card Tap buttons. |
| **AC 08** | Generate dashboard statistics and filterable reports for tagged items, members, circulation, operators, gate events | Verified by `tests/test_core_ilms.py` and Dashboard view. |
| **AC 09** | Install & run without internet access, apply offline update package, complete documented rollback | Verified by `tests/test_offline_update_rollback.py` and `tools/offline_updater.py`. |
| **AC 10** | Restore from backup after simulated failed migration or change and prove original data remains intact | Verified by `tests/test_backup_restore_resilience.py` and `tools/db_backup_restore.py`. |

---

## 📂 Deliverable Package Directory Navigation

- **D1 Requirements Package**: [docs/D1_requirements/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D1_requirements/)
  - [assumptions_and_clarifications.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D1_requirements/assumptions_and_clarifications.md)
  - [use_cases.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D1_requirements/use_cases.md)
  - [data_dictionary.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D1_requirements/data_dictionary.md)
  - [requirements_traceability_matrix.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D1_requirements/requirements_traceability_matrix.md)
- **D2 Architecture Package**: [docs/D2_architecture/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/)
  - [context_and_component_design.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/context_and_component_design.md)
  - [deployment_and_isolated_network.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/deployment_and_isolated_network.md)
  - [database_schema_design.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/database_schema_design.md)
  - [interface_and_adapter_specs.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/interface_and_adapter_specs.md)
  - [security_and_privacy_controls.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D2_architecture/security_and_privacy_controls.md)
- **D6 Test Package**: [docs/D6_test_package/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D6_test_package/)
  - [test_plan.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D6_test_package/test_plan.md)
  - [test_evidence_report.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D6_test_package/test_evidence_report.md)
  - [defect_log.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D6_test_package/defect_log.md)
  - [uat_acceptance_scenarios.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D6_test_package/uat_acceptance_scenarios.md)
- **D7 Deployment Package**: [docs/D7_deployment/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D7_deployment/)
  - [offline_installation_guide.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D7_deployment/offline_installation_guide.md)
  - [environment_checklist.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D7_deployment/environment_checklist.md)
  - [backup_restore_runbook.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D7_deployment/backup_restore_runbook.md)
  - [update_and_rollback_runbook.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D7_deployment/update_and_rollback_runbook.md)
- **D8 Operational Documentation**: [docs/D8_operational/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/)
  - [administrator_guide.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/administrator_guide.md)
  - [user_guide.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/user_guide.md)
  - [api_reference.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/api_reference.md)
  - [troubleshooting_runbook.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/troubleshooting_runbook.md)
  - [training_plan.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D8_operational/training_plan.md)
- **D9 Demonstration & Backlog**: [docs/D9_demonstration/](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D9_demonstration/)
  - [demo_script_and_scenarios.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D9_demonstration/demo_script_and_scenarios.md)
  - [system_presentation.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D9_demonstration/system_presentation.md)
  - [known_limitations.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D9_demonstration/known_limitations.md)
  - [production_completion_backlog.md](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/docs/D9_demonstration/production_completion_backlog.md)

---

## 🔒 Security, Compliance & License
- **License**: MIT License ([LICENSE](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/LICENSE))
- **Software Bill of Materials**: CycloneDX 1.5 JSON ([SBOM.json](file:///C:/Users/rahul/OneDrive/Documents/Desktop/AISYS/SBOM.json))
- **Data Protection**: 100% synthetic dataset guarantees zero leakage of institutional or personal data.
