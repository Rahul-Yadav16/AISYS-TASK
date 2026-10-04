"""
Fines management service for AISYS.
Supports fine calculation, cash/card payment recording, fine waivers, and receipt printing.
Fulfills FR 04, FR 08.
"""
from typing import Any, Dict, List, Optional
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger

class FinesService:
    @staticmethod
    def get_member_fines(member_id: str) -> Dict[str, Any]:
        member = db_manager.execute_one(
            "SELECT id, member_id, full_name, current_fines FROM members WHERE member_id = ?",
            (member_id,)
        )
        if not member:
            raise ValueError(f"Member '{member_id}' not found.")

        # Outstanding unpaid transactions
        unpaid_txs = db_manager.execute_query("""
            SELECT ct.id, ct.fine_amount, ct.issue_date, ct.return_date,
                   i.accession_number, b.title
            FROM circulation_transactions ct
            JOIN items i ON ct.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE ct.member_id = ? AND ct.fine_paid = 0 AND ct.fine_amount > 0
        """, (member["id"],))

        return {
            "member_id": member["member_id"],
            "full_name": member["full_name"],
            "total_fines": member["current_fines"],
            "unpaid_transactions": unpaid_txs
        }

    @staticmethod
    def pay_fine(
        member_id: str,
        amount: float,
        operator_id: Optional[int] = None,
        payment_method: str = "CASH"
    ) -> Dict[str, Any]:
        member = db_manager.execute_one(
            "SELECT id, member_id, full_name, current_fines FROM members WHERE member_id = ?",
            (member_id,)
        )
        if not member:
            raise ValueError(f"Member '{member_id}' not found.")

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        current_balance = member["current_fines"]
        new_balance = max(0.00, round(current_balance - amount, 2))

        with db_manager.transaction() as conn:
            conn.execute(
                "UPDATE members SET current_fines = ? WHERE id = ?",
                (new_balance, member["id"])
            )
            # If paid completely, mark overdue transactions as paid
            if new_balance == 0:
                conn.execute(
                    "UPDATE circulation_transactions SET fine_paid = 1 WHERE member_id = ? AND fine_paid = 0",
                    (member["id"],)
                )

        AuditService.log(
            action="PAY_FINE",
            entity="MEMBER",
            entity_id=member_id,
            user_id=operator_id,
            details={"paid_amount": amount, "previous_balance": current_balance, "new_balance": new_balance, "method": payment_method}
        )

        return {
            "success": True,
            "member_id": member_id,
            "paid_amount": amount,
            "previous_balance": current_balance,
            "remaining_balance": new_balance,
            "message": f"Payment of ${amount:.2f} received. New balance: ${new_balance:.2f}"
        }
