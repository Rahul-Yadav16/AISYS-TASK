# Deliverable D7: Hot Backup & Disaster Recovery Runbook

## 1. Objective
Ensure zero data loss and deterministic disaster recovery for the library catalog, RFID tag bindings, member profiles, and circulation history.

---

## 2. Taking an Online Hot Database Backup
The backup utility leverages SQLite's online backup API, ensuring active circulation desks, gate event monitors, and inventory sweeps can continue uninterrupted without locking the database.

### Command:
```powershell
python tools/db_backup_restore.py --backup
```

### Output Artifacts:
- Database snapshot: `storage/backups/aisys_backup_YYYYMMDD_HHMMSS.db`
- Integrity manifest: `storage/backups/aisys_backup_YYYYMMDD_HHMMSS.json`

### Sample Manifest:
```json
{
  "backup_file": "aisys_backup_20261004_135321.db",
  "backup_path": "storage/backups/aisys_backup_20261004_135321.db",
  "sha256": "b059aa4fa82d392c3ccf0dc35bc768e617c01ae8d5f4ab0b00be6afd17593411",
  "created_at": "2026-10-04T13:53:21Z",
  "database_counts": {
    "bibliographic_records": 5,
    "items": 6,
    "members": 5,
    "rfid_tags": 5
  }
}
```

---

## 3. Disaster Recovery Restoration Procedure
In the event of accidental operational mistakes, failed migration batches, or hardware failures:

### Step 1: Locate Target Backup
Identify the most recent verified backup file in `storage/backups/`.

### Step 2: Execute Restore Command
```powershell
python tools/db_backup_restore.py --restore storage/backups/aisys_backup_20261004_135321.db
```

### Step 3: Verification Checks
1. The tool recalculates the file SHA-256 and compares it against the manifest.
2. The SQLite backup engine synchronizes database pages into the active database path.
3. System checks record counts and validates that pre-incident data is 100% restored.
4. An immutable entry is written to `audit_logs` logging the restoration action.
