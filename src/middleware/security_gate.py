"""
Security Gate RFID service for AISYS.
Handles unauthorized exit detection, offline EAS security bit inspection,
alarm dispatch, accession logging, CCTV photo capture, and security alert emails.
Fulfills FR 07, AC 06.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger
from src.middleware.rfid_manager import rfid_manager, TagReadEvent
from src.adapters.camera_adapter import camera_adapter
from src.adapters.notification_adapter import notification_adapter

class SecurityGateService:
    @staticmethod
    def process_passage_event(
        gate_id: str = "GATE-01",
        detected_tag_uid: Optional[str] = None,
        raw_eas_bit: Optional[int] = None, # 0 = Armed (unissued), 1 = Disarmed (issued)
        is_offline_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a passage event at the security gate.
        If an unissued item is detected (raw_eas_bit == 0 or EAS is armed in DB),
        the gate sounds the alarm, logs accession number, invokes CCTV snapshot,
        and queues an email alert.
        Fulfills FR 07, AC 06.
        """
        now_dt = datetime.now(timezone.utc)
        timestamp_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Normal pedestrian passage (no tag detected)
        if not detected_tag_uid:
            event_id = db_manager.execute_mutation("""
                INSERT INTO gate_security_events (gate_id, event_type, alarm_sounded, notification_sent, timestamp)
                VALUES (?, 'PASS', 0, 0, ?)
            """, (gate_id, timestamp_str))
            return {
                "event_id": event_id,
                "event_type": "PASS",
                "alarm": False,
                "message": "Authorized pedestrian transit."
            }

        # 2. Tag detected: inspect EAS security bit
        # Offline capability (FR 07, AC 06): Gate reads raw EAS bit directly from tag antenna
        item_title = "Unknown Item"
        accession_number = None

        tag_record = db_manager.execute_one("""
            SELECT r.*, i.accession_number, b.title, i.status as item_status
            FROM rfid_tags r
            JOIN items i ON r.item_id = i.id
            JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE r.tag_uid = ?
        """, (detected_tag_uid,))

        if tag_record:
            item_title = tag_record["title"]
            accession_number = tag_record["accession_number"]
            # If raw_eas_bit is provided by the gate hardware, use it; otherwise use record's EAS
            effective_eas = raw_eas_bit if raw_eas_bit is not None else tag_record["eas_status"]
        else:
            # Tag unknown to DB, but has raw EAS bit = 0
            effective_eas = raw_eas_bit if raw_eas_bit is not None else 0

        # EAS == 0 means Armed / Protected / Not checked out -> ALARM!
        if effective_eas == 0:
            logger.warning(f"SECURITY BREACH AT {gate_id}! Unauthorized item detected: Tag {detected_tag_uid} ({accession_number or 'UNKNOWN'})")

            # Capture Mock CCTV Snapshot (AC 06)
            cctv_filename = camera_adapter.capture_snapshot(
                gate_id=gate_id,
                accession_number=accession_number,
                tag_uid=detected_tag_uid
            )

            # Queue Email Alert to Security Staff (AC 06)
            email_body = (
                f"URGENT SECURITY ALERT: Unauthorized item removal detected at {gate_id}.\n"
                f"Timestamp: {timestamp_str}\n"
                f"Accession Number: {accession_number or 'Uncatalogued'}\n"
                f"Title: {item_title}\n"
                f"Tag UID: {detected_tag_uid}\n"
                f"CCTV Evidence: storage/cctv_captures/{cctv_filename}\n"
                f"Please intercept patron at exit perimeter."
            )
            notification_adapter.send_email(
                recipient="security-desk@aisys.local",
                subject=f"SECURITY ALERT - Gate Breach at {gate_id} - {accession_number or detected_tag_uid}",
                body=email_body,
                attachment_path=f"storage/cctv_captures/{cctv_filename}"
            )

            # Record gate security event in database
            event_id = db_manager.execute_mutation("""
                INSERT INTO gate_security_events (
                    gate_id, event_type, tag_uid, accession_number,
                    item_title, cctv_image_path, alarm_sounded, notification_sent, timestamp
                ) VALUES (?, 'ALARM', ?, ?, ?, ?, 1, 1, ?)
            """, (gate_id, detected_tag_uid, accession_number, item_title, f"storage/cctv_captures/{cctv_filename}", timestamp_str))

            AuditService.log(
                action="GATE_SECURITY_ALARM",
                entity="SECURITY_GATE",
                entity_id=gate_id,
                details={
                    "tag_uid": detected_tag_uid,
                    "accession_number": accession_number,
                    "cctv_file": cctv_filename,
                    "eas_bit": effective_eas
                }
            )

            return {
                "event_id": event_id,
                "event_type": "ALARM",
                "alarm": True,
                "alarm_frequency_hz": 220,
                "audio_tone": "PERSISTENT_SIREN",
                "gate_id": gate_id,
                "tag_uid": detected_tag_uid,
                "accession_number": accession_number,
                "item_title": item_title,
                "cctv_image_path": f"/api/gate/cctv/{cctv_filename}",
                "cctv_filename": cctv_filename,
                "email_notification_queued": True,
                "message": f"ALARM TRIGGERED! Unissued item detected: {item_title} ({accession_number})"
            }
        else:
            # EAS == 1: Properly Checked Out Item!
            event_id = db_manager.execute_mutation("""
                INSERT INTO gate_security_events (
                    gate_id, event_type, tag_uid, accession_number,
                    item_title, alarm_sounded, notification_sent, timestamp
                ) VALUES (?, 'PASS', ?, ?, ?, 0, 0, ?)
            """, (gate_id, detected_tag_uid, accession_number, item_title, timestamp_str))

            return {
                "event_id": event_id,
                "event_type": "PASS",
                "alarm": False,
                "gate_id": gate_id,
                "tag_uid": detected_tag_uid,
                "accession_number": accession_number,
                "item_title": item_title,
                "message": f"Authorized pass: '{item_title}' is checked out."
            }

    @staticmethod
    def record_footfall(gate_id: str = "GATE-01", count: int = 1) -> int:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(count):
            db_manager.execute_mutation("""
                INSERT INTO gate_security_events (gate_id, event_type, alarm_sounded, notification_sent, timestamp)
                VALUES (?, 'FOOTFALL', 0, 0, ?)
            """, (gate_id, now_str))
        return count
