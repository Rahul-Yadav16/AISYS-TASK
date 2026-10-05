"""
Administration, Health Diagnostics, and System Lifecycle API routes for AISYS.
Supports liveness probes, software version reporting, audit logging,
hot database backups, and offline updates.
Fulfills FR 11, FR 12, NFR 01, NFR 07, AC 09, AC 10.
"""
import shutil
import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.core.config import get_config
from src.core.database import db_manager
from src.core.audit import AuditService
from tools.offline_updater import OfflineUpdateManager
from tools.db_backup_restore import create_backup, verify_and_restore

BASE_DIR = Path(__file__).resolve().parent.parent.parent

router = APIRouter(prefix="/api/admin", tags=["Administration & Operations"])

class ApplyUpdateRequest(BaseModel):
    version: str = "1.1.0"

class RestoreBackupRequest(BaseModel):
    backup_file: str

@router.get("/health")
def get_system_health():
    """
    Comprehensive health check diagnostic endpoint.
    Fulfills FR 11, NFR 07.
    """
    cfg = get_config()
    db_ok = True
    db_error = None
    try:
        db_manager.execute_one("SELECT 1")
    except Exception as e:
        db_ok = False
        db_error = str(e)

    # Disk Space Check
    base_dir = Path(__file__).resolve().parent.parent.parent
    stat = shutil.disk_usage(str(base_dir))
    free_gb = round(stat.free / (1024 ** 3), 2)

    return {
        "status": "HEALTHY" if db_ok else "UNHEALTHY",
        "system_name": cfg.system.institution_name,
        "environment": cfg.system.environment,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "database": {
            "status": "CONNECTED" if db_ok else "DISCONNECTED",
            "db_path": db_manager.db_path,
            "wal_mode": cfg.database.wal_mode,
            "error": db_error
        },
        "storage": {
            "free_disk_space_gb": free_gb,
            "status": "ADEQUATE" if free_gb >= 1.0 else "LOW"
        },
        "rfid_middleware": {
            "mock_mode": cfg.rfid_middleware.mock_mode,
            "offline_gate_security_bit_check": cfg.rfid_middleware.offline_gate_security_bit_check
        }
    }

@router.get("/version")
def get_software_version():
    """
    Software-version and system information reporting. Fulfills FR 11.
    """
    applied = db_manager.execute_query("SELECT version, applied_at FROM schema_migrations ORDER BY applied_at ASC")
    return {
        "application_name": "AISYS RFID-Enabled Library Solution",
        "version": "1.0.0",
        "build_date": "2026-10-04",
        "schema_version": applied[-1]["version"] if applied else "V1__initial_schema",
        "migrations_history": applied
    }

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Immutable system audit log query. Fulfills FR 11, NFR 02.
    """
    return AuditService.get_logs(limit=limit, offset=offset)

@router.post("/backup")
def trigger_hot_backup():
    """
    Executes an atomic online hot database backup. Fulfills NFR 01, AC 10.
    """
    try:
        manifest = create_backup()
        return {"success": True, "manifest": manifest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore")
def trigger_restore(req: RestoreBackupRequest):
    """
    Restores database from backup snapshot. Fulfills AC 10.
    """
    try:
        verify_and_restore(req.backup_file)
        return {"success": True, "message": "Database restored and verified successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/apply-update")
def apply_offline_update(req: ApplyUpdateRequest):
    """
    Applies offline update package and patches. Fulfills FR 12, AC 09.
    """
    try:
        result = OfflineUpdateManager.apply_update_package(req.version)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback-update")
def rollback_offline_update():
    """
    Rolls back to pre-update snapshot. Fulfills FR 12, AC 09.
    """
    try:
        result = OfflineUpdateManager.rollback_update()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documentation-pdf")
def download_documentation_pdf():
    """
    Serves the publication-ready comprehensive documentation PDF.
    """
    pdf_path = BASE_DIR / "docs" / "AISYS_Comprehensive_Documentation.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Documentation PDF not found.")
    from fastapi.responses import FileResponse
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename="AISYS_Comprehensive_Documentation.pdf"
    )
