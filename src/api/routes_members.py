"""
Member and patron API routes for AISYS.
Handles patron accounts, smart card personalization, administrative blocks, and fines.
Fulfills FR 04.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.services.member_service import MemberService, MemberCreate
from src.services.fines_service import FinesService
from src.core.database import db_manager

router = APIRouter(prefix="/api/members", tags=["Members & Patrons"])

class PersonalizeCardRequest(BaseModel):
    member_id: str
    smart_card_uid: str

class BlockStatusRequest(BaseModel):
    member_id: str
    is_blocked: bool
    reason: Optional[str] = None

class PayFineRequest(BaseModel):
    member_id: str
    amount: float
    payment_method: str = "CASH"

@router.get("/")
def list_members(
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    if q:
        sql = """
            SELECT * FROM members
            WHERE member_id LIKE ? OR full_name LIKE ? OR smart_card_uid LIKE ?
            ORDER BY id DESC LIMIT ? OFFSET ?
        """
        pattern = f"%{q}%"
        return db_manager.execute_query(sql, (pattern, pattern, pattern, limit, offset))
    return db_manager.execute_query("SELECT * FROM members ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))

@router.post("/")
def create_member(data: MemberCreate):
    try:
        mem_id = MemberService.create_member(data)
        return {"success": True, "id": mem_id, "member_id": data.member_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{member_id}")
def get_member(member_id: str):
    member = MemberService.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    return member

@router.post("/personalize-card")
def personalize_card(req: PersonalizeCardRequest):
    """
    Binds an RFID contactless card to a patron. Fulfills FR 04.
    """
    try:
        MemberService.personalize_card(req.member_id, req.smart_card_uid)
        return {"success": True, "message": f"Smart card '{req.smart_card_uid}' bound to member '{req.member_id}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/block-status")
def set_block_status(req: BlockStatusRequest):
    """
    Toggles member blocked status. Fulfills FR 04, AC 04.
    """
    try:
        MemberService.set_block_status(req.member_id, req.is_blocked, req.reason)
        status_txt = "blocked" if req.is_blocked else "unblocked"
        return {"success": True, "message": f"Member '{req.member_id}' has been {status_txt}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{member_id}/fines")
def get_member_fines(member_id: str):
    try:
        return FinesService.get_member_fines(member_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/pay-fine")
def pay_fine(req: PayFineRequest):
    try:
        return FinesService.pay_fine(req.member_id, req.amount, payment_method=req.payment_method)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
