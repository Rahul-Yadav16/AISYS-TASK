# Deliverable D1: Detailed System Use Cases

This document details the functional use cases implemented in the AISYS RFID Library Management System, covering end-to-end actor interactions, preconditions, main flows, alternate flows, and postconditions.

---

### Use Case UC-01: Bibliographic Search, Item Creation & RFID Tagging
- **Primary Actor**: Cataloguer / Library Staff
- **Requirement Mapping**: FR 01, FR 02, FR 05, AC 02
- **Preconditions**:
  - Staff is authenticated with `CATALOGUER` or `ADMIN` role.
  - RFID Staff Station reader is connected and reporting online status.
- **Main Success Scenario**:
  1. Staff searches for a title via OPAC/Staff Search or initiates creation of a new bibliographic record.
  2. System validates mandatory bibliographic fields (Title, Author, ISBN, Call Number, Material Type, Barcode/Accession Number).
  3. Staff places an unprogrammed RFID tag on the Staff Station reader.
  4. Middleware queries tag UID and checks if tag is already associated with another record.
  5. System encodes the item Accession Number and Library ID onto the RFID chip user memory and sets EAS status to Active (`0x00`).
  6. System creates the `rfid_tags` binding record linked to the specific item.
  7. UI updates immediately, displaying the tag-to-item relationship, tag health metrics, and timestamp.
- **Alternative Flows**:
  - *4a. Tag already bound*: System alerts operator with existing item details and prompts for re-tagging authorization.
  - *2a. Invalid Accession/Barcode*: System highlights missing mandatory fields and blocks tag programming until corrected.

---

### Use Case UC-02: RFID Self-Service / Desk Circulation (Check-out, Renewal, Check-in)
- **Primary Actor**: Circulation Desk Staff or Patron (via Self-Service Station)
- **Requirement Mapping**: FR 03, FR 04, AC 03
- **Preconditions**:
  - Patron card or member barcode is scanned/tapped.
  - Item is catalogued and RFID tag is programmed.
- **Main Success Scenario (Check-Out)**:
  1. Patron taps smart card or enters member ID; system displays patron profile, active loans, and fine status.
  2. Patron places item(s) on the RFID staff antenna.
  3. System verifies item eligibility:
     - Item status is `AVAILABLE`.
     - Item material type is not `REFERENCE` only.
     - Patron account is `ACTIVE` (not blocked) and outstanding fines do not exceed the configured limit (default: $10.00).
  4. System records loan transaction in `circulation_transactions` with calculated due date (default: 14 days).
  5. Middleware instructs the RFID reader to disarm the tag's EAS security bit (set to `0x01` - Issued/Disarmed).
  6. Transaction receipt is formatted for printing and a confirmation notification is queued.
- **Main Success Scenario (Check-In)**:
  1. Item is placed on the reader or returned via book drop reader.
  2. System identifies the active loan, calculates overdue fines if applicable, and updates loan status to `RETURNED`.
  3. Middleware rearms the RFID EAS security bit to `0x00` (Protected/Armed).
  4. System prompts operator with current shelf destination or reserve hold notices.
- **Main Success Scenario (Renewal)**:
  1. Patron or staff requests renewal for an active loan.
  2. System checks renewal count limit and whether another patron has placed a hold.
  3. Due date is extended and loan record is updated with audit timestamp.

---

### Use Case UC-03: Circulation Restriction & Policy Enforcement
- **Primary Actor**: Circulation Desk Staff
- **Requirement Mapping**: FR 04, AC 04
- **Preconditions**: Staff attempts to issue an item to a patron.
- **Main Scenarios**:
  - **Scenario A: Reference Book Restriction**: Patron attempts to check out an item categorized as `REFERENCE`. System immediately rejects the transaction with code `ERR_POLICY_REFERENCE_RESTRICTED` ("Reference material may not leave the library premises").
  - **Scenario B: Blocked Member**: Patron account has `is_blocked = true` (e.g., disciplinary hold or expired membership). System halts check-out with `ERR_MEMBER_BLOCKED`.
  - **Scenario C: Fine Limit Exceeded**: Patron has unpaid fines of $15.50 (exceeding ceiling of $10.00). System halts check-out with `ERR_FINE_EXCEEDED` ("Outstanding fine of $15.50 exceeds policy limit of $10.00").
