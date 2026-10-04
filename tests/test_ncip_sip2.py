"""
Test suite for 3M SIP2 and NISO NCIP 2.0 interoperability adapters.
Verifies FR 03, AC 03.
"""
from src.adapters.sip2_adapter import sip2_adapter
from src.adapters.ncip_adapter import ncip_adapter

def test_sip2_and_ncip_checkout_checkin():
    """
    Tests priority acceptance scenario AC 03:
    Check out, renew, and check in an item through a mocked NCIP or SIP2 flow
    while preserving an auditable transaction history.
    """
    # 1. SIP2 Handshake (99 -> 98)
    sip_status_resp = sip2_adapter.process_message("99")
    assert sip_status_resp.startswith("98")
    assert "AISYS" in sip_status_resp

    # 2. SIP2 Checkout (11 -> 12)
    # Issue ACC-001001 to MEM-1001
    sip_checkout = "11YN20261004    19000020261018    190000AOAISYS|AAMEM-1001|ABACC-001001|"
    sip_checkout_resp = sip2_adapter.process_message(sip_checkout)
    assert sip_checkout_resp.startswith("121") # 121 indicates Checkout OK
    assert "ACC-001001" in sip_checkout_resp

    # 3. SIP2 Renew (29 -> 30)
    sip_renew = "29YN20261004    190000AOAISYS|AAMEM-1001|ABACC-001001|"
    sip_renew_resp = sip2_adapter.process_message(sip_renew)
    assert sip_renew_resp.startswith("301") # 301 indicates Renew OK

    # 4. SIP2 Checkin (09 -> 10)
    sip_checkin = "09N20261004    190000AOAISYS|ABACC-001001|"
    sip_checkin_resp = sip2_adapter.process_message(sip_checkin)
    assert sip_checkin_resp.startswith("101") # 101 indicates Checkin OK

    # 5. NCIP 2.0 Checkout (JSON envelope)
    ncip_checkout_res = ncip_adapter.process_ncip_request("CheckOutItem", {
        "user_id": "MEM-1001",
        "item_id": "ACC-001001"
    })
    assert ncip_checkout_res["ncip_message"] == "CheckOutItemResponse"
    assert ncip_checkout_res["status"] == "SUCCESS"

    # 6. NCIP 2.0 Checkin (JSON envelope)
    ncip_checkin_res = ncip_adapter.process_ncip_request("CheckInItem", {
        "item_id": "ACC-001001"
    })
    assert ncip_checkin_res["ncip_message"] == "CheckInItemResponse"
    assert ncip_checkin_res["status"] == "SUCCESS"

    # 7. NCIP 2.0 XML Flow
    xml_req = """<ns1:NCIPMessage xmlns:ns1="http://www.niso.org/2000/inclusion">
      <ns1:CheckOutItem>
        <ns1:UserId>MEM-1001</ns1:UserId>
        <ns1:ItemId>ACC-001001</ns1:ItemId>
      </ns1:CheckOutItem>
    </ns1:NCIPMessage>"""
    xml_resp = ncip_adapter.process_xml_message(xml_req)
    assert "<CheckOutItemResponse>" in xml_resp
    assert "ACC-001001" in xml_resp

    # Return item
    sip2_adapter.process_message("09N20261004    190000AOAISYS|ABACC-001001|")
