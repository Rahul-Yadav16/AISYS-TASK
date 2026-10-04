"""
Test suite for Controlled 20,000 Record Migration and Reconciliation.
Verifies FR 10, NFR 01, AC 01, AC 10.
"""
from pathlib import Path
from src.services.migration_service import MigrationService
from src.core.database import db_manager
from src.services.search_service import SearchService

SAMPLE_CSV = "data/sample_import_20000.csv"

def test_migration_20k_reconciliation():
    """
    Tests priority acceptance scenario AC 01:
    Import a supplied spreadsheet into staging, reject invalid rows,
    identify duplicates, migrate valid records, and reconcile source and target counts.
    """
    assert Path(SAMPLE_CSV).exists()

    # Get baseline count of catalog
    initial_bib_count = db_manager.execute_one("SELECT COUNT(*) as c FROM bibliographic_records")["c"]
    initial_items_count = db_manager.execute_one("SELECT COUNT(*) as c FROM items")["c"]

    # 1. Stage Ingestion & Pre-Migration Hot Backup
    ingest_res = MigrationService.ingest_spreadsheet(SAMPLE_CSV)
    batch_id = ingest_res["batch_id"]
    assert ingest_res["total_rows_ingested"] == 20000
    assert Path(ingest_res["pre_migration_backup"]).exists()

    # 2. Validation & Duplicate Detection
    report = MigrationService.validate_and_profile_batch(batch_id)
    assert report["total_rows_profiled"] == 20000
    assert report["valid_records"] == 19850
    assert report["invalid_records"] == 100
    assert report["duplicate_records"] == 50
    assert report["reconciliation_checksum_match"] is True

    # Verify error log has exact failure details
    errors = MigrationService.get_batch_errors(batch_id)
    assert len(errors) == 150 # 100 invalid + 50 duplicates

    # 3. Commit Migration into Production Database
    commit_res = MigrationService.commit_migration(batch_id)
    assert commit_res["success"] is True
    assert commit_res["migrated_records"] == 19850

    # Verify database counts increased by exactly 19,850
    new_bib_count = db_manager.execute_one("SELECT COUNT(*) as c FROM bibliographic_records")["c"]
    new_items_count = db_manager.execute_one("SELECT COUNT(*) as c FROM items")["c"]
    assert new_bib_count == initial_bib_count + 19850
    assert new_items_count == initial_items_count + 19850

    # Verify FTS5 real-time search indexing
    search_res = SearchService.search("Principles")
    assert search_res["total"] > 100

    # 4. Atomic Rollback Verification
    rollback_res = MigrationService.rollback_migration(batch_id)
    assert rollback_res["success"] is True
    assert rollback_res["deleted_items"] == 19850

    # Verify counts restored to EXACT initial baseline without data corruption (NFR 01)
    restored_bib_count = db_manager.execute_one("SELECT COUNT(*) as c FROM bibliographic_records")["c"]
    restored_items_count = db_manager.execute_one("SELECT COUNT(*) as c FROM items")["c"]
    assert restored_bib_count == initial_bib_count
    assert restored_items_count == initial_items_count
