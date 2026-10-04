"""
Circulation service for AISYS.
Enforces institutional lending rules, fine limits, reference material blocking,
and coordinates RFID tag EAS bit manipulation upon issue/return.
Fulfills FR 04, AC 03, AC 04.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.config import get_config
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger
from src.middleware.staff_station import StaffStationService

class CirculationService:
    @staticmethod
    def checkout_item(
        member_identifier: str,
        item_identifier: str, # Barcode, Accession number, or RFID Tag UID
        operator_id: Optional[int] = None,
        override_policy: bool = False
    ) -> Dict[str, Any]:
        """
        Executes check-out transaction with strict policy validation.
        Fulfills FR 04, AC 03, AC 04.
        """
        cfg = get_config()
        policy = cfg.circulation_policy

        # 1. Resolve Member
        member = db_manager.execute_one("""
            SELECT * FROM members
            WHERE member_id = ? OR smart_card_uid = ?
        """, (member_identifier, member_identifier))

        if not member:
            raise ValueError(f"Patron '{member_identifier}' could not be found.")

        # 2. Policy Check: Blocked Member (AC 04)
        if policy.enforce_member_blocking and member["is_blocked"]:
            reason = member["block_reason"] or "Administrative hold"
            AuditService.log(
                action="CIRCULATION_DENIED_MEMBER_BLOCKED",
                entity="MEMBER",
                entity_id=member["member_id"],
                user_id=operator_id,
                details={"reason": reason}
            )
            raise PermissionError(f"Borrowing blocked for member '{member['member_id']}': {reason}")

        # 3. Policy Check: Fine Limit Ceiling (AC 04)
        if member["current_fines"] > policy.max_fine_limit:
            AuditService.log(
                action="CIRCULATION_DENIED_FINE_EXCEEDED",
                entity="MEMBER",
                entity_id=member["member_id"],
                user_id=operator_id,
                details={"current_fines": member["current_fines"], "limit": policy.max_fine_limit}
            )
            raise PermissionError(
                f"Borrowing blocked: Member fine balance (${member['current_fines']:.2f}) "
                f"exceeds maximum allowed threshold (${policy.max_fine_limit:.2f})."
            )

        # 4. Resolve Item
        item = db_manager.execute_one("""
            SELECT i.*, b.title, b.author, b.call_number, b.is_reference, b.material_type,
                   r.tag_uid, r.eas_status
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.barcode = ? OR i.accession_number = ? OR r.tag_uid = ?
        """, (item_identifier, item_identifier, item_identifier))

        if not item:
            raise ValueError(f"Item '{item_identifier}' could not be identified.")

        # 5. Policy Check: Reference Material Restriction (AC 04)
        if policy.enforce_reference_restriction and item["is_reference"]:
            AuditService.log(
                action="CIRCULATION_DENIED_REFERENCE_RESTRICTED",
                entity="ITEM",
                entity_id=item["accession_number"],
                user_id=operator_id,
                details={"title": item["title"], "call_number": item["call_number"]}
            )
            raise PermissionError(
                f"Item '{item['accession_number']}' is designated as REFERENCE MATERIAL and cannot be checked out."
            )

        # 6. Check Item Availability
        if item["status"] != "AVAILABLE":
            raise ValueError(f"Item '{item['accession_number']}' is currently '{item['status']}' and not available for check-out.")

        # 7. Calculate Due Date
        now_dt = datetime.now(timezone.utc)
        due_dt = now_dt + timedelta(days=policy.loan_period_days)
        issue_date_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        due_date_str = due_dt.strftime("%Y-%m-%d %H:%M:%S")

        with db_manager.transaction() as conn:
            # Create loan transaction
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO circulation_transactions (
                    item_id, member_id, operator_id, transaction_type,
                    issue_date, due_date, status
                ) VALUES (?, ?, ?, 'ISSUE', ?, ?, 'ACTIVE')
            """, (item["id"], member["id"], operator_id, issue_date_str, due_date_str))
            tx_id = cursor.lastrowid

            # Update item status
            conn.execute("UPDATE items SET status = 'ISSUED' WHERE id = ?", (item["id"],))

            # Disarm RFID Tag EAS bit (EAS = 1 / Disarmed)
            if item["tag_uid"]:
                conn.execute("""
                    UPDATE rfid_tags
                    SET eas_status = 1, last_scanned_at = ?, last_reader_id = 'STAFF-READER-01'
                    WHERE tag_uid = ?
                """, (issue_date_str, item["tag_uid"]))

        # Also signal the physical / mock staff station hardware to disarm EAS bit
        if item["tag_uid"]:
            StaffStationService.disarm_eas(item["tag_uid"])

        AuditService.log(
            action="CHECKOUT_ITEM",
            entity="CIRCULATION",
            entity_id=str(tx_id),
            user_id=operator_id,
            details={
                "member_id": member["member_id"],
                "accession_number": item["accession_number"],
                "title": item["title"],
                "due_date": due_date_str,
                "eas_disarmed": bool(item["tag_uid"])
            }
        )

        return {
            "success": True,
            "transaction_id": tx_id,
            "transaction_type": "ISSUE",
            "member_id": member["member_id"],
            "patron_name": member["full_name"],
            "accession_number": item["accession_number"],
            "title": item["title"],
            "due_date": due_date_str,
            "eas_status": 1,
            "message": f"Successfully issued '{item['title']}' to {member['full_name']} until {due_date_str[:10]}."
        }

    @staticmethod
    def checkin_item(
        item_identifier: str,
        operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes check-in return transaction.
        Calculates overdue fines, rearms RFID EAS security bit to 0 (Armed),
        and updates item status to AVAILABLE.
        Fulfills FR 04, AC 03.
        """
        cfg = get_config()
        now_dt = datetime.now(timezone.utc)
        return_date_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        item = db_manager.execute_one("""
            SELECT i.*, b.title, b.author, r.tag_uid, r.eas_status
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.barcode = ? OR i.accession_number = ? OR r.tag_uid = ?
        """, (item_identifier, item_identifier, item_identifier))

        if not item:
            raise ValueError(f"Item '{item_identifier}' could not be identified.")

        # Find active transaction
        active_tx = db_manager.execute_one("""
            SELECT ct.*, m.member_id, m.full_name
            FROM circulation_transactions ct
            JOIN members m ON ct.member_id = m.id
            WHERE ct.item_id = ? AND ct.status = 'ACTIVE'
        """, (item["id"],))

        fine_assessed = 0.00
        days_overdue = 0

        with db_manager.transaction() as conn:
            if active_tx:
                # Assess overdue fines
                due_dt = datetime.strptime(active_tx["due_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if now_dt > due_dt:
                    days_overdue = max(1, (now_dt - due_dt).days)
                    fine_assessed = round(days_overdue * cfg.circulation_policy.daily_fine_rate, 2)
                    # Add fine to member balance
                    conn.execute("""
                        UPDATE members SET current_fines = current_fines + ? WHERE id = ?
                    """, (fine_assessed, active_tx["member_id"]))

                # Mark transaction completed
                conn.execute("""
                    UPDATE circulation_transactions
                    SET return_date = ?, status = 'RETURNED', fine_amount = ?, fine_paid = ?
                    WHERE id = ?
                """, (return_date_str, fine_assessed, 0 if fine_assessed > 0 else 1, active_tx["id"]))

            # Set item status to AVAILABLE
            conn.execute("UPDATE items SET status = 'AVAILABLE' WHERE id = ?", (item["id"],))

            # Rearm RFID Tag EAS bit (EAS = 0 / Armed)
            if item["tag_uid"]:
                conn.execute("""
                    UPDATE rfid_tags
                    SET eas_status = 0, last_scanned_at = ?, last_reader_id = 'STAFF-READER-01'
                    WHERE tag_uid = ?
                """, (return_date_str, item["tag_uid"]))

        # Rearm physical / mock reader
        if item["tag_uid"]:
            StaffStationService.arm_eas(item["tag_uid"])

        AuditService.log(
            action="CHECKIN_ITEM",
            entity="CIRCULATION",
            entity_id=str(active_tx["id"] if active_tx else item["id"]),
            user_id=operator_id,
            details={
                "accession_number": item["accession_number"],
                "title": item["title"],
                "fine_assessed": fine_assessed,
                "days_overdue": days_overdue,
                "eas_rearmed": bool(item["tag_uid"])
            }
        )

        return {
            "success": True,
            "accession_number": item["accession_number"],
            "title": item["title"],
            "status": "AVAILABLE",
            "fine_assessed": fine_assessed,
            "days_overdue": days_overdue,
            "eas_status": 0,
            "shelf_destination": item["shelf_location"],
            "message": f"Successfully returned '{item['title']}'. Tag EAS armed."
        }

    @staticmethod
    def renew_item(
        item_identifier: str,
        operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extends due date for active loan. Fulfills FR 04, AC 03.
        """
        cfg = get_config()
        now_dt = datetime.now(timezone.utc)

        item = db_manager.execute_one("""
            SELECT i.id, i.accession_number, b.title, r.tag_uid
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.barcode = ? OR i.accession_number = ? OR r.tag_uid = ?
        """, (item_identifier, item_identifier, item_identifier))

        if not item:
            raise ValueError(f"Item '{item_identifier}' not found.")

        active_tx = db_manager.execute_one("""
            SELECT ct.*, m.member_id, m.full_name, m.is_blocked, m.current_fines
            FROM circulation_transactions ct
            JOIN members m ON ct.member_id = m.id
            WHERE ct.item_id = ? AND ct.status = 'ACTIVE'
        """, (item["id"],))

        if not active_tx:
            raise ValueError(f"No active loan found for item '{item['accession_number']}'.")

        if active_tx["is_blocked"]:
            raise PermissionError("Renewal rejected: Member account is blocked.")

        if active_tx["renewal_count"] >= cfg.circulation_policy.max_renewals:
            raise PermissionError(f"Maximum renewal limit of {cfg.circulation_policy.max_renewals} has been reached.")

        current_due = datetime.strptime(active_tx["due_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        base_date = max(now_dt, current_due)
        new_due = base_date + timedelta(days=cfg.circulation_policy.loan_period_days)
        new_due_str = new_due.strftime("%Y-%m-%d %H:%M:%S")

        db_manager.execute_mutation("""
            UPDATE circulation_transactions
            SET due_date = ?, renewal_count = renewal_count + 1
            WHERE id = ?
        """, (new_due_str, active_tx["id"]))

        AuditService.log(
            action="RENEW_ITEM",
            entity="CIRCULATION",
            entity_id=str(active_tx["id"]),
            user_id=operator_id,
            details={"accession_number": item["accession_number"], "new_due_date": new_due_str}
        )

        return {
            "success": True,
            "transaction_id": active_tx["id"],
            "accession_number": item["accession_number"],
            "title": item["title"],
            "new_due_date": new_due_str,
            "renewal_count": active_tx["renewal_count"] + 1,
            "message": f"Loan renewed. New due date is {new_due_str[:10]}."
        }
