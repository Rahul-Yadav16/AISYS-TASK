"""
Test suite for Circulation policies, restrictions, and fines.
Verifies FR 04, AC 03, AC 04.
"""
import pytest
from src.services.circulation_service import CirculationService
from src.services.fines_service import FinesService
from src.middleware.staff_station import StaffStationService

def test_circulation_normal_lifecycle():
    # Issue item ACC-001001 to student MEM-1001
    checkout_res = CirculationService.checkout_item("MEM-1001", "ACC-001001")
    assert checkout_res["success"] is True
    assert checkout_res["eas_status"] == 1 # Disarmed

    # Verify Tag EAS status is updated to 1
    tag_info = StaffStationService.get_tag_info("E00401509988A101")
    assert tag_info["eas_status"] == 1

    # Renew item
    renew_res = CirculationService.renew_item("ACC-001001")
    assert renew_res["success"] is True
    assert renew_res["renewal_count"] == 1

    # Return item
    return_res = CirculationService.checkin_item("ACC-001001")
    assert return_res["success"] is True
    assert return_res["status"] == "AVAILABLE"
    assert return_res["eas_status"] == 0 # Rearmed to 0

    # Verify Tag EAS status is rearmed to 0
    tag_info = StaffStationService.get_tag_info("E00401509988A101")
    assert tag_info["eas_status"] == 0

def test_circulation_restrictions():
    """
    Tests priority acceptance scenario AC 04:
    Block circulation for:
    1. Reference item
    2. Blocked member
    3. Member whose fine exceeds configurable limit ($10.00)
    """
    # 1. Reference Book Restriction (ACC-002001 is Reference Only)
    with pytest.raises(PermissionError) as exc_ref:
        CirculationService.checkout_item("MEM-1001", "ACC-002001")
    assert "REFERENCE MATERIAL" in str(exc_ref.value)

    # 2. Blocked Member Restriction (MEM-1003 has is_blocked = 1)
    with pytest.raises(PermissionError) as exc_block:
        CirculationService.checkout_item("MEM-1003", "ACC-001002")
    assert "blocked" in str(exc_block.value).lower()

    # 3. Fine Limit Restriction (MEM-1004 has fines = $15.50 > $10.00 limit)
    with pytest.raises(PermissionError) as exc_fine:
        CirculationService.checkout_item("MEM-1004", "ACC-001002")
    assert "fine" in str(exc_fine.value).lower()

def test_fine_payment_and_clearance():
    # MEM-1004 pays part of fine ($10.00 of $15.50)
    pay_res = FinesService.pay_fine("MEM-1004", 10.00)
    assert pay_res["success"] is True
    assert pay_res["remaining_balance"] == 5.50

    # Remaining balance is now $5.50 (below $10.00 threshold) -> Patron can now check out!
    checkout_res = CirculationService.checkout_item("MEM-1004", "ACC-001002")
    assert checkout_res["success"] is True

    # Clean up by returning
    CirculationService.checkin_item("ACC-001002")
