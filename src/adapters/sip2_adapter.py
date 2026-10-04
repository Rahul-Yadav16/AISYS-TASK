"""
3M SIP2 protocol message parser and adapter for AISYS.
Handles checkout (11/12), checkin (09/10), renew (29/30), patron info (63/64),
and status handshakes (99/98). Computes checksums per SIP2 specification.
Fulfills FR 03, AC 03.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.core.database import db_manager
from src.services.circulation_service import CirculationService
from src.core.logger import logger

def calculate_sip2_checksum(message_without_checksum: str) -> str:
    """
    Computes SIP2 checksum: negative of the 2's complement of the sum of characters modulo 65536.
    """
    total = sum(ord(c) for c in message_without_checksum)
    checksum = (-total) & 0xFFFF
    return f"{checksum:04X}"

class SIP2Adapter:
    @staticmethod
    def parse_fields(raw_msg: str) -> Dict[str, str]:
        """
        Parses variable delimited fields: e.g. AApatron1|ABitem1|
        """
        fields = {}
        # Skip header command code
        payload = raw_msg[2:]
        parts = payload.split("|")
        for part in parts:
            if len(part) >= 2:
                field_id = part[:2]
                field_val = part[2:]
                fields[field_id] = field_val
        return fields

    @staticmethod
    def process_message(raw_msg: str) -> str:
        """
        Processes an incoming SIP2 message and returns the compliant SIP2 response string.
        """
        msg = raw_msg.strip()
        if len(msg) < 2:
            return "96|AY0AZFFFF"

        cmd = msg[:2]
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d    %H%M%S")

        # 99: SC Status -> 98: ACS Status
        if cmd == "99":
            resp = f"98YNNYYA001002{now_str}2.00AOAISYS-LIBRARY|AMCentral Academic Library|BXYYYYYYYYYYYY"
            chk = calculate_sip2_checksum(resp + "|AZ")
            return f"{resp}|AY1AZ{chk}"

        fields = SIP2Adapter.parse_fields(msg)
        patron_id = fields.get("AA", "").strip()
        item_id = fields.get("AB", "").strip()

        # 63: Patron Information Request -> 64: Patron Info Response
        if cmd == "63":
            member = db_manager.execute_one(
                "SELECT * FROM members WHERE member_id = ? OR smart_card_uid = ?",
                (patron_id, patron_id)
            )
            if member:
                status_char = "Y" if not member["is_blocked"] else " "
                resp = f"64YYYY          001{now_str}0000000000000000AOAISYS|AA{member['member_id']}|AE{member['full_name']}|BV{member['current_fines']:.2f}|BL{status_char}"
            else:
                resp = f"64              001{now_str}0000000000000000AOAISYS|AA{patron_id}|BL "
            chk = calculate_sip2_checksum(resp + "|AZ")
            return f"{resp}|AY1AZ{chk}"

        # 11: Checkout Request -> 12: Checkout Response
        if cmd == "11":
            try:
                res = CirculationService.checkout_item(
                    member_identifier=patron_id,
                    item_identifier=item_id,
                    operator_id=None
                )
                due_dt = res["due_date"].replace("-", "").replace(":", "").replace(" ", "    ")[:18]
                resp = f"121NY{now_str}AOAISYS|AA{patron_id}|AB{item_id}|AJ{res['title']}|AH{due_dt}"
            except Exception as e:
                resp = f"120NN{now_str}AOAISYS|AA{patron_id}|AB{item_id}|AF{str(e)}"
            chk = calculate_sip2_checksum(resp + "|AZ")
            return f"{resp}|AY1AZ{chk}"

        # 09: Checkin Request -> 10: Checkin Response
        if cmd == "09":
            try:
                res = CirculationService.checkin_item(item_identifier=item_id)
                resp = f"101YNN{now_str}AOAISYS|AB{item_id}|AJ{res['title']}|AQ{res['shelf_destination']}"
            except Exception as e:
                resp = f"100NNN{now_str}AOAISYS|AB{item_id}|AF{str(e)}"
            chk = calculate_sip2_checksum(resp + "|AZ")
            return f"{resp}|AY1AZ{chk}"

        # 29: Renew Request -> 30: Renew Response
        if cmd == "29":
            try:
                res = CirculationService.renew_item(item_identifier=item_id)
                new_due = res["new_due_date"].replace("-", "").replace(":", "").replace(" ", "    ")[:18]
                resp = f"301Y{now_str}AOAISYS|AA{patron_id}|AB{item_id}|AJ{res['title']}|AH{new_due}"
            except Exception as e:
                resp = f"300N{now_str}AOAISYS|AA{patron_id}|AB{item_id}|AF{str(e)}"
            chk = calculate_sip2_checksum(resp + "|AZ")
            return f"{resp}|AY1AZ{chk}"

        # Default fallback
        resp = f"96{now_str}AOAISYS|AFUnsupported Command"
        chk = calculate_sip2_checksum(resp + "|AZ")
        return f"{resp}|AY1AZ{chk}"

sip2_adapter = SIP2Adapter()
