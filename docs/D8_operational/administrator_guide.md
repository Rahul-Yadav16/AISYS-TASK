# Deliverable D8: System Administrator Guide

## 1. Administrative Overview
This guide provides system administrators with the technical procedures required to configure, maintain, monitor, and secure the AISYS RFID Library Management Solution.

---

## 2. Configuration Management (SOP Section 10)
Configuration settings are managed externally in `config/sample_config.json` (or `config/production_config.json`). Environment variables override file settings.

### Key Policy Parameters:
- `system.institution_name`: Institutional title displayed on slips and UI.
- `circulation_policy.loan_period_days`: Default loan duration (default: `14` days).
- `circulation_policy.max_renewals`: Maximum allowed renewal count per loan (default: `2`).
- `circulation_policy.max_fine_limit`: Maximum outstanding fine balance before borrowing is blocked (default: `$10.00`).
- `circulation_policy.enforce_reference_restriction`: Prevents reference items from check-out (`true`).
- `rfid_middleware.offline_gate_security_bit_check`: Inspects tag EAS bit offline directly (`true`).

---

## 3. User & Role Management (RBAC)
Administrators configure staff accounts and assign granular security roles:
- `ADMIN`: Full system permissions including backups, migrations, and system settings.
- `LIBRARIAN`: Cataloguing, circulation desk, patron records, reports.
- `CATALOGUER`: Bibliographic records, items, spine labels, RFID tag encoding.
- `CIRCULATION`: Desk check-out, check-in, renewals, patron fine payments.

### Assigning Contactless Smart Cards:
Staff members can be bound to RFID smart cards (`users.smart_card_uid`) for passwordless tap-login.

---

## 4. Controlled 20,000 Record Migration Management
1. Place source spreadsheet in `storage/staging/` or upload via the Web UI.
2. Ingest into staging table. The system automatically creates a pre-migration hot backup.
3. Run validation profiling: inspect valid counts, invalid rows, and duplicates.
4. Export error reports for cataloguer review.
5. Commit valid records: automatically updates catalog and FTS5 search index.
6. If defects are discovered post-migration, execute an atomic rollback to remove the batch while leaving pre-existing catalog records intact.

---

## 5. Security & Audit Trail Inspection
Administrators can inspect immutable audit logs at `/api/admin/audit-logs` or via the web console.
All critical events (login attempts, policy overrides, check-outs, gate alarms, backups, restores, and updates) are recorded with timestamps, actor IDs, and payload metadata.
