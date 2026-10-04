# Deliverable D9: Known Limitations & Candidate Implementation Boundaries

In accordance with SOP Section 3 (Scope Boundaries) and Section 7 (Deliverable D9), this document explicitly records all design constraints, mock boundaries, and environment limitations of the candidate prototype.

---

## 1. Hardware & Physical Device Boundaries
1. **Mock Device Adapters**:
   - Physical RFID hardware (Feig Electronic, Nordic ID, Alien Technology, Impinj) interfaces are represented by software mock adapters and protocol parsers (`src/middleware/`).
   - Physical serial COM ports or raw LLRP Ethernet streams require vendor-supplied Windows C/C++ DLL drivers when migrating from prototype to live physical hardware installation.
2. **Camera / CCTV Feed**:
   - The CCTV adapter simulates video frame capture by generating synthetic surveillance frames timestamped with gate incident metadata into `storage/cctv_captures/`.
   - Production integration requires RTSP or ONVIF protocol streaming from physical institutional IP security cameras.

---

## 2. Network & Storage Boundaries
1. **Single-Node Embedded Database**:
   - SQLite 3 with Write-Ahead Logging (WAL) is optimized for local isolated servers with up to 250,000 records and ~100 concurrent requests/second.
   - For multi-campus university consortia exceeding 2,000,000 records and hundreds of concurrent self-check kiosks, the database abstraction layer can be transitioned to PostgreSQL or Microsoft SQL Server.
2. **Offline Spooling for Notifications**:
   - In air-gapped environments without an internal SMTP relay or SMS hardware modem, emails and SMS messages are routed to inspectable JSON spool files in `storage/staging/`.

---

## 3. Standard Protocol Mock Boundaries
1. **3M SIP2 Encoding**:
   - Supports core circulation frames (`11/12`, `09/10`, `29/30`, `63/64`, `99/98`). Proprietary vendor extensions (e.g. 3M specific magnetic media desensitizer commands) are excluded from the candidate prototype.
2. **NCIP 2.0 Coverage**:
   - Covers primary circulation profile services (`LookupUser`, `CheckOutItem`, `CheckInItem`, `RenewItem`). Inter-library loan (ILL) and fiscal billing transfer services are documented in the production-completion backlog.
