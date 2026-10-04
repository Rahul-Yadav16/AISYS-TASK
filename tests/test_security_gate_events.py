"""
Test suite for RFID Security Gate events, offline EAS detection, CCTV captures, and alarms.
Verifies FR 07, AC 06.
"""
from pathlib import Path
from src.middleware.security_gate import SecurityGateService
from src.adapters.notification_adapter import notification_adapter
from src.core.database import db_manager

def test_gate_alarm_cctv_and_email_flow():
    """
    Tests priority acceptance scenario AC 06:
    Generate an unauthorised-removal event from the gate mock,
    record the accession number, attach a mock CCTV image, and queue an email notification.
    """
    # E00401509988A101 is currently Armed (EAS = 0 / Unissued)
    # Simulate patron walking through GATE-01 carrying this unissued item
    gate_res = SecurityGateService.process_passage_event(
        gate_id="GATE-01",
        detected_tag_uid="E00401509988A101",
        raw_eas_bit=0 # Armed EAS bit detected offline by gate antenna
    )

    # 1. Verify Alarm Triggered
    assert gate_res["alarm"] is True
    assert gate_res["event_type"] == "ALARM"
    assert gate_res["alarm_frequency_hz"] == 220 # 220Hz persistent buzzer

    # 2. Verify Accession Number Recorded
    assert gate_res["accession_number"] == "ACC-001001"
    assert "Algorithms" in gate_res["item_title"]

    # 3. Verify Mock CCTV Snapshot Generated
    assert gate_res["cctv_filename"] is not None
    cctv_file = Path("storage/cctv_captures") / gate_res["cctv_filename"]
    assert cctv_file.exists()
    assert cctv_file.stat().st_size > 1000 # Valid JPEG image generated

    # 4. Verify Email Notification Queued
    assert gate_res["email_notification_queued"] is True
    email_spool = notification_adapter.get_email_spool()
    assert len(email_spool) >= 1
    last_email = email_spool[-1]
    assert "GATE-01" in last_email["subject"]
    assert "ACC-001001" in last_email["body"]

def test_gate_authorized_transit():
    # Simulate transit with EAS bit = 1 (Issued / Authorized)
    gate_res = SecurityGateService.process_passage_event(
        gate_id="GATE-01",
        detected_tag_uid="E00401509988A101",
        raw_eas_bit=1
    )
    assert gate_res["alarm"] is False
    assert gate_res["event_type"] == "PASS"
