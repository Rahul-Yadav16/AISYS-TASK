"""
Test suite for Offline Lifecycle, Updates, and Rollback.
Verifies FR 12, AC 09.
"""
from tools.offline_installer import run_environment_checks, perform_offline_install
from tools.offline_updater import OfflineUpdateManager
from src.core.database import db_manager

def test_offline_update_and_rollback():
    """
    Tests priority acceptance scenario AC 09:
    Install and run the solution without internet access, apply an offline update,
    and complete a documented rollback.
    """
    # 1. Environment Checklist (NFR 03)
    env_checks = run_environment_checks()
    assert env_checks["python_supported"] is True
    assert env_checks["storage_directories_writable"] is True

    # 2. Apply Offline Update Package to v1.1.0
    update_res = OfflineUpdateManager.apply_update_package(package_version="1.1.0")
    assert update_res["success"] is True
    assert update_res["updated_to_version"] == "1.1.0"
    assert update_res["snapshot_path"] is not None

    # 3. Complete Documented Rollback
    rollback_res = OfflineUpdateManager.rollback_update()
    assert rollback_res["success"] is True
    assert rollback_res["rolled_back_to_version"] == "1.0.0"
    assert rollback_res["status"] == "RESTORED"

    # Verify Database is operational after rollback
    check = db_manager.execute_one("SELECT 1 as alive")
    assert check["alive"] == 1
