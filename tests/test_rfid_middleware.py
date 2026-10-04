"""
Test suite for RFID Middleware, Staff Station, and Handheld Inventory.
Verifies FR 03, FR 05, FR 06, AC 02, AC 05.
"""
from src.middleware.staff_station import StaffStationService
from src.middleware.handheld_reader import HandheldReaderService
from src.middleware.rfid_manager import rfid_manager

def test_tag_association_and_query():
    """
    Tests priority acceptance scenario AC 02:
    Create or locate bib item, validate it, associate mock RFID tag,
    and display tag-to-item relationship.
    """
    # 1. Validate Item ACC-005001 before tagging (FR 05)
    val = StaffStationService.validate_item_for_tagging("ACC-005001")
    assert val["valid"] is True
    assert val["title"] == "Database System Concepts"
    assert val["is_already_tagged"] is False

    # 2. Associate Mock RFID Tag
    tag_uid = "E00401509988A501"
    tag_res = StaffStationService.tag_item("ACC-005001", tag_uid)
    assert tag_res["success"] is True
    assert tag_res["tag_uid"] == tag_uid
    assert tag_res["eas_status"] == 0 # Armed

    # 3. Query tag-to-item relationship
    info = StaffStationService.get_tag_info(tag_uid)
    assert info is not None
    assert info["accession_number"] == "ACC-005001"
    assert info["title"] == "Database System Concepts"
    assert info["eas_status"] == 0

def test_handheld_inventory_misplaced_and_missing():
    """
    Tests priority acceptance scenario AC 05:
    Use handheld reader mock to inventory a shelf and report missing and
    misplaced items with visible and audible confirmation events.
    """
    # Start audit on Shelf-A-01
    audit_id = HandheldReaderService.start_inventory_audit(
        audit_name="CS Shelf-A-01 Audit",
        shelf_target="Shelf-A-01"
    )
    assert audit_id > 0

    # Simulate scan burst containing:
    # 1. E00401509988A101 (Introduction to Algorithms - CORRECT on Shelf-A-01)
    # 2. E00401509988A301 (Artificial Intelligence - MISPLACED! Belongs on Shelf-A-02)
    burst_tags = ["E00401509988A101", "E00401509988A301"]
    burst_res = HandheldReaderService.process_scan_burst(
        audit_id=audit_id,
        scanned_tag_uids=burst_tags,
        current_shelf="Shelf-A-01"
    )

    assert burst_res["correct_in_burst"] == 1
    assert burst_res["misplaced_in_burst"] == 1

    # Verify audio tone frequencies
    correct_item = next(it for it in burst_res["items"] if it["status"] == "CORRECT")
    assert correct_item["audio_freq"] == 880 # 880Hz single chime

    misplaced_item = next(it for it in burst_res["items"] if it["status"] == "MISPLACED")
    assert misplaced_item["audio_freq"] == 440 # 440Hz double pulse
    assert "Shelf-A-02" in misplaced_item["assigned_shelf"]

    # Finalize audit to identify MISSING items (e.g. ACC-001002 catalogued on Shelf-A-01 but not scanned)
    final_res = HandheldReaderService.finalize_inventory_audit(audit_id)
    assert final_res["status"] == "COMPLETED"
    assert final_res["misplaced_count"] >= 1
    assert final_res["missing_count"] >= 1
    assert any(m["accession_number"] == "ACC-001002" for m in final_res["missing_items"])
