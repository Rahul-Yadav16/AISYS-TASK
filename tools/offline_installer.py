"""
Offline Environment Installer and Validator for AISYS.
Prepares offline air-gapped installation on Windows 11 / Windows Server 2022.
Fulfills FR 12, AC 09, D7.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.config import get_config
from src.core.database import db_manager
from data.seeds.seed_data import seed_database
from src.core.logger import logger

def run_environment_checks() -> dict:
    checks = {}
    # Check Python version
    checks["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks["python_supported"] = (sys.version_info.major == 3 and sys.version_info.minor >= 10)

    # Check Disk Space
    stat = shutil.disk_usage(str(BASE_DIR))
    free_gb = round(stat.free / (1024 ** 3), 2)
    checks["free_disk_space_gb"] = free_gb
    checks["disk_space_sufficient"] = (free_gb >= 2.0)

    # Check Required Directories
    dirs_to_verify = ["storage/backups", "storage/staging", "storage/cctv_captures", "storage/labels", "data/migrations"]
    missing_dirs = []
    for d in dirs_to_verify:
        p = BASE_DIR / d
        p.mkdir(parents=True, exist_ok=True)
        if not os.access(str(p), os.W_OK):
            missing_dirs.append(d)
    checks["storage_directories_writable"] = (len(missing_dirs) == 0)

    return checks

def perform_offline_install() -> bool:
    print("=== AISYS Offline Installer Starting ===")
    checks = run_environment_checks()
    print(f"Environment Checklist: {checks}")

    if not checks["python_supported"] or not checks["storage_directories_writable"]:
        print("Pre-requisite checks failed!")
        return False

    print("1. Initializing Database and Applying Baseline Migrations...")
    applied = db_manager.apply_migrations()
    print(f"   Applied migrations: {applied}")

    print("2. Seeding Baseline Synthetic Accounts, Catalog, and RFID Tags...")
    seed_database()
    print("   Synthetic database seed complete.")

    print("3. Generating Offline Diagnostic Verification...")
    counts = db_manager.execute_one("""
        SELECT
            (SELECT COUNT(*) FROM users) as users,
            (SELECT COUNT(*) FROM members) as members,
            (SELECT COUNT(*) FROM bibliographic_records) as titles,
            (SELECT COUNT(*) FROM items) as items,
            (SELECT COUNT(*) FROM rfid_tags) as tags
    """)
    print(f"   Database Verification: {dict(counts)}")
    print("=== AISYS Offline Installation Complete and Ready for Service ===")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AISYS Offline Installer")
    parser.add_argument("--check", action="store_true", help="Run pre-flight environment checks")
    parser.add_argument("--install", action="store_true", help="Run offline installation")
    args = parser.parse_args()

    if args.check:
        print(run_environment_checks())
    elif args.install:
        perform_offline_install()
    else:
        perform_offline_install()
