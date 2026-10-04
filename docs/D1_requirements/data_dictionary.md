# Deliverable D1: System Data Dictionary

This document defines the schema, table structures, column definitions, data types, and integrity constraints for the AISYS library and RFID database.

---

### 1. `users` (Staff & System Accounts)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `username` | TEXT | NO | - | Unique system username. |
| `password_hash` | TEXT | NO | - | PBKDF2-HMAC-SHA256 salted hash. |
| `full_name` | TEXT | NO | - | Display name of the user. |
| `email` | TEXT | YES | NULL | Staff notification email address. |
| `role` | TEXT | NO | 'CIRCULATION' | RBAC role: `ADMIN`, `LIBRARIAN`, `CATALOGUER`, `CIRCULATION`. |
| `smart_card_uid`| TEXT | YES | NULL | UID of staff contactless RFID card for fast tap-login. |
| `is_active` | INTEGER | NO | 1 | 1 = Active, 0 = Suspended. |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | ISO-8601 registration timestamp. |

---

### 2. `members` (Patrons / Borrowers)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `member_id` | TEXT | NO | - | Unique patron identifier / institutional ID (e.g. `MEM-1001`). |
| `full_name` | TEXT | NO | - | Full legal or registered name of member. |
| `category` | TEXT | NO | 'STUDENT' | Patron tier: `STUDENT`, `FACULTY`, `RESEARCHER`, `STAFF`, `PUBLIC`. |
| `email` | TEXT | YES | NULL | Member email for automated circulation notifications. |
| `phone` | TEXT | YES | NULL | Mobile number for SMS dispatch. |
| `smart_card_uid`| TEXT | YES | NULL | Contactless smart card RFID UID assigned to patron. |
| `current_fines` | REAL | NO | 0.00 | Accumulated unpaid fine balance. |
| `is_blocked` | INTEGER | NO | 0 | 1 = Borrowing privileges blocked, 0 = Clear. |
| `block_reason` | TEXT | YES | NULL | Explanation if member is blocked. |
| `expiry_date` | TEXT | YES | NULL | Membership expiry date (YYYY-MM-DD). |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | Registration timestamp. |

---

### 3. `bibliographic_records` (Titles / Cataloguing)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `title` | TEXT | NO | - | Primary title of work. |
| `author` | TEXT | NO | - | Primary creator / author. |
| `isbn` | TEXT | YES | NULL | 10 or 13-digit ISBN. |
| `publisher` | TEXT | YES | NULL | Publishing house or press. |
| `publication_year`| INTEGER | YES| NULL | Year of publication. |
| `edition` | TEXT | YES | NULL | Edition note (e.g. "3rd Edition"). |
| `call_number` | TEXT | NO | - | Dewey Decimal (DDC) or Library of Congress classification. |
| `subject` | TEXT | YES | NULL | Topical subject headings / keywords. |
| `material_type` | TEXT | NO | 'BOOK' | Media classification: `BOOK`, `REFERENCE`, `PERIODICAL`, `MEDIA`, `THESIS`. |
| `virtual_shelf`| TEXT | YES | 'Shelf-A' | Physical/virtual shelf location tag (e.g. `Shelf-A`, `Stack-02`). |
| `is_reference` | INTEGER | NO | 0 | 1 = Not eligible for check-out (in-library reading only). |
| `source_system`| TEXT | NO | 'AISYS' | Provenance tracking (`LEGACY_MIGRATION`, `AISYS_NATIVE`, `NET_CATALOG`). |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | Catalogued timestamp. |

---

### 4. `items` (Physical Copies / Accession Instances)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `biblio_id` | INTEGER | NO | - | Foreign Key -> `bibliographic_records(id)`. |
| `accession_number`| TEXT | NO | - | Unique accession number / inventory identifier (e.g. `ACC-002341`). |
| `barcode` | TEXT | NO | - | Printed barcode representation. |
| `status` | TEXT | NO | 'AVAILABLE' | Status: `AVAILABLE`, `ISSUED`, `LOST`, `DAMAGED`, `IN_TRANSIT`, `PROCESSING`. |
| `shelf_location`| TEXT | NO | - | Assigned shelf identifier (e.g. `Shelf-A-01`). |
| `is_tagged` | INTEGER | NO | 0 | 1 = RFID tag associated, 0 = Untagged. |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | Registration timestamp. |

---

### 5. `rfid_tags` (RFID Tag Mappings & Hardware Status)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `item_id` | INTEGER | NO | - | Foreign Key -> `items(id)` (UNIQUE constraint). |
| `tag_uid` | TEXT | NO | - | Unique RFID transponder chip UID (e.g. `E00401509988A1B2`). |
| `eas_status` | INTEGER | NO | 0 | Security/AFI bit: `0` = Armed (In-Library), `1` = Disarmed (Checked-Out). |
| `memory_format`| TEXT | NO | 'ISO15693_DATA_MODEL' | Encoded standard format. |
| `last_scanned_at`| TEXT | YES | NULL | Timestamp of most recent antenna read. |
| `last_reader_id`| TEXT | YES | NULL | Identifier of the last reader device detecting tag. |
| `battery_or_rssi`| REAL| YES | NULL | Signal strength indicator (RSSI in dBm) or health index. |
| `created_at` | TEXT | NO | CURRENT_TIMESTAMP | Tag binding timestamp. |

