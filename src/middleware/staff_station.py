"""
RFID Staff Station Service for AISYS.
Handles validation of bibliographic/item records, RFID tag programming,
tag-to-item mapping, and EAS arming/disarming.
Fulfills FR 05, AC 02.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger
from src.middleware.rfid_manager import rfid_manager, TagReadEvent

class StaffStationService:
    @staticmethod
    def validate_item_for_tagging(item_identifier: str) -> Dict[str, Any]:
        """
        Validates an item before tagging or re-tagging. Fulfills FR 05.
        """
        item = db_manager.execute_one("""
            SELECT i.*, b.title, b.author, b.isbn, b.call_number, b.material_type, b.is_reference,
                   r.tag_uid, r.eas_status, r.last_scanned_at
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.accession_number = ? OR i.barcode = ?
        """, (item_identifier, item_identifier))

        if not item:
            raise ValueError(f"Item '{item_identifier}' not found in library catalog.")

        is_already_tagged = bool(item["tag_uid"])
        return {
            "valid": True,
            "item_id": item["id"],
            "accession_number": item["accession_number"],
            "barcode": item["barcode"],
            "title": item["title"],
            "author": item["author"],
            "call_number": item["call_number"],
            "material_type": item["material_type"],
            "is_reference": bool(item["is_reference"]),
            "is_already_tagged": is_already_tagged,
            "existing_tag_uid": item["tag_uid"],
            "eas_status": item["eas_status"]
        }

    @staticmethod
    def tag_item(
        item_identifier: str,
        tag_uid: str,
        operator_id: Optional[int] = None,
        force_retag: bool = False
    ) -> Dict[str, Any]:
        """
        Associates an RFID tag UID with an item record, initializes EAS status to 0 (Armed),
        and records audit trail. Fulfills FR 05, AC 02.
        """
        val = StaffStationService.validate_item_for_tagging(item_identifier)
        item_id = val["item_id"]

        # Check if tag is already used on another item
        tag_in_use = db_manager.execute_one(
            "SELECT item_id FROM rfid_tags WHERE tag_uid = ? AND item_id != ?",
            (tag_uid, item_id)
        )
        if tag_in_use:
            raise ValueError(f"RFID Tag UID '{tag_uid}' is already associated with another item (ID {tag_in_use['item_id']}).")

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with db_manager.transaction() as conn:
            # Upsert into rfid_tags
            conn.execute("""
                INSERT INTO rfid_tags (item_id, tag_uid, eas_status, memory_format, last_scanned_at, last_reader_id)
                VALUES (?, ?, 0, 'ISO15693_DATA_MODEL', ?, 'STAFF-READER-01')
                ON CONFLICT(item_id) DO UPDATE SET
                    tag_uid = excluded.tag_uid,
                    eas_status = 0,
                    last_scanned_at = excluded.last_scanned_at,
                    last_reader_id = 'STAFF-READER-01';
            """, (item_id, tag_uid, now_str))

            # Mark item as tagged
            conn.execute("UPDATE items SET is_tagged = 1 WHERE id = ?", (item_id,))

        AuditService.log(
            action="TAG_ITEM",
            entity="RFID_TAG",
            entity_id=tag_uid,
            user_id=operator_id,
            details={"accession_number": val["accession_number"], "title": val["title"], "item_id": item_id}
        )

        # Dispatch event to RFID manager
        rfid_manager.dispatch_event(TagReadEvent(
            reader_id="STAFF-READER-01",
            reader_type="STAFF_STATION",
            tag_uid=tag_uid,
            eas_status=0,
            timestamp=now_str
        ))

        return {
            "success": True,
            "item_id": item_id,
            "accession_number": val["accession_number"],
            "title": val["title"],
            "tag_uid": tag_uid,
            "eas_status": 0, # Armed
            "memory_format": "ISO15693_DATA_MODEL",
            "message": f"RFID Tag '{tag_uid}' successfully linked to '{val['title']}'. EAS armed."
        }

    @staticmethod
    def get_tag_info(tag_uid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves tag status and associated bibliographic information.
        Fulfills AC 02 ("display the tag-to-item relationship").
        """
        sql = """
            SELECT r.*, i.accession_number, i.barcode, i.status as item_status, i.shelf_location,
                   b.title, b.author, b.call_number, b.material_type, b.is_reference
            FROM rfid_tags r
            JOIN items i ON r.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE r.tag_uid = ?
        """
        return db_manager.execute_one(sql, (tag_uid,))

    @staticmethod
    def arm_eas(tag_uid: str) -> bool:
        db_manager.execute_mutation(
            "UPDATE rfid_tags SET eas_status = 0, last_scanned_at = (strftime('%Y-%m-%d %H:%M:%S', 'now')) WHERE tag_uid = ?",
            (tag_uid,)
        )
        return True

    @staticmethod
    def disarm_eas(tag_uid: str) -> bool:
        db_manager.execute_mutation(
            "UPDATE rfid_tags SET eas_status = 1, last_scanned_at = (strftime('%Y-%m-%d %H:%M:%S', 'now')) WHERE tag_uid = ?",
            (tag_uid,)
        )
        return True
