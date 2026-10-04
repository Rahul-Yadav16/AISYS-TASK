"""
Migration API routes for AISYS.
Supports controlled staging ingestion of ~20,000 records, validation profiling,
duplicate detection, reconciliation, atomic commit, and rollback.
Fulfills FR 10, NFR 01, AC 01, AC 10.
"""
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from src.services.migration_service import MigrationService
from src.core.database import db_manager

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "storage" / "staging"

router = APIRouter(prefix="/api/migration", tags=["Data Migration"])

class IngestFileRequest(BaseModel):
    filepath: str

@router.get("/batches")
def list_batches():
    return db_manager.execute_query("SELECT * FROM migration_batches ORDER BY started_at DESC")

@router.post("/upload")
async def upload_migration_file(file: UploadFile = File(...)):
    """
    Uploads a source spreadsheet/CSV file to staging.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    target_path = STAGING_DIR / file.filename
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest into staging
    result = MigrationService.ingest_spreadsheet(str(target_path))
    return result

@router.post("/ingest-local")
def ingest_local_file(req: IngestFileRequest):
    """
    Ingests a pre-generated spreadsheet file (e.g. data/sample_import_20000.csv).
    Fulfills AC 01.
    """
    try:
        return MigrationService.ingest_spreadsheet(req.filepath)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate/{batch_id}")
def validate_batch(batch_id: str):
    """
    Executes row-level validation and produces reconciliation report.
    Fulfills AC 01.
    """
    try:
        return MigrationService.validate_and_profile_batch(batch_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/errors/{batch_id}")
def get_batch_errors(batch_id: str):
    """
    Retrieves row error details and rejection reasons for a batch.
    Fulfills FR 10.
    """
    return MigrationService.get_batch_errors(batch_id)

@router.post("/commit/{batch_id}")
def commit_batch(batch_id: str):
    """
    Commits valid records into production tables with real-time FTS5 indexing.
    Fulfills AC 01.
    """
    try:
        return MigrationService.commit_migration(batch_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback/{batch_id}")
def rollback_batch(batch_id: str):
    """
    Performs atomic rollback of migrated batch, leaving existing records intact.
    Fulfills AC 01, AC 10, NFR 01.
    """
    try:
        return MigrationService.rollback_migration(batch_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
