# Deliverable D6: Defect Tracking & Resolution Log

This log records defects identified during integration testing, root cause analyses, applied fixes, and retest verification evidence.

---

### Defect DEF-01: NCIP XML Namespace Parsing Failed for Child Elements
- **Severity**: High
- **Requirement / Acceptance ID**: FR 03, AC 03
- **Component**: `src/adapters/ncip_adapter.py`
- **Owner**: Integration Engineer
- **Status**: **RESOLVED & VERIFIED**
- **Reproduction Steps**:
  1. Send XML request with qualified namespace `xmlns:ns1="http://www.niso.org/2000/inclusion"`.
  2. Invoke `process_xml_message(xml_string)`.
  3. Parser was executing `action_elem.find(".//UserId")` which expected an unqualified tag name.
  4. Response returned: `Patron '' could not be found.`
- **Root Cause**: Qualified XML elements include namespace prefixes in ElementTree (e.g. `{http://www.niso.org/2000/inclusion}UserId`), failing exact string lookup.
- **Fix Implemented**: Updated parser to traverse elements using `.iter()` and evaluate `elem.tag.split("}")[-1]` against expected tag names.
- **Retest Evidence**: `tests/test_ncip_sip2.py::test_sip2_and_ncip_checkout_checkin` PASSED.

---

### Defect DEF-02: SQLite WAL Mode Journal Replay During Database Restore
- **Severity**: Critical
- **Requirement / Acceptance ID**: NFR 01, AC 10
- **Component**: `src/core/database.py` (`restore_backup`)
- **Owner**: Data Architect
- **Status**: **RESOLVED & VERIFIED**
- **Reproduction Steps**:
  1. Enable SQLite Write-Ahead Logging (`PRAGMA journal_mode = WAL;`).
  2. Perform database mutations.
  3. Attempt file replacement using `shutil.copy2(src, dest)`.
  4. Existing `-wal` file persisted on disk and replayed subsequent uncheckpointed mutations into the restored database.
  5. Bibliographic count was 6 instead of expected 5.
- **Root Cause**: Directly copying a database file over a WAL-journaled SQLite database without checkpointing or synchronizing open connections causes stale WAL frames to replay.
- **Fix Implemented**: Switched `restore_backup()` to use SQLite's native `sqlite3.Connection.backup()` API, properly committing and synchronizing WAL pages atomically across connections.
- **Retest Evidence**: `tests/test_backup_restore_resilience.py::test_restore_after_failed_migration` PASSED. Original database restored with 100% exact row counts.
