"""
Smart card authentication and patron identification service for AISYS.
Supports contactless Mifare / DESFire card tap-login for staff and patron profile lookup.
Fulfills FR 04, FR 11, AC 07.
"""
from typing import Any, Dict, Optional
from src.core.database import db_manager
from src.core.security import create_session, UserSession
from src.core.audit import AuditService
from src.core.logger import logger

class SmartCardService:
    @staticmethod
    def staff_login_by_card(smart_card_uid: str) -> Dict[str, Any]:
        """
        Authenticates a staff member via contactless smart card tap.
        Enforces role-based permissions and issues an active session token.
        Fulfills AC 07.
        """
        user = db_manager.execute_one("""
            SELECT * FROM users
            WHERE smart_card_uid = ? AND is_active = 1
        """, (smart_card_uid.strip(),))

        if not user:
            logger.warning(f"Unrecognized or inactive smart card UID presented: {smart_card_uid}")
            AuditService.log(
                action="FAILED_SMART_CARD_LOGIN",
                entity="USER",
                details={"smart_card_uid": smart_card_uid}
            )
            raise PermissionError(f"Smart card UID '{smart_card_uid}' is not recognized or user account is disabled.")

        session: UserSession = create_session(
            user_id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            role=user["role"],
            smart_card_uid=smart_card_uid
        )

        AuditService.log(
            action="SMART_CARD_LOGIN_SUCCESS",
            entity="USER",
            entity_id=str(user["id"]),
            user_id=user["id"],
            details={"username": user["username"], "role": user["role"], "card_uid": smart_card_uid}
        )

        logger.info(f"Staff member {user['username']} logged in via smart card (Role: {user['role']})")

        return {
            "success": True,
            "token": session.token,
            "user_id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "smart_card_uid": smart_card_uid,
            "expires_at": session.expires_at.isoformat()
        }

    @staticmethod
    def identify_card(smart_card_uid: str) -> Dict[str, Any]:
        """
        Identifies whether a tapped smart card belongs to a staff member or a library member/patron.
        """
        clean_uid = smart_card_uid.strip()

        # Check Staff Users first
        user = db_manager.execute_one(
            "SELECT id, username, full_name, role FROM users WHERE smart_card_uid = ? AND is_active = 1",
            (clean_uid,)
        )
        if user:
            return {
                "type": "STAFF",
                "smart_card_uid": clean_uid,
                "user_id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"]
            }

        # Check Patrons / Members
        member = db_manager.execute_one(
            "SELECT id, member_id, full_name, category, is_blocked, current_fines FROM members WHERE smart_card_uid = ?",
            (clean_uid,)
        )
        if member:
            return {
                "type": "PATRON",
                "smart_card_uid": clean_uid,
                "member_id": member["member_id"],
                "full_name": member["full_name"],
                "category": member["category"],
                "is_blocked": bool(member["is_blocked"]),
                "current_fines": member["current_fines"]
            }

        return {
            "type": "UNREGISTERED",
            "smart_card_uid": clean_uid,
            "message": "Card UID is unassigned."
        }
