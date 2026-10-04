# Deliverable D8: Diagnostics and Troubleshooting Runbook

This runbook provides frontline IT technicians with diagnostic procedures and resolutions for operational incidents.

---

## 1. Quick Diagnostic Triage

### Step 1: Query Health Probe
Send an HTTP GET request to `/api/admin/health`:
```powershell
curl http://localhost:8000/api/admin/health
```
- If `status == "HEALTHY"`: Core application and database are operational.
- If `status == "UNHEALTHY"`: Check the `database.error` message and free disk space.

### Step 2: Inspect Structured JSON Logs
Review the active log stream at `storage/aisys.log`:
```powershell
Get-Content -Tail 50 -Wait storage\aisys.log
```

---

## 2. Common Incident Playbooks

### Playbook 1: RFID Security Gate Sounds Alarm for Checked-Out Item
- **Symptom**: Patron exits with a book checked out at desk; gate buzzer triggers alarm.
- **Probable Cause**: Desk staff station failed to disarm the RFID tag EAS security bit (`0x01`).
- **Resolution**:
  1. Inspect the item in **RFID Staff Station** (`/api/rfid/tag/{tag_uid}`).
  2. Verify `eas_status`. If `0` (Armed), place item on staff station and trigger manual disarm or re-process check-out.
  3. Ensure antenna pad is free of metal interference during desk checkout.

### Playbook 2: Patron Blocked from Check-Out with Fine Warning
- **Symptom**: Check-out returns `403 Forbidden` - "Member fine balance ($15.50) exceeds maximum allowed threshold ($10.00)".
- **Resolution**:
  1. Direct patron to circulation desk.
  2. Open **Member Management** -> search member ID.
  3. Process fine payment (e.g. $10.00 cash or card payment).
  4. Balance will reduce below the policy ceiling, immediately restoring checkout privileges.

### Playbook 3: Migration Batch Contains Rejected Rows
- **Symptom**: During 20,000 record spreadsheet import, reconciliation indicates rejected rows (e.g., 100 invalid, 50 duplicates).
- **Resolution**:
  1. Click **View Errors** in Migration Wizard or query `/api/migration/errors/{batch_id}`.
  2. Review the row index and exact defect message (e.g., `Missing mandatory 'barcode'`, `Duplicate barcode 'BC-MIG-000100'`).
  3. The valid records (19,850) can be committed safely while invalid rows are returned to the catalog team for source spreadsheet correction.

### Playbook 4: Database Lock or Slow Query Response
- **Symptom**: SQLite database busy timeout.
- **Resolution**:
  1. Confirm Write-Ahead Logging (WAL) is enabled:
     ```sql
     PRAGMA journal_mode; -- Must return 'wal'
     ```
  2. If locked by a hung process, restart the AISYS Windows background service. The WAL checkpoint will automatically reconcile uncommitted frames.