- **Postconditions**: No loan record is created; RFID tag EAS bit remains Armed (`0x00`); policy denial event logged in audit trail.

---

### Use Case UC-04: Handheld Shelf Inventory & Misplaced Item Detection
- **Primary Actor**: Library Technician
- **Requirement Mapping**: FR 06, AC 05
- **Preconditions**: Handheld RFID reader is paired with AISYS mobile/staff web view; target shelf/section is selected (e.g., Call Numbers 000-099 or Shelf A-03).
- **Main Success Scenario**:
  1. Operator waves the handheld reader wand across the shelf books.
  2. Middleware receives burst of RFID tag EPC/UID reads in real time via WebSocket/REST.
  3. For each detected tag, system compares item's catalogued shelf location and sequence:
     - **On-Shelf Correct**: Green UI indicator, short high-pitch audio beep (880Hz).
     - **Misplaced Item**: Yellow/Orange UI indicator, double warning pulse (440Hz), displaying item's actual assigned shelf vs. scanned shelf.
     - **Uncatalogued / Unknown Tag**: Red UI indicator, warning alert.
  4. System compiles inventory reconciliation: compares shelf inventory against database catalog to report **Missing Items** (catalogued on this shelf but not detected).
  5. Operator clicks "Finalize Inventory" to export the verification report.

---

### Use Case UC-05: Security Gate Unauthorized Item Alarm & CCTV Capture
- **Primary Actor**: Security Gate Antenna / Visitor / Security Officer
- **Requirement Mapping**: FR 07, AC 06
- **Preconditions**: RFID Security Gate is operational at the library perimeter exit.
- **Main Success Scenario**:
  1. A person walks through the gate carrying an unissued library book (EAS bit = `0x00`).
  2. Gate antenna detects the active EAS bit and reads the item accession number / EPC tag.
  3. Gate triggers local hardware strobe and audible alarm buzzer (220Hz persistent alarm).
  4. Middleware receives gate security event and executes event pipeline:
     - Records gate event in `gate_security_events` table with timestamp, gate ID, and accession number.
     - Invokes Mock Camera Adapter to trigger CCTV photo snapshot of the gate egress zone.
     - Queues an urgent email/SMS alert to the Head of Security and Chief Librarian with incident details and CCTV image link.
     - Increments gate footfall counter.
- **Offline Fallback Scenario**:
  - If the centralized server is temporarily offline, the gate's local microcontroller triggers the physical siren/strobe directly based on the tag's raw EAS bit, buffering the event in local EEPROM/memory until server reconnection.

---

### Use Case UC-06: Staff Smart Card Authentication & RBAC Enforcement
- **Primary Actor**: Library Staff Member
- **Requirement Mapping**: FR 04, FR 11, AC 07
- **Preconditions**: Staff member possesses an authorized RFID/contactless smart card (e.g., Mifare Classic / DESFire UID).
- **Main Success Scenario**:
  1. Staff member presents smart card to the contactless reader at the login terminal.
  2. Middleware reads card UID `SC-ADMIN-001` and forwards it to `SmartCardAuthService`.
  3. System looks up credential binding, validates card status (`ACTIVE`), and retrieves associated user roles (`ADMIN`, `LIBRARIAN`, or `CIRCULATION`).
  4. System generates an authenticated session token with granular role permissions.
  5. The UI dynamically configures menus and access controls:
     - An `ADMIN` sees System Configuration, Migration Center, Database Backup, and Audit Logs.
     - A `CIRCULATION` operator only sees Desk Operations, Tagging, and Inventory.
- **Alternative Flow**:
  - Card UID unrecognized: System denies access, prompts for standard username/password or card registration.

