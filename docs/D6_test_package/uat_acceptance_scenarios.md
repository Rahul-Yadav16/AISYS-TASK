# Deliverable D6: User Acceptance Testing (UAT) Scenarios

This document provides step-by-step test instructions for human testers and evaluation teams to reproduce and verify the 10 Priority Acceptance Scenarios (AC 01 to AC 10).

---

### Scenario UAT-01: Controlled 20,000 Record Spreadsheet Migration (AC 01)
1. Open web browser to `http://localhost:8000/`.
2. Click **20k Migration Wizard** on the left menu.
3. Click the button: **Ingest 20,000 Record Dataset (sample_import_20000.csv)**.
4. Verify notification shows 20,000 records ingested into staging and an automated pre-migration hot backup path is recorded.
5. Click **Run Validation & Profile**.
6. Verify Reconciliation Report displays:
   - Total Rows Profiled: 20,000
   - Valid Records: 19,850
   - Invalid Records: 100
   - Duplicate Records: 50
   - Checksum Match: 100% RECONCILED.
7. Click **Commit Valid Records to Database**. Verify Dashboard title and item counts increment by 19,850.
8. Click **Test Atomic Rollback**. Verify counts revert exactly to initial numbers without modifying baseline records.

---

### Scenario UAT-02: RFID Staff Station Tag Association & Validation (AC 02)
1. Navigate to **RFID Staff Station**.
2. In Item Accession Number, enter `ACC-005001`. Click **Validate Item Record**.
3. Verify title displays: *Database System Concepts* and status shows *Unassigned*.
4. In RFID Tag Transponder UID, enter `E00401509988A501`.
5. Click **Encode & Bind Tag to Item**.
6. Verify green confirmation banner and success chime (880Hz).
7. Navigate to **OPAC & Catalog**, search `Database System Concepts`, and verify tag icon indicates active RFID transponder with EAS Armed (0x00).

---

### Scenario UAT-03: Interoperability Circulation Check-Out, Renew, Check-In (AC 03)
1. Navigate to **Circulation Desk**.
2. In Patron ID, enter `MEM-1001` (Alice Smith).
3. In Item Barcode/Accession, enter `ACC-001001` (Introduction to Algorithms).
4. Click **Authorize Check-Out**.
5. Observe success chime (880Hz), loan record created, due date calculated (14 days), and RFID tag EAS bit set to Disarmed (`0x01`).
6. In Desk Check-In, enter `ACC-001001`. Click **Process Item Return**.
7. Observe return confirmation, shelf destination displayed (`Shelf-A-01`), and RFID tag EAS bit set to Armed (`0x00`).

---

### Scenario UAT-04: Circulation Policy Block Restrictions (AC 04)
1. On **Circulation Desk**, test the three restriction buttons under "Test Priority Acceptance Restrictions":
   - **Test 1 - Reference Book**: Attempt checkout of `ACC-002001` (Oxford English Dictionary).
     *Expected Result*: Red policy rejection banner stating *"REFERENCE MATERIAL and cannot be checked out"*.
   - **Test 2 - Blocked Member**: Attempt checkout for `MEM-1003` (Charlie Brown).
     *Expected Result*: Red rejection banner stating *"Borrowing blocked for member 'MEM-1003': Suspended for damaged media"*.
   - **Test 3 - Over-limit Fine**: Attempt checkout for `MEM-1004` (Diana Prince).
     *Expected Result*: Red rejection banner stating *"Member fine balance ($15.50) exceeds maximum allowed threshold ($10.00)"*.

---

### Scenario UAT-05: Handheld RFID Shelf Inventory & Misplaced Detection (AC 05)
1. Navigate to **Handheld Inventory**.
2. Click **Start Audit Session** (Target: `Shelf-A-01`).
3. Click **Wave Wand: Scan Correct Items**.
   *Expected Result*: Green indicators appear, high-frequency confirmation chime sounds (880Hz).
4. Click **Wave Wand: Detect Misplaced Item**.
   *Expected Result*: Amber banner appears with double warning pulse (440Hz), showing *Artificial Intelligence* scanned on `Shelf-A-01` but assigned to `Shelf-A-02`.
5. Click **Finalize Audit & Detect Missing Items**.
   *Expected Result*: Summary modal lists Missing Item `ACC-001002` (catalogued on shelf but not scanned).

---

### Scenario UAT-06: Security Gate Unauthorized Exit Alarm & CCTV Capture (AC 06)
1. Navigate to **Security Gate Monitor**.
2. Click the red button: **Trigger Unauthorized Removal (Unissued Book EAS 0x00)**.
3. Observe:
   - Audible persistent siren (220Hz) sounds.
   - Screen flashes red alarm state.
   - Alarm banner displays accession number `ACC-001001` and title *Introduction to Algorithms*.
   - Surveillance surveillance CCTV snapshot is generated and displayed on screen.
   - Security email alert is dispatched to mock spool.
4. Click the green button: **Authorized Exit (Checked-Out Book EAS 0x01)**.
   *Expected Result*: Passage allowed silently, no alarm triggered.

---

### Scenario UAT-07: Staff Smart Card Fast Tap-Login & RBAC Enforcement (AC 07)
1. Click **Logout** in the top navigation bar.
2. Click the quick tap button: **Tap Admin Card (SC-ADMIN-001)**.
   *Expected Result*: Success chime sounds, top bar indicates *"System Administrator (ADMIN)"*, full administrative controls unlocked.
3. Click **Tap Staff Card (SC-CIRC-004)**.
   *Expected Result*: Success chime sounds, top bar indicates *"Circulation Desk Staff (CIRCULATION)"*. Administrative features are restricted.

---

### Scenario UAT-08: Executive Dashboard & Filterable Reports (AC 08)
1. Navigate to **Dashboard & KPIs**.
2. Verify all live KPI cards are populated:
   - Total Titles, Total Items, Tagged RFID Items (percentage calculated)
   - Active Loans, Total Members, Gate Alarm Incidents, Footfall Traffic.
3. Review recent security alarms table with clickable links to CCTV snapshots.

---

### Scenario UAT-09: Offline Update Package Installation & Rollback (AC 09)
1. Navigate to **System & Offline Lifecycle**.
2. Click **Apply Offline Update Package v1.1.0**.
   *Expected Result*: Pre-update snapshot is saved; system confirms update applied to version `1.1.0`.
3. Click **Rollback Offline Update to v1.0.0**.
   *Expected Result*: Pre-update database snapshot restored; system version reports `1.0.0`.

---

### Scenario UAT-10: Disaster Recovery Restore After Failed Change (AC 10)
1. Navigate to **System & Offline Lifecycle**.
2. Click **Create Atomic Hot Database Backup**.
   *Expected Result*: Online SQLite backup is generated, SHA-256 integrity hash is computed and stored.
3. Using API or simulated change, introduce bad data.
4. Restore database using `tools/db_backup_restore.py --restore storage/backups/<backup_name>.db`.
   *Expected Result*: SHA-256 hash verified, database restored, original row counts 100% verified.
