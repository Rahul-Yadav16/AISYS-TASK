# Deliverable D2: Database Schema & Indexing Design

## 1. Relational Entity-Relationship Model

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : records
    MEMBERS ||--o{ CIRCULATION_TRANSACTIONS : borrows
    MEMBERS ||--o{ NOTIFICATIONS : receives
    BIBLIOGRAPHIC_RECORDS ||--|{ ITEMS : catalogued_as
    ITEMS ||--o| RFID_TAGS : identified_by
    ITEMS ||--o{ CIRCULATION_TRANSACTIONS : issued_in
    ITEMS ||--o{ GATE_SECURITY_EVENTS : triggers
    INVENTORY_AUDITS ||--o{ INVENTORY_AUDIT_ITEMS : tracks

    USERS {
        int id PK
        string username UK
        string password_hash
        string full_name
        string email
        string role
        string smart_card_uid UK
        int is_active
        datetime created_at
    }

    MEMBERS {
        int id PK
        string member_id UK
        string full_name
        string category
        string email
        string phone
        string smart_card_uid UK
        float current_fines
        int is_blocked
        string block_reason
        string expiry_date
        datetime created_at
    }

    BIBLIOGRAPHIC_RECORDS {
        int id PK
        string title
        string author
        string isbn
        string publisher
        int publication_year
        string edition
        string call_number
        string subject
        string material_type
        string virtual_shelf
        int is_reference
        string source_system
        datetime created_at
    }

    ITEMS {
        int id PK
        int biblio_id FK
        string accession_number UK
        string barcode UK
        string status
        string shelf_location
        int is_tagged
        datetime created_at
    }

    RFID_TAGS {
        int id PK
        int item_id FK,UK
        string tag_uid UK
        int eas_status
        string memory_format
        datetime last_scanned_at
        string last_reader_id
        float battery_or_rssi
        datetime created_at
    }

    CIRCULATION_TRANSACTIONS {
        int id PK
        int item_id FK
        int member_id FK
        int operator_id FK
        string transaction_type
        datetime issue_date
        datetime due_date
        datetime return_date
        int renewal_count
        float fine_amount
        int fine_paid
        string status
    }

    GATE_SECURITY_EVENTS {
        int id PK
        string gate_id
        string event_type
        string tag_uid
        string accession_number
        string item_title
        string cctv_image_path
        int alarm_sounded
        int notification_sent
        datetime timestamp
    }
```

---

## 2. Full-Text Search Table (`biblio_fts`)

To fulfill **FR 02** ("Provide a web interface, full-text search, search engine, real-time indexing"), SQLite's FTS5 virtual table engine is employed:

```sql
CREATE VIRTUAL TABLE biblio_fts USING fts5(
    title,
    author,
    isbn,
    subject,
    call_number,
    content='bibliographic_records',
    content_rowid='id'
);
```

### Real-Time Synchronous Triggers
Triggers keep `biblio_fts` updated synchronously upon any insertion, update, or deletion in `bibliographic_records`:
- `trg_biblio_ai`: AFTER INSERT ON `bibliographic_records` -> inserts into `biblio_fts`.
- `trg_biblio_ad`: AFTER DELETE ON `bibliographic_records` -> deletes from `biblio_fts`.
- `trg_biblio_au`: AFTER UPDATE ON `bibliographic_records` -> updates `biblio_fts`.

---

## 3. High-Concurrency Performance Tuning

1. **Write-Ahead Logging (WAL)**:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA foreign_keys = ON;
   PRAGMA busy_timeout = 5000;
   ```
   WAL allows concurrent readers while a write is occurring, ensuring zero reader blockage during active circulation, gate events, or migration batch processing.
2. **Index Optimization**:
   - `idx_items_accession`: `CREATE INDEX idx_items_accession ON items(accession_number);`
   - `idx_items_barcode`: `CREATE INDEX idx_items_barcode ON items(barcode);`
   - `idx_rfid_tag_uid`: `CREATE INDEX idx_rfid_tag_uid ON rfid_tags(tag_uid);`
   - `idx_circ_member_active`: `CREATE INDEX idx_circ_member_active ON circulation_transactions(member_id, status);`
   - `idx_members_card_uid`: `CREATE INDEX idx_members_card_uid ON members(smart_card_uid);`
   - `idx_users_card_uid`: `CREATE INDEX idx_users_card_uid ON users(smart_card_uid);`
