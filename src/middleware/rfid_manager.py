"""
Device-neutral RFID Middleware and Event Dispatcher for AISYS.
Manages connections and event routing for staff stations, handheld readers,
security gates, and smart card transponders.
Fulfills FR 03.
"""
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
from src.core.logger import logger

class TagReadEvent(BaseModel):
    reader_id: str
    reader_type: str # STAFF_STATION, HANDHELD, SECURITY_GATE, SMART_CARD
    tag_uid: str
    eas_status: int # 0 = Armed, 1 = Disarmed
    timestamp: str
    rssi: float = -50.0
    antenna_port: int = 1

class RFIDDeviceStatus(BaseModel):
    device_id: str
    device_type: str
    is_online: bool
    ip_or_port: str
    last_heartbeat: str
    firmware_version: str = "v3.4.1-AISYS"

class RFIDManager:
    def __init__(self):
        self._devices: Dict[str, RFIDDeviceStatus] = {
            "STAFF-READER-01": RFIDDeviceStatus(
                device_id="STAFF-READER-01",
                device_type="STAFF_STATION",
                is_online=True,
                ip_or_port="COM3 (USB-HID)",
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            ),
            "GATE-01": RFIDDeviceStatus(
                device_id="GATE-01",
                device_type="SECURITY_GATE",
                is_online=True,
                ip_or_port="192.168.10.50:5084",
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            ),
            "HH-WAND-01": RFIDDeviceStatus(
                device_id="HH-WAND-01",
                device_type="HANDHELD",
                is_online=True,
                ip_or_port="192.168.10.60:8080",
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            ),
            "SMART-CARD-01": RFIDDeviceStatus(
                device_id="SMART-CARD-01",
                device_type="SMART_CARD",
                is_online=True,
                ip_or_port="PC/SC USB Reader 0",
                last_heartbeat=datetime.now(timezone.utc).isoformat()
            )
        }
        self._listeners: List[Callable[[TagReadEvent], None]] = []

    def get_devices(self) -> List[Dict[str, Any]]:
        return [d.model_dump() for d in self._devices.values()]

    def update_heartbeat(self, device_id: str):
        if device_id in self._devices:
            self._devices[device_id].last_heartbeat = datetime.now(timezone.utc).isoformat()
            self._devices[device_id].is_online = True

    def register_listener(self, callback: Callable[[TagReadEvent], None]):
        self._listeners.append(callback)

    def dispatch_event(self, event: TagReadEvent):
        self.update_heartbeat(event.reader_id)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in RFID event listener: {e}")

rfid_manager = RFIDManager()
