"""
Synthetic seed data generator for AISYS.
Populates standard baseline users, members, catalog, items, RFID tags, and policies.
Guarantees 100% synthetic data per NFR 02.
"""
from src.core.database import db_manager
from src.core.security import hash_password
from src.core.logger import logger

def seed_database():
    logger.info("Starting baseline synthetic database seeding...")

    with db_manager.transaction() as conn:
        # 1. Seed Users & Staff
        users_data = [
            ("admin", "AdminPass123!", "System Administrator", "admin@aisys.local", "ADMIN", "SC-ADMIN-001"),
            ("librarian", "LibPass123!", "Senior Librarian", "librarian@aisys.local", "LIBRARIAN", "SC-LIB-002"),
            ("cataloguer", "CatPass123!", "Technical Cataloguer", "cataloguer@aisys.local", "CATALOGUER", "SC-CAT-003"),
            ("circulation", "CircPass123!", "Circulation Desk Staff", "circ@aisys.local", "CIRCULATION", "SC-CIRC-004")
        ]

        for username, raw_pass, full_name, email, role, card_uid in users_data:
            pw_hash = hash_password(raw_pass)
            conn.execute("""
                INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role, smart_card_uid, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (username, pw_hash, full_name, email, role, card_uid))

        # 2. Seed Members / Patrons
        # Includes: standard patron, blocked patron, high-fine patron, faculty
        members_data = [
            ("MEM-1001", "Alice Smith (Student)", "STUDENT", "alice@example.com", "+1555123401", "CARD-MEM-1001", 0.00, 0, None, "2027-12-31"),
            ("MEM-1002", "Prof. Robert Davis (Faculty)", "FACULTY", "robert@example.com", "+1555123402", "CARD-MEM-1002", 0.00, 0, None, "2028-12-31"),
            ("MEM-1003", "Charlie Brown (Blocked Member)", "STUDENT", "charlie@example.com", "+1555123403", "CARD-MEM-1003", 0.00, 1, "Suspended for damaged media", "2026-06-30"),
            ("MEM-1004", "Diana Prince (High Fine Member)", "STUDENT", "diana@example.com", "+1555123404", "CARD-MEM-1004", 15.50, 0, None, "2027-12-31"),
            ("MEM-1005", "Evan Wright (Researcher)", "RESEARCHER", "evan@example.com", "+1555123405", "CARD-MEM-1005", 2.00, 0, None, "2027-12-31")
        ]

        for mid, name, cat, email, phone, card_uid, fines, blocked, reason, exp in members_data:
            conn.execute("""
                INSERT OR IGNORE INTO members (member_id, full_name, category, email, phone, smart_card_uid, current_fines, is_blocked, block_reason, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mid, name, cat, email, phone, card_uid, fines, blocked, reason, exp))

        # 3. Seed Bibliographic Records (Titles)
        # Includes normal books and a Reference-only book (is_reference = 1)
        biblio_data = [
            ("Introduction to Algorithms (4th Edition)", "Thomas H. Cormen, Charles E. Leiserson", "9780262046305", "MIT Press", 2022, "4th", "005.13 COR", "Computer Science, Algorithms", "BOOK", "Shelf-A-01", 0),
            ("Oxford English Dictionary (Reference Only)", "Oxford University Press", "9780198611868", "Oxford University Press", 2020, "2nd", "423 OXF", "Linguistics, Reference, Dictionaries", "REFERENCE", "Shelf-REF-01", 1),
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "9780134610993", "Pearson", 2020, "4th", "006.3 RUS", "Computer Science, AI, Machine Learning", "BOOK", "Shelf-A-02", 0),
            ("Clean Architecture: A Craftsman's Guide", "Robert C. Martin", "9780134494166", "Prentice Hall", 2017, "1st", "005.1 MAR", "Software Engineering, Architecture", "BOOK", "Shelf-A-03", 0),
            ("Database System Concepts", "Abraham Silberschatz, Henry F. Korth", "9780078022159", "McGraw-Hill", 2019, "7th", "005.74 SIL", "Database Systems, SQL", "BOOK", "Shelf-B-01", 0)
        ]

        for title, author, isbn, publisher, year, ed, call, subj, mat, shelf, is_ref in biblio_data:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO bibliographic_records (title, author, isbn, publisher, publication_year, edition, call_number, subject, material_type, virtual_shelf, is_reference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, author, isbn, publisher, year, ed, call, subj, mat, shelf, is_ref))

        # Retrieve bib IDs
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, is_reference FROM bibliographic_records")
        bib_rows = cursor.fetchall()
        bib_map = {row["title"]: row["id"] for row in bib_rows}

        # 4. Seed Physical Items & Accessions
        items_data = [
            (bib_map.get("Introduction to Algorithms (4th Edition)"), "ACC-001001", "BC-001001", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("Introduction to Algorithms (4th Edition)"), "ACC-001002", "BC-001002", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("Oxford English Dictionary (Reference Only)"), "ACC-002001", "BC-002001", "AVAILABLE", "Shelf-REF-01", 1),
            (bib_map.get("Artificial Intelligence: A Modern Approach"), "ACC-003001", "BC-003001", "AVAILABLE", "Shelf-A-02", 1),
            (bib_map.get("Clean Architecture: A Craftsman's Guide"), "ACC-004001", "BC-004001", "AVAILABLE", "Shelf-A-03", 1),
            (bib_map.get("Database System Concepts"), "ACC-005001", "BC-005001", "AVAILABLE", "Shelf-B-01", 0) # Untagged for tagging tests
        ]

        for bib_id, acc, bc, status, shelf, tagged in items_data:
            if bib_id:
                conn.execute("""
                    INSERT OR IGNORE INTO items (biblio_id, accession_number, barcode, status, shelf_location, is_tagged)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bib_id, acc, bc, status, shelf, tagged))

        # Retrieve items
        cursor.execute("SELECT id, accession_number FROM items")
        item_rows = cursor.fetchall()
        item_map = {row["accession_number"]: row["id"] for row in item_rows}

        # 5. Seed RFID Tags
        # EAS Status: 0 = Armed (In-Library), 1 = Disarmed (Checked out)
        tags_data = [
            (item_map.get("ACC-001001"), "E00401509988A101", 0, "ISO15693_DATA_MODEL", -45.5),
            (item_map.get("ACC-001002"), "E00401509988A102", 0, "ISO15693_DATA_MODEL", -48.0),
            (item_map.get("ACC-002001"), "E00401509988A201", 0, "ISO15693_DATA_MODEL", -42.1), # Reference item
            (item_map.get("ACC-003001"), "E00401509988A301", 0, "ISO15693_DATA_MODEL", -50.2),
            (item_map.get("ACC-004001"), "E00401509988A401", 0, "ISO15693_DATA_MODEL", -46.7)
        ]

        for item_id, tag_uid, eas, fmt, rssi in tags_data:
            if item_id:
                conn.execute("""
                    INSERT OR IGNORE INTO rfid_tags (item_id, tag_uid, eas_status, memory_format, battery_or_rssi, last_reader_id)
                    VALUES (?, ?, ?, ?, ?, 'STAFF-READER-01')
                """, (item_id, tag_uid, eas, fmt, rssi))

    logger.info("Baseline synthetic seed data successfully applied.")

if __name__ == "__main__":
    db_manager.apply_migrations()
    seed_database()
