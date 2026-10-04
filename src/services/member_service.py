"""
Patron / Member management service for AISYS.
Handles registrations, card personalization, block rules, and fine tracking.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger

class MemberCreate(BaseModel):
    member_id: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    category: str = "STUDENT" # STUDENT, FACULTY, STAFF, PUBLIC
    email: Optional[str] = None
    phone: Optional[str] = None
    smart_card_uid: Optional[str] = None
    expiry_date: Optional[str] = "2028-12-31"

class MemberService:
    @staticmethod
    def create_member(data: MemberCreate, user_id: Optional[int] = None) -> int:
        existing = db_manager.execute_one(
            "SELECT id FROM members WHERE member_id = ?", (data.member_id,)
        )
        if existing:
            raise ValueError(f"Member with ID '{data.member_id}' already exists.")

        if data.smart_card_uid:
            card_exists = db_manager.execute_one(
                "SELECT id FROM members WHERE smart_card_uid = ?", (data.smart_card_uid,)
            )
            if card_exists:
                raise ValueError(f"Smart card UID '{data.smart_card_uid}' is already assigned.")

        member_db_id = db_manager.execute_mutation("""
            INSERT INTO members (member_id, full_name, category, email, phone, smart_card_uid, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data.member_id, data.full_name, data.category.upper(), data.email, data.phone, data.smart_card_uid, data.expiry_date))

        AuditService.log(
            action="CREATE_MEMBER",
            entity="MEMBER",
            entity_id=data.member_id,
            user_id=user_id,
            details={"full_name": data.full_name, "category": data.category}
        )
        return member_db_id

    @staticmethod
    def get_member(member_id: str) -> Optional[Dict[str, Any]]:
        member = db_manager.execute_one(
            "SELECT * FROM members WHERE member_id = ? OR smart_card_uid = ?",
            (member_id, member_id)
        )
        if not member:
            return None

        # Fetch active loans
        loans = db_manager.execute_query("""
            SELECT ct.*, i.accession_number, i.barcode, b.title, b.author
            FROM circulation_transactions ct
            JOIN items i ON ct.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE ct.member_id = ? AND ct.status = 'ACTIVE'
            ORDER BY ct.due_date ASC
        """, (member["id"],))

        member["active_loans"] = loans
        member["active_loans_count"] = len(loans)
        return member

    @staticmethod
    def personalize_card(member_id: str, smart_card_uid: str, user_id: Optional[int] = None) -> bool:
        """
        Associates an RFID contactless smart card with a member record.
        Fulfills FR 04 patron-card personalisation.
        """
        # Validate member exists
        member = db_manager.execute_one("SELECT id FROM members WHERE member_id = ?", (member_id,))
        if not member:
            raise ValueError(f"Member '{member_id}' not found.")

        # Check if card UID is assigned to someone else
        card_taken = db_manager.execute_one(
            "SELECT id, member_id FROM members WHERE smart_card_uid = ? AND member_id != ?",
            (smart_card_uid, member_id)
        )
        if card_taken:
            raise ValueError(f"Smart card UID '{smart_card_uid}' is already assigned to member '{card_taken['member_id']}'.")

        db_manager.execute_mutation(
            "UPDATE members SET smart_card_uid = ? WHERE member_id = ?",
            (smart_card_uid, member_id)
        )

        AuditService.log(
            action="PERSONALIZE_CARD",
            entity="MEMBER",
            entity_id=member_id,
            user_id=user_id,
            details={"smart_card_uid": smart_card_uid}
        )
        logger.info(f"Smart card {smart_card_uid} assigned to member {member_id}")
        return True

    @staticmethod
    def set_block_status(member_id: str, is_blocked: bool, reason: Optional[str] = None, user_id: Optional[int] = None) -> bool:
        """
        Blocks or unblocks a member. Fulfills FR 04 member blocking.
        """
        member = db_manager.execute_one("SELECT id FROM members WHERE member_id = ?", (member_id,))
        if not member:
            raise ValueError(f"Member '{member_id}' not found.")

        db_manager.execute_mutation("""
            UPDATE members SET is_blocked = ?, block_reason = ? WHERE member_id = ?
        """, (1 if is_blocked else 0, reason if is_blocked else None, member_id))

        AuditService.log(
            action="MEMBER_BLOCK" if is_blocked else "MEMBER_UNBLOCK",
            entity="MEMBER",
            entity_id=member_id,
            user_id=user_id,
            details={"reason": reason}
        )
        return True
