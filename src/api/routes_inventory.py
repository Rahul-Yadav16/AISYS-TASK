"""
Inventory and stock verification API routes for AISYS.
Handles shelf audit sessions, handheld wand scan bursts, misplaced item detection,
and missing item reconciliation with audible/visible event streams.
Fulfills FR 06, AC 05.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.middleware.handheld_reader import HandheldReaderService
from src.core.database import db_manager

router = APIRouter(prefix="/api/inventory", tags=["Inventory & Handheld Reader"])

class StartAuditRequest(BaseModel):
    audit_name: str
    shelf_target: str

class ScanBurstRequest(BaseModel):
    audit_id: int
    current_shelf: str
    scanned_tag_uids: List[str]

@router.get("/audits")
def list_audits(limit: int = Query(20, ge=1, le=100)):
    return db_manager.execute_query("""
        SELECT * FROM inventory_audits
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,))

@router.post("/start-audit")
def start_audit(req: StartAuditRequest):
    """
    Initializes an inventory verification audit session.
    """
    try:
        audit_id = HandheldReaderService.start_inventory_audit(
            audit_name=req.audit_name,
            shelf_target=req.shelf_target
        )
        return {
            "success": True,
            "audit_id": audit_id,
            "audit_name": req.audit_name,
            "shelf_target": req.shelf_target
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/scan-burst")
def scan_burst(req: ScanBurstRequest):
    """
    Processes a burst of tags scanned by the handheld reader.
    Computes correct vs misplaced tags and returns audio/visual event directives.
    Fulfills FR 06, AC 05.
    """
    try:
        return HandheldReaderService.process_scan_burst(
            audit_id=req.audit_id,
            scanned_tag_uids=req.scanned_tag_uids,
            current_shelf=req.current_shelf
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/finalize-audit/{audit_id}")
def finalize_audit(audit_id: int):
    """
    Finalizes shelf audit, calculates missing items, and produces reconciliation.
    Fulfills AC 05.
    """
    try:
        return HandheldReaderService.finalize_inventory_audit(audit_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
