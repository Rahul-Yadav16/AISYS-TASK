"""
Audit trail logging service for AISYS.
Records immutable audit entries for administrative, circulation, migration, and security events.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.core.database import db_manager
from src.core.logger import logger

class AuditService:
    @staticmethod
    def log(
        action: str,
        entity: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "127.0.0.1"
    ) -> int:
        details_str = json.dumps(details) if details else None
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        try:
            log_id = db_manager.execute_mutation(
                """
                INSERT INTO audit_logs (user_id, action, entity, entity_id, details, ip_address, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, action, entity, entity_id, details_str, ip_address, timestamp)
            )
            return log_id
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            return -1

    @staticmethod
    def get_logs(limit: int = 100, offset: int = 0) -> list[dict]:
        return db_manager.execute_query(
            """
            SELECT a.*, u.username, u.full_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
