"""
Test suite for Hot Backup, Disaster Recovery, and Resilience.
Verifies NFR 01, AC 10.
"""
from src.core.database import db_manager
from tools.db_backup_restore import create_backup, verify_and_restore

def test_restore_after_failed_migration():
    """
    Tests priority acceptance scenario AC 10:
    Restore from backup after a simulated failed migration or integration change
    and prove that the original data remains intact.
    """
    # 1. Take Hot Database Backup
    initial_counts = db_manager.execute_one("""
        SELECT
            (SELECT COUNT(*) FROM bibliographic_records) as bibs,
            (SELECT COUNT(*) FROM items) as items,
            (SELECT COUNT(*) FROM members) as members
    """)
    backup_manifest = create_backup()
    backup_file = backup_manifest["backup_path"]
    assert backup_manifest["sha256"] is not None

    # 2. Simulate Corrupting/Accidental Insertion & Changes
    with db_manager.transaction() as conn:
        conn.execute("INSERT INTO members (member_id, full_name) VALUES ('CORRUPT-MEM', 'Corrupt User')")
        conn.execute("INSERT INTO bibliographic_records (title, author, call_number) VALUES ('Corrupt Title', 'Unknown', '000 COR')")

    # Verify counts are altered
    corrupt_counts = db_manager.execute_one("SELECT COUNT(*) as c FROM members WHERE member_id = 'CORRUPT-MEM'")
    assert corrupt_counts["c"] == 1

    # 3. Restore Database from Verified Backup
    restored = verify_and_restore(backup_file)
    assert restored is True

    # 4. Verify original data remains 100% intact
    post_restore_counts = db_manager.execute_one("""
        SELECT
            (SELECT COUNT(*) FROM bibliographic_records) as bibs,
            (SELECT COUNT(*) FROM items) as items,
            (SELECT COUNT(*) FROM members) as members
    """)
    assert post_restore_counts["bibs"] == initial_counts["bibs"]
    assert post_restore_counts["items"] == initial_counts["items"]
    assert post_restore_counts["members"] == initial_counts["members"]

    # Ensure corrupt records do not exist
    assert db_manager.execute_one("SELECT COUNT(*) as c FROM members WHERE member_id = 'CORRUPT-MEM'")["c"] == 0