---

### Use Case UC-07: Controlled 20,000 Record Spreadsheet Migration
- **Primary Actor**: Systems Administrator
- **Requirement Mapping**: FR 10, NFR 01, AC 01, AC 10
- **Preconditions**:
  - Source spreadsheet (CSV/Excel format containing ~20,000 records) is uploaded or placed in `storage/staging/`.
  - System executes an automated hot backup of the current database before migration.
- **Main Success Scenario**:
  1. Administrator initiates the Migration Wizard and selects the source spreadsheet file.
  2. **Stage 1 - Ingestion & Profiling**: Records are ingested into the isolated `migration_staging` table.
  3. **Stage 2 - Validation & Deduplication**:
     - System validates mandatory fields (Title, Author, Call Number, Barcode).
     - System flags duplicates within the file and against existing database records.
     - Rows with validation failures (e.g. malformed ISBN, missing title, duplicate barcode) are flagged with detailed error codes in `migration_errors`.
  4. **Stage 3 - Reconciliation Report**: System displays preview:
     - Total Rows Read: 20,000
     - Valid Records: 19,850
     - Invalid / Rejected Rows: 100
     - Duplicate Rows: 50
  5. **Stage 4 - Commit / Migration**: Valid records are atomically transferred into the production `bibliographic_records` and `items` tables with real-time FTS5 search index updates.
  6. **Stage 5 - Rollback Option**: If any unforeseen defect is detected, administrator can click "Atomic Rollback", completely purging the migrated batch and restoring original counts without touching pre-existing records.

---

### Use Case UC-08: Administrative Reports & Real-Time Dashboard
- **Primary Actor**: Library Director / Administrator
- **Requirement Mapping**: FR 08, AC 08
- **Main Success Scenario**:
  1. Administrator navigates to Dashboard & Reports.
  2. System renders real-time KPI cards:
     - Total Titles & Items
     - Percentage of Tagged vs. Untagged Items
     - Active Loans & Overdue Counts
     - Today's Circulation Turnover (Check-outs / Check-ins)
     - Security Gate Violations & Footfall Count
     - Active RFID Devices & Heartbeat Status
  3. Administrator selects filterable reports (by date range, department, material type, operator ID) and exports CSV / printable PDF.

---

### Use Case UC-09: Hot Database Backup & Disaster Recovery Verification
- **Primary Actor**: System Administrator
- **Requirement Mapping**: NFR 01, NFR 07, AC 10
- **Main Success Scenario**:
  1. Administrator or scheduled job triggers hot backup via `/api/admin/backup`.
  2. System locks SQLite WAL write stream cleanly, streams byte-level backup to `storage/backups/backup_YYYYMMDD_HHMMSS.db`, and generates SHA-256 checksum.
  3. Administrator simulates a corruption or accidental configuration change.
  4. Administrator initiates restore with target backup timestamp.
  5. System validates SHA-256 integrity, closes active connections, swaps database file safely, and restarts service.
  6. System verifies table counts match pre-incident snapshot exactly.

---

### Use Case UC-10: Offline Update Package Installation & Rollback
- **Primary Actor**: IT Technician / System Administrator
- **Requirement Mapping**: FR 12, AC 09
- **Preconditions**: Update archive `aisys_update_v1.1.0.pkg` is copied via USB flash drive to the isolated server.
- **Main Success Scenario**:
  1. Administrator runs `offline_updater.py --package aisys_update_v1.1.0.pkg`.
  2. Updater verifies cryptographic package signature / SHA-256 manifest.
  3. Updater takes automated snapshot of current application binary, migrations, and database.
  4. Updater applies schema patch `V2__updates.sql` and updates application files.
  5. System runs post-update health checks (`/api/health`).
  6. If health checks pass, new version `1.1.0` is marked active.
  7. If health checks fail or administrator issues `--rollback`, updater restores previous snapshot, executes down-migration, and restarts service cleanly.
