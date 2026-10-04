"""
Handheld RFID reader inventory service for AISYS.
Supports shelf stock verification, bulk tag reading, missing and misplaced item detection,
and visible/audible confirmation events.
Fulfills FR 06, AC 05.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger
from src.middleware.rfid_manager import rfid_manager, TagReadEvent

class HandheldReaderService:
    @staticmethod
    def start_inventory_audit(audit_name: str, shelf_target: str) -> int:
        """
        Initializes an inventory audit session on a target shelf.
        """
        # Count catalogued items on this shelf
        expected_items = db_manager.execute_query(
            "SELECT id, accession_number FROM items WHERE shelf_location LIKE ?",
            (f"%{shelf_target}%",)
        )
        total_expected = len(expected_items)

        audit_id = db_manager.execute_mutation("""
            INSERT INTO inventory_audits (audit_name, shelf_target, total_expected, total_scanned, status)
            VALUES (?, ?, ?, 0, 'IN_PROGRESS')
        """, (audit_name, shelf_target, total_expected))

        logger.info(f"Inventory audit #{audit_id} started for shelf: {shelf_target} ({total_expected} expected items)")
        return audit_id

    @staticmethod
    def process_scan_burst(
        audit_id: int,
        scanned_tag_uids: List[str],
        current_shelf: str
    ) -> Dict[str, Any]:
        """
        Processes a burst of RFID tags captured by the handheld wand.
        Computes item status (CORRECT, MISPLACED, UNKNOWN) and produces
        audible frequency cues and visual event data.
        Fulfills FR 06, AC 05.
        """
        results: List[Dict[str, Any]] = []
        correct_count = 0
        misplaced_count = 0
        unknown_count = 0

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        for tag_uid in scanned_tag_uids:
            # Query tag mapping
            tag_info = db_manager.execute_one("""
                SELECT r.tag_uid, r.eas_status, i.id as item_id, i.accession_number,
                       i.shelf_location, b.title, b.author, b.call_number
                FROM rfid_tags r
                JOIN items i ON r.item_id = i.id
                JOIN bibliographic_records b ON i.biblio_id = b.id
                WHERE r.tag_uid = ?
            """, (tag_uid,))

            if not tag_info:
                # Uncatalogued / Unknown Tag
                unknown_count += 1
                item_event = {
                    "tag_uid": tag_uid,
                    "status": "UNKNOWN",
                    "title": "Unregistered / Unknown Tag",
                    "accession_number": "N/A",
                    "assigned_shelf": "Unknown",
                    "scanned_shelf": current_shelf,
                    "audio_tone": "LOW_BUZZ", # 220Hz
                    "audio_freq": 220,
                    "visual_color": "RED",
                    "message": f"Tag {tag_uid} is not recognized in the library catalog."
                }
            elif current_shelf in tag_info["shelf_location"]:
                # Correct Shelf Placement
                correct_count += 1
                item_event = {
                    "tag_uid": tag_uid,
                    "status": "CORRECT",
                    "title": tag_info["title"],
                    "accession_number": tag_info["accession_number"],
                    "assigned_shelf": tag_info["shelf_location"],
                    "scanned_shelf": current_shelf,
                    "audio_tone": "HIGH_BEEP", # 880Hz single confirmation beep
                    "audio_freq": 880,
                    "visual_color": "GREEN",
                    "message": f"Correct: '{tag_info['title']}' belongs on this shelf."
                }
            else:
                # Misplaced Item!
                misplaced_count += 1
                item_event = {
                    "tag_uid": tag_uid,
                    "status": "MISPLACED",
                    "title": tag_info["title"],
                    "accession_number": tag_info["accession_number"],
                    "assigned_shelf": tag_info["shelf_location"],
                    "scanned_shelf": current_shelf,
                    "audio_tone": "DOUBLE_PULSE_WARNING", # 440Hz double pulse
                    "audio_freq": 440,
                    "visual_color": "AMBER",
                    "message": f"MISPLACED: '{tag_info['title']}' belongs on {tag_info['shelf_location']}, not {current_shelf}!"
                }

            # Record in inventory_items
            db_manager.execute_mutation("""
                INSERT INTO inventory_items (audit_id, tag_uid, accession_number, shelf_detected, status, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                tag_uid,
                tag_info["accession_number"] if tag_info else None,
                current_shelf,
                item_event["status"],
                now_str
            ))

            results.append(item_event)

        # Update audit counts
        db_manager.execute_mutation("""
            UPDATE inventory_audits
            SET total_scanned = total_scanned + ?,
                correct_count = correct_count + ?,
                misplaced_count = misplaced_count + ?
            WHERE id = ?
        """, (len(scanned_tag_uids), correct_count, misplaced_count, audit_id))

        return {
            "audit_id": audit_id,
            "processed_in_burst": len(scanned_tag_uids),
            "correct_in_burst": correct_count,
            "misplaced_in_burst": misplaced_count,
            "unknown_in_burst": unknown_count,
            "items": results
        }

    @staticmethod
    def finalize_inventory_audit(audit_id: int) -> Dict[str, Any]:
        """
        Completes the audit session, detects missing items, and produces reconciliation.
        Fulfills AC 05.
        """
        audit = db_manager.execute_one("SELECT * FROM inventory_audits WHERE id = ?", (audit_id,))
        if not audit:
            raise ValueError(f"Audit #{audit_id} not found.")

        # Find items catalogued on this shelf that were NEVER scanned in this audit
        missing_items = db_manager.execute_query("""
            SELECT i.id, i.accession_number, i.barcode, i.shelf_location,
                   b.title, b.author, b.call_number, r.tag_uid
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.shelf_location LIKE ?
              AND i.id NOT IN (
                  SELECT ii.accession_number FROM inventory_items ii WHERE ii.audit_id = ?
              )
              AND (r.tag_uid IS NULL OR r.tag_uid NOT IN (
                  SELECT ii.tag_uid FROM inventory_items ii WHERE ii.audit_id = ?
              ))
        """, (f"%{audit['shelf_target']}%", audit_id, audit_id))

        missing_count = len(missing_items)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        db_manager.execute_mutation("""
            UPDATE inventory_audits
            SET status = 'COMPLETED', completed_at = ?, missing_count = ?
            WHERE id = ?
        """, (now_str, missing_count, audit_id))

        # Retrieve all scanned misplaced items
        misplaced_items = db_manager.execute_query("""
            SELECT ii.*, b.title, b.author, i.shelf_location as assigned_shelf
            FROM inventory_items ii
            LEFT JOIN items i ON ii.accession_number = i.accession_number
            LEFT JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE ii.audit_id = ? AND ii.status = 'MISPLACED'
        """, (audit_id,))

        return {
            "audit_id": audit_id,
            "audit_name": audit["audit_name"],
            "shelf_target": audit["shelf_target"],
            "total_expected": audit["total_expected"],
            "total_scanned": audit["total_scanned"],
            "correct_count": audit["correct_count"],
            "misplaced_count": audit["misplaced_count"],
            "missing_count": missing_count,
            "misplaced_items": misplaced_items,
            "missing_items": missing_items,
            "status": "COMPLETED"
        }
