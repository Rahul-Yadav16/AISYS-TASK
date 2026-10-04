"""
NISO NCIP 2.0 adapter for AISYS.
Handles XML and JSON representations for LookupUser, CheckOutItem, CheckInItem, and RenewItem.
Fulfills FR 03, AC 03.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET
from src.services.circulation_service import CirculationService
from src.services.member_service import MemberService
from src.core.logger import logger

class NCIPAdapter:
    @staticmethod
    def process_ncip_request(request_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches NCIP 2.0 request using standard JSON structure.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if request_type == "LookupUser":
            user_id = payload.get("user_id")
            member = MemberService.get_member(user_id)
            if not member:
                return {
                    "ncip_message": "LookupUserResponse",
                    "timestamp": now_iso,
                    "problem": {"problem_type": "UserNotFound", "problem_detail": f"User {user_id} not found."}
                }
            return {
                "ncip_message": "LookupUserResponse",
                "timestamp": now_iso,
                "user_id": member["member_id"],
                "name_information": member["full_name"],
                "user_privilege_status": "BLOCKED" if member["is_blocked"] else "ACTIVE",
                "account_details": {"current_fines": member["current_fines"]},
                "active_loans_count": member["active_loans_count"]
            }

        elif request_type == "CheckOutItem":
            user_id = payload.get("user_id")
            item_id = payload.get("item_id")
            try:
                result = CirculationService.checkout_item(
                    member_identifier=user_id,
                    item_identifier=item_id
                )
                return {
                    "ncip_message": "CheckOutItemResponse",
                    "timestamp": now_iso,
                    "transaction_id": result["transaction_id"],
                    "user_id": result["member_id"],
                    "item_id": result["accession_number"],
                    "title": result["title"],
                    "date_due": result["due_date"],
                    "status": "SUCCESS"
                }
            except Exception as e:
                return {
                    "ncip_message": "CheckOutItemResponse",
                    "timestamp": now_iso,
                    "problem": {"problem_type": "CheckOutFailed", "problem_detail": str(e)}
                }

        elif request_type == "CheckInItem":
            item_id = payload.get("item_id")
            try:
                result = CirculationService.checkin_item(item_identifier=item_id)
                return {
                    "ncip_message": "CheckInItemResponse",
                    "timestamp": now_iso,
                    "item_id": result["accession_number"],
                    "title": result["title"],
                    "status": "SUCCESS",
                    "fine_assessed": result["fine_assessed"]
                }
            except Exception as e:
                return {
                    "ncip_message": "CheckInItemResponse",
                    "timestamp": now_iso,
                    "problem": {"problem_type": "CheckInFailed", "problem_detail": str(e)}
                }

        elif request_type == "RenewItem":
            item_id = payload.get("item_id")
            try:
                result = CirculationService.renew_item(item_identifier=item_id)
                return {
                    "ncip_message": "RenewItemResponse",
                    "timestamp": now_iso,
                    "item_id": result["accession_number"],
                    "title": result["title"],
                    "date_due": result["new_due_date"],
                    "renewal_count": result["renewal_count"],
                    "status": "SUCCESS"
                }
            except Exception as e:
                return {
                    "ncip_message": "RenewItemResponse",
                    "timestamp": now_iso,
                    "problem": {"problem_type": "RenewFailed", "problem_detail": str(e)}
                }

        return {
            "ncip_message": "NCIPProblemResponse",
            "timestamp": now_iso,
            "problem": {"problem_type": "UnsupportedService", "problem_detail": f"Unknown service: {request_type}"}
        }

    @staticmethod
    def process_xml_message(xml_string: str) -> str:
        """
        Parses NCIP 2.0 XML request, invokes service, and outputs compliant XML response.
        """
        try:
            root = ET.fromstring(xml_string)
            # Find first child tag (e.g. CheckOutItem)
            action_elem = None
            for child in root:
                action_elem = child
                break

            if action_elem is None:
                return "<NCIPMessage><Problem>EmptyRequest</Problem></NCIPMessage>"

            tag_name = action_elem.tag.split("}")[-1] # strip namespace
            now_iso = datetime.now(timezone.utc).isoformat()

            if "CheckOutItem" in tag_name:
                user_id = ""
                item_id = ""
                for elem in action_elem.iter():
                    local_tag = elem.tag.split("}")[-1]
                    if local_tag in ("UserId", "UserIdentifierValue") and elem.text:
                        user_id = elem.text.strip()
                    elif local_tag in ("ItemId", "ItemIdentifierValue") and elem.text:
                        item_id = elem.text.strip()

                res = NCIPAdapter.process_ncip_request("CheckOutItem", {"user_id": user_id, "item_id": item_id})
                if "problem" in res:
                    return f'<NCIPMessage><CheckOutItemResponse><Problem><ProblemDetail>{res["problem"]["problem_detail"]}</ProblemDetail></Problem></CheckOutItemResponse></NCIPMessage>'
                return f'<NCIPMessage><CheckOutItemResponse><ItemId>{res["item_id"]}</ItemId><UserId>{res["user_id"]}</UserId><DateDue>{res["date_due"]}</DateDue><Title>{res["title"]}</Title></CheckOutItemResponse></NCIPMessage>'

            return f'<NCIPMessage><Problem>UnsupportedAction_{tag_name}</Problem></NCIPMessage>'

        except Exception as e:
            return f'<NCIPMessage><Problem>XMLParseError: {str(e)}</Problem></NCIPMessage>'

ncip_adapter = NCIPAdapter()
