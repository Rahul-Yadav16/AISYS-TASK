"""
Test suite for Security, Smart Card Authentication, RBAC, and Audit Logging.
Verifies FR 11, NFR 02, AC 07.
"""
from fastapi.testclient import TestClient
from src.middleware.smart_card import SmartCardService
from src.core.security import hash_password, verify_password, has_permission
from src.core.audit import AuditService

def test_smart_card_rbac_login():
    """
    Tests priority acceptance scenario AC 07:
    Demonstrate staff smart-card login through a mock credential provider
    and enforce role-based permissions.
    """
    # 1. Staff Admin Tap-Login (SC-ADMIN-001)
    admin_login = SmartCardService.staff_login_by_card("SC-ADMIN-001")
    assert admin_login["success"] is True
    assert admin_login["role"] == "ADMIN"
    assert admin_login["username"] == "admin"
    assert admin_login["token"] is not None

    # Verify Admin has administrative permissions
    assert has_permission("ADMIN", "ADMIN") is True
    assert has_permission("ADMIN", "CIRCULATION") is True

    # 2. Circulation Staff Tap-Login (SC-CIRC-004)
    circ_login = SmartCardService.staff_login_by_card("SC-CIRC-004")
    assert circ_login["success"] is True
    assert circ_login["role"] == "CIRCULATION"

    # Verify Circulation staff has circulation rights, but NOT admin rights
    assert has_permission("CIRCULATION", "CIRCULATION") is True
    assert has_permission("CIRCULATION", "ADMIN") is False

def test_password_hashing_and_verification():
    raw = "SecureSecretPassword2026!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_immutable_audit_logging():
    log_id = AuditService.log(
        action="TEST_SECURITY_ACTION",
        entity="SYSTEM",
        details={"test_key": "test_val"}
    )
    assert log_id > 0

    logs = AuditService.get_logs(limit=10)
    assert any(l["action"] == "TEST_SECURITY_ACTION" for l in logs)

def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/admin/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database"]["status"] == "CONNECTED"
