"""
Pytest configuration and shared fixtures for AISYS automated test suite.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from fastapi.testclient import TestClient

from src.core.config import reload_config, get_config
from src.core.database import db_manager
from data.seeds.seed_data import seed_database
from src.app import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Create isolated temp database for testing
    temp_dir = tempfile.mkdtemp(prefix="aisys_test_")
    test_db = Path(temp_dir) / "test_aisys.db"

    # Configure environment
    os.environ["AISYS_CONFIG_PATH"] = ""
    cfg = get_config()
    cfg.database.db_path = str(test_db)
    cfg.system.environment = "testing"

    # Apply migrations and seed data
    db_manager._cfg_path = str(test_db)
    db_manager.apply_migrations()
    seed_database()

    yield

    # Teardown
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
