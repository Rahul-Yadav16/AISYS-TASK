# Deliverable D6: Test Execution Evidence Report

## 1. Summary of Test Execution
- **Date of Execution**: 2026-10-04
- **Test Framework**: `pytest 9.1.1`, Python 3.12.0 (win32)
- **Total Tests Collected**: 20
- **Total Passed**: 20 (100% Pass Rate)
- **Execution Duration**: 5.56 seconds

---

## 2. Evidence Mapping to Priority Acceptance Scenarios (AC 01 to AC 10)

| Acceptance ID | Scenario Summary | Test Function & File | Execution Result |
|---|---|---|---|
| **AC 01** | Import 20k spreadsheet into staging, reject invalid rows, detect duplicates, migrate valid records, reconcile counts | `tests/test_data_migration_20k.py::test_migration_20k_reconciliation` | **PASSED** (20,000 processed; 19,850 valid, 100 invalid, 50 duplicates; reconciled; committed & rolled back cleanly) |
| **AC 02** | Create/locate bib item, validate, associate mock RFID tag, display tag-to-item relationship | `tests/test_rfid_middleware.py::test_tag_association_and_query` | **PASSED** (Item validated; tag bound with EAS 0; tag-to-item mapping verified) |
| **AC 03** | Check out, renew, check in through mocked NCIP or SIP2 flow while preserving auditable history | `tests/test_ncip_sip2.py::test_sip2_and_ncip_checkout_checkin` | **PASSED** (SIP2 frames 99, 11, 29, 09 and NCIP JSON/XML verified with checksums) |
| **AC 04** | Block circulation for reference item, blocked member, or member whose fine exceeds configurable limit | `tests/test_circulation_and_fines.py::test_circulation_restrictions` | **PASSED** (Blocked reference items, blocked members, and patrons exceeding fine limit) |
| **AC 05** | Handheld-reader mock shelf inventory, report missing & misplaced items with visible & audible confirmation | `tests/test_rfid_middleware.py::test_handheld_inventory_misplaced_and_missing` | **PASSED** (Misplaced item on wrong shelf flagged with 440Hz pulse; missing items detected on finalization) |
| **AC 06** | Unauthorized removal event from gate mock, record accession number, attach mock CCTV image, queue email | `tests/test_security_gate_events.py::test_gate_alarm_cctv_and_email_flow` | **PASSED** (Gate detected EAS 0x00, triggered 220Hz siren, recorded accession, saved CCTV image, queued email) |
| **AC 07** | Staff smart-card login through mock credential provider and enforce role-based permissions | `tests/test_security_and_audit.py::test_smart_card_rbac_login` | **PASSED** (Admin & Circulation staff cards authenticated; RBAC rights strictly enforced) |
| **AC 08** | Generate dashboard statistics and filterable reports for tagged items, members, circulation, operators, gate events | `tests/test_core_ilms.py::test_dashboard_and_filterable_reports` | **PASSED** (KPI cards, tagged percentages, and reports populated accurately) |
| **AC 09** | Install & run without internet access, apply offline update package, complete documented rollback | `tests/test_offline_update_rollback.py::test_offline_update_and_rollback` | **PASSED** (Applied v1.1.0 update with snapshot, then rolled back to v1.0.0 cleanly) |
| **AC 10** | Restore from backup after simulated failed migration or integration change and prove original data remains intact | `tests/test_backup_restore_resilience.py::test_restore_after_failed_migration` | **PASSED** (Pre-change backup verified with SHA-256; corrupting changes reverted; original data 100% intact) |

---

## 3. Raw Test Output Log Excerpt

```
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\rahul\OneDrive\Documents\Desktop\AISYS
configfile: pytest.ini
testpaths: tests
collected 20 items

tests/test_backup_restore_resilience.py::test_restore_after_failed_migration PASSED [  5%]
tests/test_circulation_and_fines.py::test_circulation_normal_lifecycle PASSED [ 10%]
tests/test_circulation_and_fines.py::test_circulation_restrictions PASSED [ 15%]
tests/test_circulation_and_fines.py::test_fine_payment_and_clearance PASSED [ 20%]
tests/test_core_ilms.py::test_create_bibliographic_and_item PASSED       [ 25%]
tests/test_core_ilms.py::test_fts5_fulltext_search PASSED                [ 30%]
tests/test_core_ilms.py::test_spine_label_generation PASSED              [ 35%]
tests/test_core_ilms.py::test_virtual_bookshelf PASSED                   [ 40%]
tests/test_core_ilms.py::test_dashboard_and_filterable_reports PASSED    [ 45%]
tests/test_data_migration_20k.py::test_migration_20k_reconciliation PASSED [ 50%]
tests/test_ncip_sip2.py::test_sip2_and_ncip_checkout_checkin PASSED      [ 55%]
tests/test_offline_update_rollback.py::test_offline_update_and_rollback PASSED [ 60%]
tests/test_rfid_middleware.py::test_tag_association_and_query PASSED     [ 65%]
tests/test_rfid_middleware.py::test_handheld_inventory_misplaced_and_missing PASSED [ 70%]
tests/test_security_and_audit.py::test_smart_card_rbac_login PASSED      [ 75%]
tests/test_security_and_audit.py::test_password_hashing_and_verification PASSED [ 80%]
tests/test_security_and_audit.py::test_immutable_audit_logging PASSED    [ 85%]
tests/test_security_and_audit.py::test_health_check_endpoint PASSED      [ 90%]
tests/test_security_gate_events.py::test_gate_alarm_cctv_and_email_flow PASSED [ 95%]
tests/test_security_gate_events.py::test_gate_authorized_transit PASSED  [100%]

======================== 20 passed in 5.56s ========================
```
