# Deliverable D1: Project Initiation, Assumptions, Clarifications & Scope Boundaries

## 1. Project Overview
The AISYS RFID-enabled Library Solution is an industrial-grade, modular library management and RFID middleware system. It is designed to operate seamlessly either standalone or integrated non-destructively with an existing Integrated Library Management Software (ILMS) system. The solution enforces data integrity, zero records corruption, offline operability, robust migration of 20,000+ records, and vendor-neutral hardware mock adapters.

---

## 2. Scope Boundaries (SOP Section 3)

### 2.1 Included Software Work
- **Core Library Workflows**: Acquisition, cataloguing, serials management, circulation, OPAC search, barcode/spine-label generation, and report generation (FR 01).
- **Web & Search Engine**: Full-text search with real-time indexing (SQLite FTS5), net cataloguing, and virtual bookshelf (FR 02).
- **RFID Middleware**: Device-neutral abstraction layer for staff stations, handheld readers, security gates, patron smart cards, and item tags (FR 03, FR 05, FR 06, FR 07).
- **Interoperability Boundaries**: Standard NCIP 2.0 (XML & JSON) and 3M SIP2 adapter boundaries with fully verified mocks (FR 03, AC 03).
- **Circulation & Policy Enforcement**: Check-out, check-in, renewals, patron-card personalization, reference-only restrictions, member blocking, configurable fine ceilings, and role-based access control (FR 04, AC 04).
- **Inventory & Shelf Management**: Stock verification, missing/misplaced item detection, bulk RFID reading, and visible/audible confirmation events (FR 06, AC 05).
- **Security Gate & Event Integration**: Unauthorized removal detection, offline EAS/security-bit reading, accession logging, audible alarms, mock CCTV photo capture, and automated security notification dispatch (FR 07, AC 06).
- **Reporting & Dashboards**: Comprehensive analytics across tagged items, patrons, circulation turnover, operator activity, RFID client health, and gate security violations (FR 08, AC 08).
- **Provider-Neutral Notifications**: Email, SMS, and receipt printing queues with template rendering (FR 09).
- **Controlled Migration Utility**: Streaming import for ~20,000 spreadsheet records, row-level validation, duplicate detection, dry-run profiling, reconciliation reporting, and atomic rollback (FR 10, AC 01, AC 10).
- **Administration & Security**: User and role management (RBAC), password hashing, audit trails, software versioning, and system health checks (FR 11, NFR 02).
- **Offline Lifecycle Management**: Zero-cloud deployment, standalone activation, offline update packages, hot database backup, verification, and automated rollback (FR 12, AC 09, AC 10).
- **Documentation & Verification**: Requirements Traceability Matrix (RTM), Architecture Package (D2), Automated Test Suite (D6), Deployment & Rollback Runbooks (D7), Operational Manuals (D8), and Demonstration Pack (D9).

### 2.2 Excluded from Candidate Implementation
- Physical hardware manufacturing, physical mounting, or electrical/optical cabling of RFID readers, antennas, security gates, smart card readers, thermal printers, servers, or CCTV cameras.
- Access to live institutional production databases, institutional intranet networks, or real student/staff personal data (PII).
- Unverifiable claims of formal ISO/IEC, OEM hardware, or SIP2/NCIP vendor certifications without published test evidence.

---

## 3. Assumptions Log

