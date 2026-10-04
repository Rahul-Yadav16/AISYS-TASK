# Deliverable D2: Interface and Adapter Specifications

## 1. 3M SIP2 Protocol Adapter Specification

The 3M Standard Interchange Protocol (SIP2) enables automated self-check stations, book drops, and security gates to communicate with the ILMS.

### Supported SIP2 Commands & Frames

| Code | Direction | Message Name | Description |
|---|---|---|---|
| `99 / 98` | Client -> Host | SC Status / ACS Status | Handshake exchanging protocol version, online status, supported features. |
| `11 / 12` | Client -> Host | Checkout / Checkout Response | Issues item to patron, verifies limits, updates transaction history. |
| `09 / 10` | Client -> Host | Checkin / Checkin Response | Returns item to shelf status, resets EAS bit to armed. |
| `29 / 30` | Client -> Host | Renew / Renew Response | Extends active loan duration. |
| `63 / 64` | Client -> Host | Patron Information / Response | Returns patron status, active loan count, fine balance, block flag. |
| `17 / 18` | Client -> Host | Item Information / Response | Returns item status, circulation history, hold queue. |

### SIP2 Frame Format & Checksum
- Fixed-width header followed by variable delimited fields: `field_id + value + '|'`
- Checksum validation: 2-character hexadecimal sum of characters modulo 65536.
- Example Checkout Request (`11`):
  `11YN20261004    19000020261018    190000AOinstitution|AApatron_id|ABitem_barcode|ACterminal_pwd|AY1AZF243`
- Adapter Mock: Handled by `src/adapters/sip2_adapter.py`.

---

## 2. NISO NCIP 2.0 Adapter Specification

The ANSI/NISO Z39.83-1 (NCIP 2.0) protocol standardizes XML-based interoperability between library applications.

### Supported NCIP Services
1. `LookupUser`: Queries patron eligibility, balance, contact information.
2. `CheckOutItem`: Initiates loan, validates reference restrictions and fine ceilings.
3. `CheckInItem`: Closes loan, clears patron liability.
4. `RenewItem`: Extends due date.

### NCIP 2.0 XML Schema Excerpt
```xml
<ns1:NCIPMessage xmlns:ns1="http://www.niso.org/2000/inclusion">
  <ns1:CheckOutItemResponse>
    <ns1:ResponseHeader>
      <ns1:TransactionId>TX-20261004-9842</ns1:TransactionId>
    </ns1:ResponseHeader>
    <ns1:ItemId>
      <ns1:ItemIdentifierValue>ACC-001004</ns1:ItemIdentifierValue>
    </ns1:ItemId>
    <ns1:UserId>
      <ns1:UserIdentifierValue>MEM-1001</ns1:UserIdentifierValue>
    </ns1:UserId>
    <ns1:DateDue>2026-10-18T23:59:59Z</ns1:DateDue>
    <ns1:ItemOptionalFields>
      <ns1:BibliographicDescription>
        <ns1:Title>Introduction to Algorithms</ns1:Title>
      </ns1:BibliographicDescription>
    </ns1:ItemOptionalFields>
  </ns1:CheckOutItemResponse>
</ns1:NCIPMessage>
```
- Adapter Mock: Implemented in `src/adapters/ncip_adapter.py` supporting both XML and JSON REST representations.

---

## 3. RFID Middleware Device Abstraction

All hardware interactions route through `src/middleware/rfid_manager.py` using standard protocol-agnostic interfaces:

```python
class RFIDReaderInterface:
    def connect(self, port_or_ip: str) -> bool: ...
    def inventory(self) -> list[RFIDTagRead]: ...
    def read_memory(self, tag_uid: str, block: int) -> bytes: ...
    def write_memory(self, tag_uid: str, block: int, data: bytes) -> bool: ...
    def set_eas(self, tag_uid: str, state: int) -> bool: ... # 0=Armed, 1=Disarmed
    def get_eas(self, tag_uid: str) -> int: ...
```

### Device Implementations:
- **Staff Station**: Single-item or multi-item near-field tag encoder. Disarms EAS upon checkout; rearms EAS upon return.
- **Handheld Reader**: Long-range wand emitting continuous tag bursts during shelf sweeps. Computes missing and misplaced items in real time.
- **Security Gate**: Independent reader listening continuously on egress antennas. Reads AFI/EAS byte directly from tag. If EAS = `0x00`, sounds local siren and fires `UNAUTHORIZED_PASSAGE` event.
- **Smart Card Reader**: Near-field 13.56MHz reader reading ISO 14443 Type A/B UIDs for staff authentication and patron self-service.

---

## 4. CCTV Camera Mock Adapter

When an unauthorized item passes through the gate, the security gate triggers `src/adapters/camera_adapter.py`.
- **Method**: `capture_snapshot(gate_id: str, trigger_event: str) -> str`
- **Output**: Generates a high-contrast mock JPEG image timestamped with incident details, gate ID, detected accession number, and simulated security frame overlay into `storage/cctv_captures/`.
- **Retention & URL**: Accessible to authorized security personnel via `/api/gate/cctv/{filename}`.

---

## 5. Provider-Neutral Notification Adapter

To prevent vendor lock-in to external SMS or email gateways (e.g., Twilio, SendGrid), AISYS defines provider-neutral adapters:
- **Email**: Dispatches SMTP messages or writes to an inspectable mock spool in `storage/staging/email_spool.json`.
- **SMS**: Formats SMS notifications or logs to `storage/staging/sms_spool.json`.
- **Print**: Emulates ESC/POS thermal printers, formatting formatted circulation receipts and spine/barcode label slips stored in `storage/labels/`.

---

## 6. Non-Destructive Existing ILMS Sync Adapter (NFR 01)

The legacy ILMS connector (`src/adapters/ilms_adapter.py`) enforces strict read-only query contracts:
- Uses SQLite/ODBC connection strings in read-only mode (`PRAGMA query_only = ON;`).
- All queries utilize `SELECT ...`. Any attempt to execute `INSERT`, `UPDATE`, `DELETE`, `DROP`, or `ALTER` raises a strict runtime `SecurityViolationError`.
- Synchronization records are imported into an isolated delta audit log, ensuring existing legacy records are never mutated or corrupted.
