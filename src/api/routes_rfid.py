"""
RFID Staff Station and Middleware API routes for AISYS.
Handles tag validation, tag-to-item binding, EAS status queries, and device health.
Fulfills FR 03, FR 05, AC 02.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.middleware.staff_station import StaffStationService
from src.middleware.rfid_manager import rfid_manager
from src.middleware.smart_card import SmartCardService

router = APIRouter(prefix="/api/rfid", tags=["RFID Middleware & Staff Station"])

class TagItemRequest(BaseModel):
    item_identifier: str
    tag_uid: str
    operator_id: Optional[int] = None
    force_retag: bool = False

class ValidateTagItemRequest(BaseModel):
    item_identifier: str

class EasControlRequest(BaseModel):
    tag_uid: str
    armed: bool # True = Armed (0), False = Disarmed (1)

@router.get("/devices")
def get_rfid_devices():
    """
    Returns live connection and health status of all RFID hardware adapters.
    """
    return rfid_manager.get_devices()

@router.post("/validate-item")
def validate_item(req: ValidateTagItemRequest):
    """
    Validates item existence and current tagging status before tag programming.
    Fulfills FR 05.
    """
    try:
        return StaffStationService.validate_item_for_tagging(req.item_identifier)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/tag-item")
def tag_item(req: TagItemRequest):
    """
    Associates an RFID tag with an item and initializes EAS to Armed (0).
    Fulfills FR 05, AC 02.
    """
    try:
        return StaffStationService.tag_item(
            item_identifier=req.item_identifier,
            tag_uid=req.tag_uid,
            operator_id=req.operator_id,
            force_retag=req.force_retag
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/tag/{tag_uid}")
def get_tag_info(tag_uid: str):
    """
    Queries tag details and linked bibliographic metadata.
    Fulfills AC 02.
    """
    info = StaffStationService.get_tag_info(tag_uid)
    if not info:
        raise HTTPException(status_code=404, detail=f"RFID tag '{tag_uid}' not found in registry.")
    return info

@router.post("/eas-control")
def set_eas_status(req: EasControlRequest):
    """
    Manually arm or disarm tag EAS bit for staff testing.
    """
    if req.armed:
        StaffStationService.arm_eas(req.tag_uid)
        return {"success": True, "tag_uid": req.tag_uid, "eas_status": 0, "status": "ARMED"}
    else:
        StaffStationService.disarm_eas(req.tag_uid)
        return {"success": True, "tag_uid": req.tag_uid, "eas_status": 1, "status": "DISARMED"}

@router.get("/identify-card/{card_uid}")
def identify_smart_card(card_uid: str):
    """
    Quick card tap lookup for smart card reader station.
    """
    return SmartCardService.identify_card(card_uid)
