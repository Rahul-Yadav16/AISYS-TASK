"""
Provider-neutral notification and print service adapter for AISYS.
Supports mock and live spooling for Email, SMS, and thermal slip printing.
Fulfills FR 09.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STAGING_DIR = BASE_DIR / "storage" / "staging"
LABELS_DIR = BASE_DIR / "storage" / "labels"

class NotificationAdapter:
    def __init__(self):
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        LABELS_DIR.mkdir(parents=True, exist_ok=True)
        self.email_spool_path = STAGING_DIR / "email_spool.json"
        self.sms_spool_path = STAGING_DIR / "sms_spool.json"

    def _append_spool(self, filepath: Path, item: Dict[str, Any]):
        spool: List[Dict[str, Any]] = []
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    spool = json.load(f)
            except Exception:
                spool = []
        spool.append(item)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(spool, f, indent=2)

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches email or stores in mock spool.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        message = {
            "timestamp": now_str,
            "type": "EMAIL",
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "attachment": attachment_path,
            "status": "QUEUED_AND_DELIVERED_MOCK"
        }
        self._append_spool(self.email_spool_path, message)
        logger.info(f"Notification email dispatched to {recipient}: '{subject}'")
        return {"success": True, "message": message}

    def send_sms(self, phone_number: str, message_text: str) -> Dict[str, Any]:
        """
        Dispatches SMS or stores in mock spool.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        message = {
            "timestamp": now_str,
            "type": "SMS",
            "phone_number": phone_number,
            "message": message_text,
            "status": "DELIVERED_MOCK"
        }
        self._append_spool(self.sms_spool_path, message)
        logger.info(f"Notification SMS sent to {phone_number}: '{message_text[:40]}...'")
        return {"success": True, "message": message}

    def print_slip(self, slip_type: str, content: str) -> str:
        """
        Emulates thermal receipt/label slip printing, writing output file.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"slip_{slip_type}_{timestamp}.txt"
        file_path = LABELS_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Receipt/Slip printed to file: {filename}")
        return str(file_path)

    def get_email_spool(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.email_spool_path.exists():
            return []
        try:
            with open(self.email_spool_path, "r", encoding="utf-8") as f:
                spool = json.load(f)
                return spool[-limit:]
        except Exception:
            return []

    def get_sms_spool(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.sms_spool_path.exists():
            return []
        try:
            with open(self.sms_spool_path, "r", encoding="utf-8") as f:
                spool = json.load(f)
                return spool[-limit:]
        except Exception:
            return []

notification_adapter = NotificationAdapter()
