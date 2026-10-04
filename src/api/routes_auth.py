"""
Authentication and session API routes for AISYS.
Supports standard username/password login and fast contactless smart card tap-login.
Fulfills FR 11, AC 07.
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from src.core.database import db_manager
from src.core.security import (
    create_session, get_session, hash_password, revoke_session,
    verify_password, UserSession
)
from src.middleware.smart_card import SmartCardService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class SmartCardLoginRequest(BaseModel):
    smart_card_uid: str

@router.post("/login")
def login(req: LoginRequest):
    user = db_manager.execute_one(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (req.username.strip(),)
    )
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    session = create_session(
        user_id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"]
    )
    return {
        "success": True,
        "token": session.token,
        "user_id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "expires_at": session.expires_at.isoformat()
    }

@router.post("/smart-card-login")
def smart_card_login(req: SmartCardLoginRequest):
    """
    Staff smart card tap-login provider. Fulfills AC 07.
    """
    try:
        return SmartCardService.staff_login_by_card(req.smart_card_uid)
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))

@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid.")
    token = authorization.split(" ")[1]
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    return session.model_dump()

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        revoke_session(token)
    return {"success": True, "message": "Logged out successfully."}
