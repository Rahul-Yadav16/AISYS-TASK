"""
Security, password hashing, token management, and RBAC enforcement for AISYS.
Uses Python's standard hashlib (PBKDF2-HMAC-SHA256) for zero external dependencies.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from pydantic import BaseModel

ROLE_HIERARCHY: Dict[str, Set[str]] = {
    "ADMIN": {"ADMIN", "LIBRARIAN", "CATALOGUER", "CIRCULATION", "PATRON"},
    "LIBRARIAN": {"LIBRARIAN", "CATALOGUER", "CIRCULATION", "PATRON"},
    "CATALOGUER": {"CATALOGUER", "PATRON"},
    "CIRCULATION": {"CIRCULATION", "PATRON"},
    "PATRON": {"PATRON"}
}

class UserSession(BaseModel):
    user_id: int
    username: str
    full_name: str
    role: str
    token: str
    expires_at: datetime
    smart_card_uid: Optional[str] = None

_active_sessions: Dict[str, UserSession] = {}

def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    iterations = 100_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{salt.hex()}${iterations}${dk.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt_hex, iterations_str, dk_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        iterations = int(iterations_str)
        expected_dk = bytes.fromhex(dk_hex)
        calculated_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(calculated_dk, expected_dk)
    except Exception:
        return False

def create_session(user_id: int, username: str, full_name: str, role: str, ttl_hours: int = 8, smart_card_uid: Optional[str] = None) -> UserSession:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    session = UserSession(
        user_id=user_id,
        username=username,
        full_name=full_name,
        role=role.upper(),
        token=token,
        expires_at=expires,
        smart_card_uid=smart_card_uid
    )
    _active_sessions[token] = session
    return session

def get_session(token: str) -> Optional[UserSession]:
    session = _active_sessions.get(token)
    if not session:
        return None
    if datetime.now(timezone.utc) > session.expires_at:
        del _active_sessions[token]
        return None
    return session

def revoke_session(token: str) -> bool:
    if token in _active_sessions:
        del _active_sessions[token]
        return True
    return False

def has_permission(user_role: str, required_role: str) -> bool:
    allowed_roles = ROLE_HIERARCHY.get(user_role.upper(), set())
    return required_role.upper() in allowed_roles
