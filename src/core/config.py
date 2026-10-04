"""
Configuration manager for AISYS Library & RFID Solution.
Loads configuration from JSON files or environment variables with strict validation.
"""
import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class SystemConfig(BaseModel):
    institution_name: str = "AISYS Central Academic Library"
    institution_code: str = "AISYS-LIB-01"
    environment: str = "development"
    secret_key: str = "AISYS_SECURE_DEV_SECRET_KEY_CHANGE_IN_PRODUCTION"
    token_ttl_hours: int = 8

class DatabaseConfig(BaseModel):
    db_path: str = "data/aisys_library.db"
    wal_mode: bool = True
    busy_timeout_ms: int = 5000

class CirculationPolicyConfig(BaseModel):
    loan_period_days: int = 14
    max_renewals: int = 2
    max_fine_limit: float = 10.00
    daily_fine_rate: float = 0.50
    enforce_reference_restriction: bool = True
    enforce_member_blocking: bool = True

class RFIDMiddlewareConfig(BaseModel):
    mock_mode: bool = True
    staff_station_id: str = "STAFF-READER-01"
    gate_id: str = "GATE-01"
    handheld_id: str = "HH-WAND-01"
    offline_gate_security_bit_check: bool = True
    sound_effects_enabled: bool = True

class InteroperabilityConfig(BaseModel):
    sip2_enabled: bool = True
    sip2_port: int = 6001
    ncip_version: str = "2.0"

class NotificationsConfig(BaseModel):
    email_adapter: str = "mock"
    sms_adapter: str = "mock"
    print_adapter: str = "mock"

class AppConfig(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    circulation_policy: CirculationPolicyConfig = Field(default_factory=CirculationPolicyConfig)
    rfid_middleware: RFIDMiddlewareConfig = Field(default_factory=RFIDMiddlewareConfig)
    interoperability: InteroperabilityConfig = Field(default_factory=InteroperabilityConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)

_active_config: Optional[AppConfig] = None

def get_config(config_file: Optional[str] = None) -> AppConfig:
    global _active_config
    if _active_config is not None and config_file is None:
        return _active_config

    path = config_file or os.environ.get("AISYS_CONFIG_PATH")
    if not path:
        default_candidate = BASE_DIR / "config" / "sample_config.json"
        if default_candidate.exists():
            path = str(default_candidate)

    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            _active_config = AppConfig(**raw_data)
    else:
        _active_config = AppConfig()

    return _active_config

def reload_config(config_file: Optional[str] = None) -> AppConfig:
    global _active_config
    _active_config = None
    return get_config(config_file)
