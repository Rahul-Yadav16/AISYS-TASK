# Deliverable D8: REST & WebSocket API Reference

The AISYS application provides interactive OpenAPI / Swagger documentation at `http://localhost:8000/docs`. This reference details key integration interfaces.

---

## 1. Authentication (`/api/auth`)

### `POST /api/auth/login`
- **Body**: `{"username": "admin", "password": "AdminPass123!"}`
- **Response**: `{"success": true, "token": "...", "role": "ADMIN"}`

### `POST /api/auth/smart-card-login`
- **Body**: `{"smart_card_uid": "SC-ADMIN-001"}`
- **Response**: `{"success": true, "token": "...", "user_id": 1, "role": "ADMIN"}`

---

## 2. Cataloguing & Search (`/api/catalog`)

### `GET /api/catalog/search?q=Algorithms&limit=25`
- **Response**: `{"total": 1, "results": [{"id": 1, "title": "...", "call_number": "...", "available_copies": 2}]}`

### `GET /api/catalog/spine-label/{item_id}`
- **Response**: `{"item_id": 1, "accession_number": "ACC-001001", "svg_label": "<svg ...>"}`

### `GET /api/catalog/bookshelf?shelf_id=Shelf-A-01`
- **Response**: `[{"title": "...", "call_number": "...", "status": "AVAILABLE"}]`

---

## 3. Circulation (`/api/circulation`)

### `POST /api/circulation/checkout`
- **Body**: `{"member_identifier": "MEM-1001", "item_identifier": "ACC-001001"}`
- **Response**: `{"success": true, "transaction_id": 1, "due_date": "2026-10-18 ...", "eas_status": 1}`
- **Error (403)**: `{"detail": "Borrowing blocked for member 'MEM-1003': Suspended"}`

### `POST /api/circulation/checkin`
- **Body**: `{"item_identifier": "ACC-001001"}`
- **Response**: `{"success": true, "status": "AVAILABLE", "fine_assessed": 0.0, "shelf_destination": "Shelf-A-01"}`

---

## 4. RFID Middleware (`/api/rfid`)

### `POST /api/rfid/tag-item`
- **Body**: `{"item_identifier": "ACC-005001", "tag_uid": "E00401509988A501"}`
- **Response**: `{"success": true, "tag_uid": "E00401509988A501", "eas_status": 0}`

### `GET /api/rfid/tag/{tag_uid}`
- **Response**: `{"tag_uid": "...", "eas_status": 0, "accession_number": "...", "title": "..."}`

---

## 5. Security Gate (`/api/gate`)

### `POST /api/gate/passage`
- **Body**: `{"gate_id": "GATE-01", "detected_tag_uid": "E00401509988A101", "raw_eas_bit": 0}`
- **Response**: `{"event_id": 1, "event_type": "ALARM", "alarm": true, "accession_number": "ACC-001001", "cctv_image_path": "/api/gate/cctv/cctv_GATE-01_....jpg"}`

---

## 6. Migration (`/api/migration`)

### `POST /api/migration/ingest-local`
- **Body**: `{"filepath": "data/sample_import_20000.csv"}`
- **Response**: `{"batch_id": "BATCH-...", "total_rows_ingested": 20000, "pre_migration_backup": "..."}`

### `POST /api/migration/validate/{batch_id}`
- **Response**: `{"total_rows_profiled": 20000, "valid_records": 19850, "invalid_records": 100, "duplicate_records": 50, "reconciliation_checksum_match": true}`

### `POST /api/migration/commit/{batch_id}`
- **Response**: `{"success": true, "migrated_records": 19850, "status": "COMMITTED"}`

### `POST /api/migration/rollback/{batch_id}`
- **Response**: `{"success": true, "deleted_items": 19850, "deleted_bibliographic_records": 19850, "status": "ROLLED_BACK"}`

---

## 7. Interoperability (`/api/interop`)

### `POST /api/interop/sip2/message`
- **Body**: `{"raw_message": "11YN20261004    19000020261018    190000AOAISYS|AAMEM-1001|ABACC-001001|"}`
- **Response**: `{"response": "121NY...|AY1AZ..."}`

### `POST /api/interop/ncip/v2`
- **Body**: `{"service": "CheckOutItem", "payload": {"user_id": "MEM-1001", "item_id": "ACC-001001"}}`
- **Response**: `{"ncip_message": "CheckOutItemResponse", "status": "SUCCESS", "date_due": "..."}`
