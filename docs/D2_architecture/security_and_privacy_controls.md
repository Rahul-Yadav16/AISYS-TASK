# Deliverable D2: Security, Privacy, and Access Controls

## 1. Role-Based Access Control (RBAC) Matrix

AISYS enforces the principle of least privilege across all functional endpoints and UI capabilities:

| Role | Cataloguing | Circulation | Member Management | RFID Tagging | Inventory Audit | Security Monitor | Migration & DB Admin |
|---|---|---|---|---|---|---|---|
| **ADMIN** | Full | Full | Full | Full | Full | Full | Full |
| **LIBRARIAN** | Full | Full | Full | Full | Full | View Only | View Only |
| **CATALOGUER** | Full | Read Only | Read Only | Full | Read Only | Denied | Denied |
| **CIRCULATION** | Read Only | Full | Full | Full | Read Only | Read Only | Denied |
| **PATRON (OPAC)**| Search Only| Self-Check | View Profile | Denied | Denied | Denied | Denied |

---

## 2. Authentication & Credential Storage

1. **Password Security**:
   - Passwords are never stored in plaintext.
   - Salted hashes are computed using PBKDF2 with SHA-256 and 100,000 iterations.
2. **Staff Smart Card Authentication**:
   - Staff members can log in by tapping an authorized contactless smart card.
   - Smart card UIDs are verified against the active users directory and mapped to their RBAC role.
3. **Session Tokens**:
   - Ephemeral cryptographically random session tokens are issued with a configurable TTL (default: 8 hours).
   - Sessions are revoked immediately upon logout or account suspension.

---

## 3. Data Protection and Synthetic Data Isolation (NFR 01, NFR 02)

1. **Strictly Synthetic Data**:
   - Per project guidelines and SOP Section 3/Stage 1, no real student, faculty, or institutional records are present or used in test environments.
   - All sample records are generated synthetically with fictitious names, titles, and generated identifiers.
2. **Immutable Audit Trail**:
   - Every security-sensitive transaction (login, check-out, policy bypass, database backup, restore, migration batch commit/rollback) is logged to `audit_logs`.
   - Audit logs contain: Actor ID, IP Address, Timestamp, Action Verb, Affected Entity, and a JSON diff of changed parameters.
   - Audit logs cannot be modified or deleted via any standard API endpoint.
3. **Log Sanitization**:
   - Credit card numbers, raw passwords, or private encryption keys are automatically masked if present in request payloads before being written to operational logs.
