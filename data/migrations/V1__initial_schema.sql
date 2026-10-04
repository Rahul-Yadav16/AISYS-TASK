-- V1__initial_schema.sql
-- AISYS Library & RFID Middleware Baseline Schema
-- Target: SQLite 3.35+ with FTS5 enabled

PRAGMA foreign_keys = ON;

-- 1. System Users & Staff Accounts
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'CIRCULATION', -- 'ADMIN', 'LIBRARIAN', 'CATALOGUER', 'CIRCULATION'
    smart_card_uid TEXT UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 2. Library Members / Patrons
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'STUDENT', -- 'STUDENT', 'FACULTY', 'STAFF', 'PUBLIC'
    email TEXT,
    phone TEXT,
    smart_card_uid TEXT UNIQUE,
    current_fines REAL NOT NULL DEFAULT 0.00,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    block_reason TEXT,
    expiry_date TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 3. Bibliographic Records (Cataloguing & Titles)
CREATE TABLE IF NOT EXISTS bibliographic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT,
    publisher TEXT,
    publication_year INTEGER,
    edition TEXT,
    call_number TEXT NOT NULL,
    subject TEXT,
    material_type TEXT NOT NULL DEFAULT 'BOOK', -- 'BOOK', 'REFERENCE', 'PERIODICAL', 'MEDIA', 'THESIS'
    virtual_shelf TEXT DEFAULT 'Shelf-A',
    is_reference INTEGER NOT NULL DEFAULT 0,
    source_system TEXT NOT NULL DEFAULT 'AISYS', -- 'AISYS', 'LEGACY_MIGRATION', 'NET_CATALOG'
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 4. Physical Items / Accessions
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    biblio_id INTEGER NOT NULL REFERENCES bibliographic_records(id) ON DELETE CASCADE,
    accession_number TEXT NOT NULL UNIQUE,
    barcode TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'ISSUED', 'LOST', 'DAMAGED', 'IN_TRANSIT'
    shelf_location TEXT NOT NULL,
    is_tagged INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 5. RFID Tag Mappings & Transponder Metadata
CREATE TABLE IF NOT EXISTS rfid_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
    tag_uid TEXT NOT NULL UNIQUE,
    eas_status INTEGER NOT NULL DEFAULT 0, -- 0 = Armed/Protected (In-Library), 1 = Disarmed (Checked Out)
    memory_format TEXT NOT NULL DEFAULT 'ISO15693_DATA_MODEL',
    last_scanned_at TEXT,
    last_reader_id TEXT,
    battery_or_rssi REAL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 6. Circulation Transactions
CREATE TABLE IF NOT EXISTS circulation_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    operator_id INTEGER REFERENCES users(id),
    transaction_type TEXT NOT NULL, -- 'ISSUE', 'RETURN', 'RENEWAL'
    issue_date TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    due_date TEXT NOT NULL,
    return_date TEXT,
    renewal_count INTEGER NOT NULL DEFAULT 0,
    fine_amount REAL NOT NULL DEFAULT 0.00,
    fine_paid INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ACTIVE' -- 'ACTIVE', 'RETURNED', 'OVERDUE'
);

-- 7. Security Gate Events & Alarms
CREATE TABLE IF NOT EXISTS gate_security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_id TEXT NOT NULL DEFAULT 'GATE-01',
    event_type TEXT NOT NULL, -- 'ALARM', 'PASS', 'FOOTFALL'
    tag_uid TEXT,
    accession_number TEXT,
    item_title TEXT,
    cctv_image_path TEXT,
    alarm_sounded INTEGER NOT NULL DEFAULT 1,
    notification_sent INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 8. Inventory Audits & Shelf Verification
CREATE TABLE IF NOT EXISTS inventory_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_name TEXT NOT NULL,
    shelf_target TEXT NOT NULL,
    total_expected INTEGER NOT NULL DEFAULT 0,
    total_scanned INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    misplaced_count INTEGER NOT NULL DEFAULT 0,
    missing_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'IN_PROGRESS', -- 'IN_PROGRESS', 'COMPLETED'
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL REFERENCES inventory_audits(id) ON DELETE CASCADE,
    tag_uid TEXT NOT NULL,
    accession_number TEXT,
    shelf_detected TEXT,
    status TEXT NOT NULL, -- 'CORRECT', 'MISPLACED', 'UNKNOWN'
    scanned_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 9. Migration Staging & Error Log
CREATE TABLE IF NOT EXISTS migration_staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    raw_data TEXT NOT NULL,
    validation_status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'VALID', 'INVALID', 'DUPLICATE', 'MIGRATED'
    error_details TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS migration_batches (
    batch_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    invalid_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    migrated_rows INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'STAGED', -- 'STAGED', 'VALIDATED', 'COMMITTED', 'ROLLED_BACK'
    started_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    completed_at TEXT
);

-- 10. Audit Trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    ip_address TEXT DEFAULT '127.0.0.1',
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 11. Schema Migrations History Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 12. Full-Text Search (SQLite FTS5) Table & Triggers
CREATE VIRTUAL TABLE IF NOT EXISTS biblio_fts USING fts5(
    title,
    author,
    isbn,
    subject,
    call_number,
    content='bibliographic_records',
    content_rowid='id'
);

-- Real-Time Triggers for FTS5 Synchronization
CREATE TRIGGER IF NOT EXISTS trg_biblio_ai AFTER INSERT ON bibliographic_records BEGIN
    INSERT INTO biblio_fts(rowid, title, author, isbn, subject, call_number)
    VALUES (new.id, new.title, new.author, new.isbn, new.subject, new.call_number);
END;

CREATE TRIGGER IF NOT EXISTS trg_biblio_ad AFTER DELETE ON bibliographic_records BEGIN
    INSERT INTO biblio_fts(biblio_fts, rowid, title, author, isbn, subject, call_number)
    VALUES ('delete', old.id, old.title, old.author, old.isbn, old.subject, old.call_number);
END;

CREATE TRIGGER IF NOT EXISTS trg_biblio_au AFTER UPDATE ON bibliographic_records BEGIN
    INSERT INTO biblio_fts(biblio_fts, rowid, title, author, isbn, subject, call_number)
    VALUES ('delete', old.id, old.title, old.author, old.isbn, old.subject, old.call_number);
    INSERT INTO biblio_fts(rowid, title, author, isbn, subject, call_number)
    VALUES (new.id, new.title, new.author, new.isbn, new.subject, new.call_number);
END;

-- Record Baseline Schema Migration
INSERT OR IGNORE INTO schema_migrations (version) VALUES ('V1__initial_schema');
