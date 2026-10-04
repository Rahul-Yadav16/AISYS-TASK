"""
Circulation API routes for AISYS.
Handles check-out, check-in, renewals, policy rule enforcement, and active loans.
Fulfills FR 04, AC 03, AC 04.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.circulation_service import CirculationService

router = APIRouter(prefix="/api/circulation", tags=["Circulation"])

class CheckoutRequest(BaseModel):
    member_identifier: str
    item_identifier: str
    operator_id: Optional[int] = None

class CheckinRequest(BaseModel):
    item_identifier: str
    operator_id: Optional[int] = None

class RenewRequest(BaseModel):
    item_identifier: str
    operator_id: Optional[int] = None

@router.post("/checkout")
def checkout(req: CheckoutRequest):
    """
    Issues item to patron, evaluates fine ceilings and reference book restrictions,
    and disarms RFID EAS security bit. Fulfills AC 03, AC 04.
    """
    try:
        return CirculationService.checkout_item(
            member_identifier=req.member_identifier,
            item_identifier=req.item_identifier,
            operator_id=req.operator_id
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.post("/checkin")
def checkin(req: CheckinRequest):
    """
    Returns item, evaluates overdue fines, and rearms RFID EAS security bit.
    Fulfills AC 03.
    """
    try:
        return CirculationService.checkin_item(
            item_identifier=req.item_identifier,
            operator_id=req.operator_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.post("/renew")
def renew(req: RenewRequest):
    """
    Renews active item loan. Fulfills AC 03.
    """
    try:
        return CirculationService.renew_item(
            item_identifier=req.item_identifier,
            operator_id=req.operator_id
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