---

### 6. `circulation_transactions` (Loans, Returns, Renewals)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `item_id` | INTEGER | NO | - | Foreign Key -> `items(id)`. |
| `member_id` | INTEGER | NO | - | Foreign Key -> `members(id)`. |
| `operator_id` | INTEGER | YES | NULL | Foreign Key -> `users(id)` (or NULL if self-checkout). |
| `transaction_type`| TEXT | NO | - | `ISSUE`, `RETURN`, `RENEWAL`. |
| `issue_date` | TEXT | NO | CURRENT_TIMESTAMP | Loan initiation timestamp. |
| `due_date` | TEXT | NO | - | Expected return date. |
| `return_date` | TEXT | YES | NULL | Actual return timestamp. |
| `renewal_count` | INTEGER | NO | 0 | Number of renewals granted. |
| `fine_amount` | REAL | NO | 0.00 | Fine assessed on this transaction. |
| `fine_paid` | INTEGER | NO | 1 | 1 = Settled/Zero, 0 = Outstanding. |
| `status` | TEXT | NO | 'ACTIVE' | `ACTIVE`, `COMPLETED`, `OVERDUE`. |

---

### 7. `gate_security_events` (Security Gate Violations & Footfall)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `gate_id` | TEXT | NO | 'GATE-01' | Security gate device identifier. |
| `event_type` | TEXT | NO | 'ALARM' | `ALARM` (Unauthorized item), `PASS` (Normal exit), `FOOTFALL`. |
| `tag_uid` | TEXT | YES | NULL | Detected tag UID if triggered by unissued item. |
| `accession_number`| TEXT | YES | NULL | Resolved item accession number. |
| `item_title` | TEXT | YES | NULL | Title of detected item. |
| `cctv_image_path`| TEXT | YES | NULL | Relative path to captured snapshot (`storage/cctv_captures/...`). |
| `alarm_sounded` | INTEGER | NO | 1 | 1 = Buzzer/Strobe triggered, 0 = Silent. |
| `notification_sent`| INTEGER | NO | 0 | 1 = Security staff alert dispatched, 0 = Pending/Suppressed. |
| `timestamp` | TEXT | NO | CURRENT_TIMESTAMP | Event timestamp. |

---

### 8. `inventory_audits` & `inventory_items` (Stock Verification)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `audit_name` | TEXT | NO | - | Friendly name (e.g. "Annual CS Dept Audit - Shelf A"). |
| `shelf_target` | TEXT | NO | - | Target shelf identifier. |
| `total_expected`| INTEGER | NO | 0 | Total catalogued items registered on this shelf. |
| `total_scanned` | INTEGER | NO | 0 | Total tags detected during scan. |
| `correct_count` | INTEGER | NO | 0 | Items verified in correct location. |
| `misplaced_count`| INTEGER| NO | 0 | Items detected belonging to other shelves. |
| `missing_count` | INTEGER | NO | 0 | Items catalogued here but not detected. |
| `status` | TEXT | NO | 'IN_PROGRESS' | `IN_PROGRESS`, `COMPLETED`, `CANCELLED`. |
| `started_at` | TEXT | NO | CURRENT_TIMESTAMP | Audit start time. |
| `completed_at`| TEXT | YES | NULL | Audit completion time. |

---

### 9. `migration_staging` & `migration_errors` (20,000 Record Import Area)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `batch_id` | TEXT | NO | - | Unique UUID identifying import batch. |
| `row_index` | INTEGER | NO | - | 1-indexed row number from spreadsheet. |
| `raw_data` | TEXT | NO | - | Raw JSON payload of source record. |
| `validation_status`| TEXT| NO | 'PENDING' | `VALID`, `INVALID`, `DUPLICATE`, `MIGRATED`. |
| `error_details`| TEXT | YES | NULL | Explanatory defect description for rejected rows. |

---

### 10. `audit_logs` (System Security & Compliance)
| Column Name | Data Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | INTEGER | NO | AUTOINCREMENT | Primary Key. |
| `user_id` | INTEGER | YES | NULL | User who initiated action. |
| `action` | TEXT | NO | - | `LOGIN`, `CHECKOUT`, `CHECKIN`, `MIGRATE`, `BACKUP`, `RESTORE`, `UPDATE`, `POLICY_VIOLATION`. |
| `entity` | TEXT | NO | - | Target resource (e.g. `BIBLIO`, `MEMBER`, `SYSTEM`, `GATE`). |
| `entity_id` | TEXT | YES | NULL | Identifier of affected entity. |
| `details` | TEXT | YES | NULL | Structured JSON of prior/new values and metadata. |
| `ip_address` | TEXT | YES | '127.0.0.1' | Origin client IP address. |
| `timestamp` | TEXT | NO | CURRENT_TIMESTAMP | Audit timestamp. |
