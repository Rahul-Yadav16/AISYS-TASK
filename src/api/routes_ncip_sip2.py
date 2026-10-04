"""
Interoperability API routes for AISYS.
Exposes standard 3M SIP2 frame processor and NISO NCIP 2.0 XML/JSON endpoints.
Fulfills FR 03, AC 03.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException, Response
from pydantic import BaseModel
from src.adapters.sip2_adapter import sip2_adapter
from src.adapters.ncip_adapter import ncip_adapter

router = APIRouter(prefix="/api/interop", tags=["Interoperability (SIP2 & NCIP 2.0)"])

class SIP2MessageRequest(BaseModel):
    raw_message: str

class NCIPJsonRequest(BaseModel):
    service: str # LookupUser, CheckOutItem, CheckInItem, RenewItem
    payload: Dict[str, Any]

@router.post("/sip2/message")
def process_sip2_message(req: SIP2MessageRequest):
    """
    Processes incoming 3M SIP2 protocol message frame and returns SIP2 response string.
    Fulfills FR 03, AC 03.
    """
    response_frame = sip2_adapter.process_message(req.raw_message)
    return {"request": req.raw_message, "response": response_frame}

@router.post("/ncip/v2")
def process_ncip_json(req: NCIPJsonRequest):
    """
    Processes standard NCIP 2.0 message using JSON envelope.
    Fulfills FR 03, AC 03.
    """
    return ncip_adapter.process_ncip_request(req.service, req.payload)

@router.post("/ncip/v2/xml")
def process_ncip_xml(xml_payload: str = Body(..., media_type="application/xml")):
    """
    Processes raw NCIP 2.0 XML request and returns compliant XML response.
    Fulfills FR 03, AC 03.
    """
    xml_resp = ncip_adapter.process_xml_message(xml_payload)
    return Response(content=xml_resp, media_type="application/xml")
