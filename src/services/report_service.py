"""
Reporting and dashboard service for AISYS.
Aggregates library operational statistics, RFID tag metrics, circulation turnover,
operator productivity, and security gate violations.
Fulfills FR 08, AC 08.
"""
from typing import Any, Dict, List, Optional
from src.core.database import db_manager

class ReportService:
    @staticmethod
    def get_dashboard_summary() -> Dict[str, Any]:
        """
        Aggregates top-level KPI metrics for the executive dashboard.
        """
        # Titles and Items
        titles_count = db_manager.execute_one("SELECT COUNT(*) as c FROM bibliographic_records")["c"]
        items_count = db_manager.execute_one("SELECT COUNT(*) as c FROM items")["c"]
        tagged_count = db_manager.execute_one("SELECT COUNT(*) as c FROM rfid_tags")["c"]
        tagging_percentage = round((tagged_count / items_count * 100), 1) if items_count > 0 else 0.0

        # Patrons
        members_count = db_manager.execute_one("SELECT COUNT(*) as c FROM members")["c"]
        blocked_members = db_manager.execute_one("SELECT COUNT(*) as c FROM members WHERE is_blocked = 1")["c"]
        total_fines_due = db_manager.execute_one("SELECT COALESCE(SUM(current_fines), 0) as s FROM members")["s"]

        # Circulation
        active_loans = db_manager.execute_one("SELECT COUNT(*) as c FROM circulation_transactions WHERE status = 'ACTIVE'")["c"]
        total_issues = db_manager.execute_one("SELECT COUNT(*) as c FROM circulation_transactions WHERE transaction_type = 'ISSUE'")["c"]
        total_returns = db_manager.execute_one("SELECT COUNT(*) as c FROM circulation_transactions WHERE status = 'RETURNED'")["c"]

        # Security Gate
        total_gate_events = db_manager.execute_one("SELECT COUNT(*) as c FROM gate_security_events")["c"]
        alarm_events = db_manager.execute_one("SELECT COUNT(*) as c FROM gate_security_events WHERE event_type = 'ALARM'")["c"]
        footfall_count = db_manager.execute_one("SELECT COUNT(*) as c FROM gate_security_events WHERE event_type = 'FOOTFALL' OR event_type = 'PASS'")["c"]

        # Recent Gate Violations
        recent_alarms = db_manager.execute_query("""
            SELECT * FROM gate_security_events
            WHERE event_type = 'ALARM'
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        return {
            "catalog": {
                "total_titles": titles_count,
                "total_items": items_count,
                "tagged_items": tagged_count,
                "untagged_items": items_count - tagged_count,
                "tagging_percentage": tagging_percentage
            },
            "patrons": {
                "total_members": members_count,
                "blocked_members": blocked_members,
                "total_fines_due": round(total_fines_due, 2)
            },
            "circulation": {
                "active_loans": active_loans,
                "total_issues": total_issues,
                "total_returns": total_returns
            },
            "security": {
                "total_events": total_gate_events,
                "alarm_violations": alarm_events,
                "footfall_count": footfall_count,
                "recent_alarms": recent_alarms
            }
        }

    @staticmethod
    def get_tagged_items_report(
        shelf_location: Optional[str] = None,
        eas_status: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []

        if shelf_location:
            conditions.append("i.shelf_location LIKE ?")
            params.append(f"%{shelf_location}%")

        if eas_status is not None:
            conditions.append("r.eas_status = ?")
            params.append(eas_status)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT r.tag_uid, r.eas_status, r.memory_format, r.last_scanned_at,
                   r.last_reader_id, r.battery_or_rssi,
                   i.accession_number, i.barcode, i.status as item_status, i.shelf_location,
                   b.title, b.author, b.call_number, b.material_type
            FROM rfid_tags r
            JOIN items i ON r.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            {where}
            ORDER BY r.last_scanned_at DESC
            LIMIT ? OFFSET ?
        """
        return db_manager.execute_query(sql, tuple(params + [limit, offset]))

    @staticmethod
    def get_circulation_report(
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []

        if transaction_type:
            conditions.append("ct.transaction_type = ?")
            params.append(transaction_type.upper())

        if status:
            conditions.append("ct.status = ?")
            params.append(status.upper())

        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT ct.*, m.member_id, m.full_name as member_name, m.category as member_category,
                   i.accession_number, i.barcode, b.title, b.author,
                   u.username as operator_username
            FROM circulation_transactions ct
            JOIN members m ON ct.member_id = m.id
            JOIN items i ON ct.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN users u ON ct.operator_id = u.id
            {where}
            ORDER BY ct.issue_date DESC
            LIMIT ? OFFSET ?
        """
        return db_manager.execute_query(sql, tuple(params + [limit, offset]))

    @staticmethod
    def get_operator_activity_report() -> List[Dict[str, Any]]:
        sql = """
            SELECT u.id, u.username, u.full_name, u.role,
                   COUNT(ct.id) as total_transactions,
                   SUM(CASE WHEN ct.transaction_type = 'ISSUE' THEN 1 ELSE 0 END) as issue_count,
                   SUM(CASE WHEN ct.transaction_type = 'RETURN' THEN 1 ELSE 0 END) as return_count
            FROM users u
            LEFT JOIN circulation_transactions ct ON u.id = ct.operator_id
            GROUP BY u.id
            ORDER BY total_transactions DESC
        """
        return db_manager.execute_query(sql)

    @staticmethod
    def get_gate_events_report(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        sql = """
            SELECT ge.*
            FROM gate_security_events ge
            ORDER BY ge.timestamp DESC
            LIMIT ? OFFSET ?
        """
        return db_manager.execute_query(sql, (limit, offset))
