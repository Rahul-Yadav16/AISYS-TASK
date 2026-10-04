"""
Security Gate monitoring and alarm API routes for AISYS.
Handles unauthorized exit events, offline EAS reading, alarm generation,
CCTV image retrieval, and notification dispatch.
Fulfills FR 07, AC 06.
"""
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.middleware.security_gate import SecurityGateService
from src.core.database import db_manager

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CAPTURES_DIR = BASE_DIR / "storage" / "cctv_captures"

router = APIRouter(prefix="/api/gate", tags=["Security Gate"])

class GatePassageRequest(BaseModel):
    gate_id: str = "GATE-01"
    detected_tag_uid: Optional[str] = None
    raw_eas_bit: Optional[int] = None # 0 = Armed (unissued), 1 = Disarmed (issued)
    is_offline_simulation: bool = False

class FootfallRequest(BaseModel):
    gate_id: str = "GATE-01"
    count: int = 1

@router.post("/passage")
def process_passage(req: GatePassageRequest):
    """
    Simulates passage through security gate.
    If an unissued item passes, triggers alarm, captures CCTV snapshot, and queues email.
    Fulfills FR 07, AC 06.
    """
    return SecurityGateService.process_passage_event(
        gate_id=req.gate_id,
        detected_tag_uid=req.detected_tag_uid,
        raw_eas_bit=req.raw_eas_bit,
        is_offline_simulation=req.is_offline_simulation
    )

@router.post("/footfall")
def record_footfall(req: FootfallRequest):
    """
    Records pedestrian footfall traffic.
    """
    count = SecurityGateService.record_footfall(req.gate_id, req.count)
    return {"success": True, "gate_id": req.gate_id, "recorded_footfall": count}

@router.get("/events")
def get_gate_events(
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Retrieves recent security gate violation and footfall events.
    """
    if event_type:
        return db_manager.execute_query("""
            SELECT * FROM gate_security_events
            WHERE event_type = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (event_type.upper(), limit))
    return db_manager.execute_query("""
        SELECT * FROM gate_security_events
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))

@router.get("/cctv/{filename}")
def get_cctv_image(filename: str):
    """
    Serves mock CCTV surveillance snapshots.
    """
    file_path = CAPTURES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CCTV capture not found.")
    return FileResponse(str(file_path), media_type="image/jpeg")
