# Deliverable D9: Demonstration Walkthrough & Script

This document provides a live demonstration script for evaluators, covering all 10 Priority Acceptance Scenarios (AC 01 to AC 10).

---

## Demonstration Outline & Timing (Total: 15 Minutes)

| Segment | Topic & Acceptance Scenario | Action Steps | Expected Visual / Auditory Outcome |
|---|---|---|---|
| **00:00 - 02:00** | System Overview & Smart Card Login (**AC 07**) | 1. Open `http://localhost:8000/`.<br>2. Tap Admin Smart Card (`SC-ADMIN-001`).<br>3. Inspect role-based navigation. | High-frequency confirmation chime (880Hz); top bar displays `System Administrator (ADMIN)`. |
| **02:00 - 04:00** | Bibliographic Search & RFID Tagging (**AC 02**) | 1. Navigate to **RFID Staff Station**.<br>2. Validate unassigned copy `ACC-005001`.<br>3. Bind RFID Tag `E00401509988A501`.<br>4. Check OPAC search. | Item details verified; tag linked with EAS bit Armed (`0x00`); OPAC shows active RFID transponder. |
| **04:00 - 06:30** | Circulation & Policy Restrictions (**AC 03, AC 04**) | 1. Checkout `ACC-001001` to `MEM-1001`.<br>2. Demonstrate rejection for Reference Book `ACC-002001`.<br>3. Demonstrate rejection for Blocked Member `MEM-1003`.<br>4. Demonstrate rejection for High Fine `MEM-1004`.<br>5. Return `ACC-001001`. | Normal checkout succeeds with EAS disarmed (`0x01`); each restriction produces a clear red policy violation banner with low buzz tone; return rearms EAS to `0x00`. |
| **06:30 - 08:30** | Handheld Inventory & Misplaced Detection (**AC 05**) | 1. Navigate to **Handheld Inventory**.<br>2. Start audit on `Shelf-A-01`.<br>3. Trigger correct scan burst.<br>4. Trigger misplaced scan burst.<br>5. Finalize audit. | Correct item gives 880Hz chime; misplaced item (*Artificial Intelligence*) gives 440Hz double pulse and amber alert; summary lists missing item `ACC-001002`. |
| **08:30 - 10:30** | Security Gate Alarm & CCTV Snapshot (**AC 06**) | 1. Navigate to **Security Gate Monitor**.<br>2. Click **Trigger Unauthorized Removal** (Unissued EAS 0x00).<br>3. Click **Authorized Exit** (Issued EAS 0x01). | Unissued item triggers 220Hz persistent siren, red strobe, logs accession `ACC-001001`, displays captured CCTV surveillance snapshot, and queues security email. Authorized exit passes silently. |
| **10:30 - 13:00** | 20k Spreadsheet Migration & Rollback (**AC 01, AC 10**) | 1. Navigate to **20k Migration Wizard**.<br>2. Ingest `sample_import_20000.csv`.<br>3. Run validation & profile.<br>4. Review Reconciliation Report (19,850 valid, 100 invalid, 50 duplicates).<br>5. Commit valid records.<br>6. Test Atomic Rollback. | Pre-migration hot backup saved; reconciliation shows 100% checksum match; titles jump by 19,850 and search indexes in real time; rollback cleanly removes migrated batch and restores exact baseline counts. |
| **13:00 - 15:00** | Offline Update & Disaster Recovery (**AC 09, AC 10**) | 1. Navigate to **System & Offline Lifecycle**.<br>2. Click **Apply Offline Update v1.1.0**.<br>3. Click **Rollback Offline Update to v1.0.0**.<br>4. Inspect immutable audit log. | Pre-update snapshot saved; schema updated; rollback restores exact snapshot; audit log reflects complete administrative history. |
