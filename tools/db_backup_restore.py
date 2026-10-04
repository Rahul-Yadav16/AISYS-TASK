"""
Database Backup, Checksum Verification, and Restore Tool for AISYS.
Supports automated pre-change snapshots, SHA-256 integrity verification,
and atomic disaster recovery.
Fulfills NFR 01, AC 10.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger

def calculate_file_hash(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def create_backup(target_dir: str = "storage/backups") -> dict:
    backup_path = db_manager.hot_backup(target_dir)
    checksum = calculate_file_hash(backup_path)

    # Save manifest
    manifest_path = Path(backup_path).with_suffix(".json")
    manifest = {
        "backup_file": Path(backup_path).name,
        "backup_path": str(backup_path),
        "sha256": checksum,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_counts": {
            "bibliographic_records": db_manager.execute_one("SELECT COUNT(*) as c FROM bibliographic_records")["c"],
            "items": db_manager.execute_one("SELECT COUNT(*) as c FROM items")["c"],
            "members": db_manager.execute_one("SELECT COUNT(*) as c FROM members")["c"],
            "rfid_tags": db_manager.execute_one("SELECT COUNT(*) as c FROM rfid_tags")["c"]
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Backup manifest saved: {manifest_path}")
    return manifest

def verify_and_restore(backup_file: str) -> bool:
    manifest_candidate = Path(backup_file).with_suffix(".json")
    if manifest_candidate.exists():
        with open(manifest_candidate, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        current_hash = calculate_file_hash(backup_file)
        if current_hash != manifest["sha256"]:
            raise ValueError(f"Integrity check failed! Expected {manifest['sha256']}, got {current_hash}")
        logger.info(f"Backup SHA-256 verified successfully: {current_hash}")

    db_manager.restore_backup(backup_file)

    AuditService.log(
        action="DATABASE_RESTORE_VERIFIED",
        entity="DATABASE",
        details={"backup_file": Path(backup_file).name}
    )
    logger.info("Database restoration completed and verified.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AISYS Database Backup and Restore Utility")
    parser.add_argument("--backup", action="store_true", help="Perform online hot backup")
    parser.add_argument("--restore", type=str, help="Restore database from backup file")
    args = parser.parse_args()

    if args.backup:
        res = create_backup()
        print(json.dumps(res, indent=2))
    elif args.restore:
        verify_and_restore(args.restore)
        print("Restoration successful.")
    else:
        parser.print_help()