| ID | Category | Assumption Description | Impact / Mitigation |
|---|---|---|---|
| ASM-01 | Environment | Target operating systems are Windows 11 (64-bit) for desktop clients and Windows Server 2022+ for server hosting. | Architecture uses cross-platform Python 3.12 + FastAPI + modern HTML5/ES6 without platform-locked proprietary drivers. |
| ASM-02 | Network | The target library facility operates on an isolated Ethernet/LAN environment with intermittent or strictly zero external internet access. | All dependencies, CSS, JavaScript, and fonts are 100% self-hosted; no external CDNs or online licensing servers required. |
| ASM-03 | Database | SQLite 3 with WAL (Write-Ahead Logging) and FTS5 full-text indexing fulfills the performance and zero-administration needs of isolated sites (~100k records, concurrency > 100 req/s). | Avoids heavy DBMS overhead (SQL Server / Oracle); hot backups are atomic and zero-configuration. |
| ASM-04 | Existing ILMS | The legacy ILMS exposes either a read-only database replica or standard SIP2/NCIP service endpoints. | The AISYS system interacts via non-destructive adapter boundaries, maintaining an audit trail and never executing `DROP`, `DELETE`, or destructive `UPDATE` on existing legacy records. |
| ASM-05 | RFID Standards | Item tags adhere to ISO 15693 / ISO 18000-3 Mode 1 (HF) or EPC Class 1 Gen 2 (UHF), utilizing a standard AFI/EAS security bit (Byte 0x01 = Checked Out, Byte 0x00 = Protected). | Middleware models the AFI/EAS byte flag directly, allowing offline gate detection without network latency. |
| ASM-06 | Data Privacy | All patron and bibliographic data supplied or generated during prototype verification must be 100% synthetic. | A synthetic data generator produces 20,000 realistic records with randomized titles, ISBNs, DDC call numbers, and patron records without real PII. |

---

## 4. Clarification Log & Resolved Questions

| Ref | Topic | Question / Issue | Resolution & Design Decision |
|---|---|---|---|
| CLR-01 | RFID Gate Offline Reading | How does the security gate verify item status when the ILMS or network is completely disconnected? | The RFID security gate reads the tag's physical EAS (Electronic Article Surveillance) or AFI (Application Family Identifier) bit directly at the antenna plane. If the bit indicates "unissued" (0x00), the gate triggers an alarm, logs the accession number, triggers the CCTV camera mock, and stores the event locally for deferred reconciliation. |
| CLR-02 | Non-destructive Integration | How is NFR 01 ("The solution must not modify, delete, or corrupt existing library records") guaranteed during migration and synchronization? | AISYS implements a staging schema (`migration_staging`) and an immutable transactional log. Sync adapters use append-only or versioned records. Database backups are taken automatically prior to any migration or bulk update. |
| CLR-03 | Migration Volume | How should ~20,000 records be handled reliably without running out of memory or locking the system? | The migration service utilizes streaming chunking (batches of 1,000 records), writes row errors to a persistent defect table, reconciles source vs target counts, and wraps operations in an atomic transaction that allows one-click rollback. |
| CLR-04 | Smart Card Authentication | How does patron and staff smart card login operate? | Smart card readers pass a unique UID (Mifare / Desfire mock). The middleware maps this UID to staff credentials and patron records via the `patron_cards` table and issues a cryptographically signed session token. |
| CLR-05 | Sound / Visual Alerts | How are audible/visible confirmation events for handheld and gate readers represented in a web application? | The user interface incorporates the Web Audio API to synthesize distinct audio frequencies (e.g., 880Hz short beep for found item, 440Hz double pulse for misplaced item, 220Hz persistent siren for gate alarm) and real-time color-coded visual banners. |

---

## 5. Risk Assessment & Mitigation Strategy

| Risk ID | Risk Description | Severity | Likelihood | Mitigation Strategy |
|---|---|---|---|---|
| RSK-01 | Data corruption during 20,000 record spreadsheet import. | High | Medium | Enforce pre-migration hot backup, validate rows in staging, detect duplicate ISBNs/accession numbers, and provide instant rollback. |
| RSK-02 | Network partition between gate and ILMS causing false positives/negatives. | High | Medium | Store security status on RFID tag EAS bit; gate evaluates tag hardware bit independently of ILMS connection status. |
| RSK-03 | High fine or blocked patron bypasses circulation desk. | Medium | Low | Enforce strict server-side validation in `CirculationService` checking `patron.is_blocked` and `patron.current_fines > max_limit`. |
| RSK-04 | Offline deployment failure due to missing OS libraries. | Medium | Low | Bundle dependencies as standalone Python wheels and package an automated offline installer script (`tools/offline_installer.py`). |
