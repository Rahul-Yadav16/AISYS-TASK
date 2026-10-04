"""
Mock Camera / CCTV snapshot adapter for AISYS security gates.
Generates realistic timestamped mock JPEG security captures when an alarm event occurs.
Fulfills FR 07, AC 06.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from src.core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CAPTURES_DIR = BASE_DIR / "storage" / "cctv_captures"

class CameraAdapter:
    @staticmethod
    def capture_snapshot(
        gate_id: str = "GATE-01",
        accession_number: Optional[str] = None,
        tag_uid: Optional[str] = None
    ) -> str:
        """
        Synthesizes a security surveillance frame snapshot with an OSD (On-Screen Display)
        timestamp, gate ID, and detection box.
        """
        CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        now_dt = datetime.now(timezone.utc)
        timestamp_str = now_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        file_timestamp = now_dt.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"cctv_{gate_id}_{file_timestamp}.jpg"
        filepath = CAPTURES_DIR / filename

        # Create 640x480 surveillance camera frame
        img = Image.new("RGB", (640, 480), color=(25, 30, 36))
        draw = ImageDraw.Draw(img)

        # Draw simulated security exit corridor lines
        draw.line([(0, 400), (220, 260), (420, 260), (640, 400)], fill=(45, 55, 72), width=2)
        draw.line([(220, 260), (220, 100), (420, 100), (420, 260)], fill=(45, 55, 72), width=2)

        # Gate antenna posts representation
        draw.rectangle([(160, 120), (190, 420)], outline=(220, 38, 38), width=3) # Left gate (Red strobe)
        draw.rectangle([(450, 120), (480, 420)], outline=(220, 38, 38), width=3) # Right gate (Red strobe)

        # Simulated Target Motion / Pedestrian Bounding Box
        draw.rectangle([(270, 150), (370, 380)], outline=(239, 68, 68), width=2)
        draw.text((275, 135), "[UNAUTHORIZED ITEM DETECTED]", fill=(239, 68, 68))

        # On-Screen Display (OSD) Header
        draw.rectangle([(0, 0), (640, 40)], fill=(15, 23, 42))
        draw.text((15, 12), f"CCTV CAM 04 - {gate_id} EGRESS | LIVE REC", fill=(248, 113, 113))
        draw.text((430, 12), timestamp_str, fill=(255, 255, 255))

        # Incident Metadata Footer
        draw.rectangle([(0, 440), (640, 480)], fill=(15, 23, 42))
        acc_text = f"ACCESSION: {accession_number or 'UNKNOWN'}"
        tag_text = f"TAG UID: {tag_uid or 'E00401509988A101'}"
        draw.text((15, 452), f"EAS ALARM: ACTIVE | {acc_text} | {tag_text}", fill=(254, 240, 138))

        img.save(str(filepath), "JPEG", quality=85)
        logger.info(f"CCTV surveillance snapshot captured: {filepath.name}")
        return filename

camera_adapter = CameraAdapter()
