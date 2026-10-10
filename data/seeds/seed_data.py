"""
Synthetic seed data generator for AISYS.
Populates standard baseline users, members, catalog, items, RFID tags, and policies.
Guarantees 100% synthetic data per NFR 02.
Fulfills FR 01, FR 02, FR 03, FR 04, FR 05, FR 06, FR 07.
"""
from src.core.database import db_manager
from src.core.security import hash_password
from src.core.logger import logger

def seed_database():
    logger.info("Starting baseline synthetic database seeding...")

    with db_manager.transaction() as conn:
        # Clean up any orphaned duplicate bibliographic records from previous runs
        conn.execute("""
            DELETE FROM bibliographic_records 
            WHERE id > 5 AND id NOT IN (SELECT DISTINCT biblio_id FROM items)
        """)

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
        # Includes: standard patron, blocked patron, high-fine patron, faculty, researcher
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

        # 3. Seed Bibliographic Records (Titles across multiple Virtual Shelves)
        biblio_data = [
            # Shelf-A-01: Computer Science - Algorithms & Foundations
            ("Introduction to Algorithms (4th Edition)", "Thomas H. Cormen, Charles E. Leiserson", "9780262046305", "MIT Press", 2022, "4th", "005.13 COR", "Computer Science, Algorithms", "BOOK", "Shelf-A-01", 0),
            ("The Algorithm Design Manual (3rd Edition)", "Steven S. Skiena", "9783030542559", "Springer", 2020, "3rd", "005.13 SKI", "Algorithms, Data Structures", "BOOK", "Shelf-A-01", 0),
            ("Structure and Interpretation of Computer Programs", "Harold Abelson, Gerald Jay Sussman", "9780262510875", "MIT Press", 1996, "2nd", "005.13 ABE", "Programming, Lisp, Computer Science", "BOOK", "Shelf-A-01", 0),
            ("The Art of Computer Programming, Vol 1", "Donald E. Knuth", "9780201896831", "Addison-Wesley", 1997, "3rd", "005.1 KNU", "Algorithms, Information Structures", "BOOK", "Shelf-A-01", 0),

            # Shelf-REF-01: Reference Collection (Restricted)
            ("Oxford English Dictionary (Reference Only)", "Oxford University Press", "9780198611868", "Oxford University Press", 2020, "2nd", "423 OXF", "Linguistics, Reference, Dictionaries", "REFERENCE", "Shelf-REF-01", 1),
            ("Encyclopaedia Britannica Academic Edition (Reference)", "Encyclopaedia Britannica Inc", "9781593392925", "Britannica", 2021, "15th", "031 BRI", "Encyclopedias, General Reference", "REFERENCE", "Shelf-REF-01", 1),
            ("CRC Handbook of Chemistry and Physics (Reference)", "John R. Rumble", "9781138561632", "CRC Press", 2023, "104th", "540 CRC", "Chemistry, Physics, Physical Constants", "REFERENCE", "Shelf-REF-01", 1),

            # Shelf-A-02: Artificial Intelligence & Machine Learning
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "9780134610993", "Pearson", 2020, "4th", "006.3 RUS", "Computer Science, AI, Machine Learning", "BOOK", "Shelf-A-02", 0),
            ("Deep Learning", "Ian Goodfellow, Yoshua Bengio, Aaron Courville", "9780262035613", "MIT Press", 2016, "1st", "006.32 GOO", "Deep Learning, Neural Networks", "BOOK", "Shelf-A-02", 0),
            ("Pattern Recognition and Machine Learning", "Christopher M. Bishop", "9780387310732", "Springer", 2006, "1st", "006.31 BIS", "Machine Learning, Bayesian Methods", "BOOK", "Shelf-A-02", 0),
            ("Reinforcement Learning: An Introduction", "Richard S. Sutton, Andrew G. Barto", "9780262039246", "MIT Press", 2018, "2nd", "006.31 SUT", "Reinforcement Learning, Markov Decision", "BOOK", "Shelf-A-02", 0),

            # Shelf-A-03: Software Engineering & Architecture
            ("Clean Architecture: A Craftsman's Guide", "Robert C. Martin", "9780134494166", "Prentice Hall", 2017, "1st", "005.1 MAR", "Software Engineering, Architecture", "BOOK", "Shelf-A-03", 0),
            ("Design Patterns: Elements of Reusable Object-Oriented Software", "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides", "9780201633610", "Addison-Wesley", 1994, "1st", "005.12 GAM", "Design Patterns, Object-Oriented", "BOOK", "Shelf-A-03", 0),
            ("The Pragmatic Programmer (20th Anniversary Edition)", "David Thomas, Andrew Hunt", "9780135957059", "Addison-Wesley", 2019, "2nd", "005.1 THO", "Software Craftsmanship, Best Practices", "BOOK", "Shelf-A-03", 0),
            ("Refactoring: Improving the Design of Existing Code", "Martin Fowler", "9780134757599", "Addison-Wesley", 2018, "2nd", "005.16 FOW", "Refactoring, Code Quality", "BOOK", "Shelf-A-03", 0),

            # Shelf-B-01: Database Systems & Data Engineering
            ("Database System Concepts", "Abraham Silberschatz, Henry F. Korth", "9780078022159", "McGraw-Hill", 2019, "7th", "005.74 SIL", "Database Systems, SQL", "BOOK", "Shelf-B-01", 0),
            ("Designing Data-Intensive Applications", "Martin Kleppmann", "9781449373320", "O'Reilly Media", 2017, "1st", "005.74 KLE", "Distributed Systems, Data Engineering, NoSQL", "BOOK", "Shelf-B-01", 0),
            ("Database Internals: A Deep Dive into Distributed Systems", "Alex Petrov", "9781492040347", "O'Reilly Media", 2019, "1st", "005.74 PET", "Storage Engines, Distributed Databases", "BOOK", "Shelf-B-01", 0),

            # Shelf-NET-01: Networks & Operating Systems
            ("Computer Networks: A Systems Approach", "Larry L. Peterson, Bruce S. Davie", "9780128182000", "Morgan Kaufmann", 2021, "6th", "004.6 PET", "Computer Networks, Protocols", "BOOK", "Shelf-NET-01", 0),
            ("TCP/IP Illustrated, Volume 1: The Protocols", "W. Richard Stevens, Kevin R. Fall", "9780321336316", "Addison-Wesley", 2011, "2nd", "004.62 STE", "TCP/IP, Networking, Internet", "BOOK", "Shelf-NET-01", 0),
            ("Operating Systems: Three Easy Pieces", "Remzi H. Arpaci-Dusseau, Andrea C. Arpaci-Dusseau", "9781985086593", "CreateSpace", 2018, "1st", "005.43 ARP", "Operating Systems, Virtualization, Concurrency", "BOOK", "Shelf-NET-01", 0),

            # Shelf-LIT-01: Literature & Classics
            ("To Kill a Mockingbird", "Harper Lee", "9780060935467", "Harper Perennial", 2002, "50th", "813.54 LEE", "American Literature, Classic Fiction", "BOOK", "Shelf-LIT-01", 0),
            ("1984: A Novel", "George Orwell", "9780451524935", "Signet Classic", 1950, "1st", "823.912 ORW", "Dystopian, Classic Literature, Political Fiction", "BOOK", "Shelf-LIT-01", 0),
            ("The Republic", "Plato", "9780140455526", "Penguin Classics", 2007, "Reissue", "184 PLA", "Philosophy, Classical Greek, Ethics", "BOOK", "Shelf-LIT-01", 0)
        ]

        cursor = conn.cursor()
        for title, author, isbn, publisher, year, ed, call, subj, mat, shelf, is_ref in biblio_data:
            cursor.execute("SELECT id FROM bibliographic_records WHERE title = ?", (title,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("""
                    INSERT INTO bibliographic_records (title, author, isbn, publisher, publication_year, edition, call_number, subject, material_type, virtual_shelf, is_reference)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, author, isbn, publisher, year, ed, call, subj, mat, shelf, is_ref))

        # Retrieve all bibliographic record IDs mapped by title
        cursor.execute("SELECT id, title, is_reference FROM bibliographic_records")
        bib_map = {row["title"]: row["id"] for row in cursor.fetchall()}

        # 4. Seed Physical Items & Accessions
        # Keep exact baseline accessions (ACC-001001 through ACC-005001) for test compatibility
        items_data = [
            # Baseline test fixtures
            (bib_map.get("Introduction to Algorithms (4th Edition)"), "ACC-001001", "BC-001001", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("Introduction to Algorithms (4th Edition)"), "ACC-001002", "BC-001002", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("Oxford English Dictionary (Reference Only)"), "ACC-002001", "BC-002001", "AVAILABLE", "Shelf-REF-01", 1),
            (bib_map.get("Artificial Intelligence: A Modern Approach"), "ACC-003001", "BC-003001", "AVAILABLE", "Shelf-A-02", 1),
            (bib_map.get("Clean Architecture: A Craftsman's Guide"), "ACC-004001", "BC-004001", "AVAILABLE", "Shelf-A-03", 1),
            (bib_map.get("Database System Concepts"), "ACC-005001", "BC-005001", "AVAILABLE", "Shelf-B-01", 0), # Untagged for tagging tests

            # Additional shelf stock
            (bib_map.get("The Algorithm Design Manual (3rd Edition)"), "ACC-001003", "BC-001003", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("Structure and Interpretation of Computer Programs"), "ACC-001004", "BC-001004", "AVAILABLE", "Shelf-A-01", 1),
            (bib_map.get("The Art of Computer Programming, Vol 1"), "ACC-001005", "BC-001005", "AVAILABLE", "Shelf-A-01", 1),

            (bib_map.get("Encyclopaedia Britannica Academic Edition (Reference)"), "ACC-002002", "BC-002002", "AVAILABLE", "Shelf-REF-01", 1),
            (bib_map.get("CRC Handbook of Chemistry and Physics (Reference)"), "ACC-002003", "BC-002003", "AVAILABLE", "Shelf-REF-01", 1),

            (bib_map.get("Deep Learning"), "ACC-003002", "BC-003002", "AVAILABLE", "Shelf-A-02", 1),
            (bib_map.get("Pattern Recognition and Machine Learning"), "ACC-003003", "BC-003003", "AVAILABLE", "Shelf-A-02", 1),
            (bib_map.get("Reinforcement Learning: An Introduction"), "ACC-003004", "BC-003004", "AVAILABLE", "Shelf-A-02", 1),

            (bib_map.get("Design Patterns: Elements of Reusable Object-Oriented Software"), "ACC-004002", "BC-004002", "AVAILABLE", "Shelf-A-03", 1),
            (bib_map.get("The Pragmatic Programmer (20th Anniversary Edition)"), "ACC-004003", "BC-004003", "AVAILABLE", "Shelf-A-03", 1),
            (bib_map.get("Refactoring: Improving the Design of Existing Code"), "ACC-004004", "BC-004004", "AVAILABLE", "Shelf-A-03", 1),

            (bib_map.get("Designing Data-Intensive Applications"), "ACC-005002", "BC-005002", "AVAILABLE", "Shelf-B-01", 1),
            (bib_map.get("Database Internals: A Deep Dive into Distributed Systems"), "ACC-005003", "BC-005003", "AVAILABLE", "Shelf-B-01", 1),

            (bib_map.get("Computer Networks: A Systems Approach"), "ACC-006001", "BC-006001", "AVAILABLE", "Shelf-NET-01", 1),
            (bib_map.get("TCP/IP Illustrated, Volume 1: The Protocols"), "ACC-006002", "BC-006002", "AVAILABLE", "Shelf-NET-01", 1),
            (bib_map.get("Operating Systems: Three Easy Pieces"), "ACC-006003", "BC-006003", "AVAILABLE", "Shelf-NET-01", 1),

            (bib_map.get("To Kill a Mockingbird"), "ACC-007001", "BC-007001", "AVAILABLE", "Shelf-LIT-01", 1),
            (bib_map.get("1984: A Novel"), "ACC-007002", "BC-007002", "AVAILABLE", "Shelf-LIT-01", 1),
            (bib_map.get("The Republic"), "ACC-007003", "BC-007003", "AVAILABLE", "Shelf-LIT-01", 1)
        ]

        for bib_id, acc, bc, status, shelf, tagged in items_data:
            if bib_id:
                conn.execute("""
                    INSERT OR IGNORE INTO items (biblio_id, accession_number, barcode, status, shelf_location, is_tagged)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bib_id, acc, bc, status, shelf, tagged))

        # Retrieve items map
        cursor.execute("SELECT id, accession_number FROM items")
        item_map = {row["accession_number"]: row["id"] for row in cursor.fetchall()}

        # 5. Seed RFID Tags
        # EAS Status: 0 = Armed (In-Library), 1 = Disarmed (Checked out)
        tags_data = [
            # Baseline test fixtures
            (item_map.get("ACC-001001"), "E00401509988A101", 0, "ISO15693_DATA_MODEL", -45.5),
            (item_map.get("ACC-001002"), "E00401509988A102", 0, "ISO15693_DATA_MODEL", -48.0),
            (item_map.get("ACC-002001"), "E00401509988A201", 0, "ISO15693_DATA_MODEL", -42.1), # Reference item
            (item_map.get("ACC-003001"), "E00401509988A301", 0, "ISO15693_DATA_MODEL", -50.2),
            (item_map.get("ACC-004001"), "E00401509988A401", 0, "ISO15693_DATA_MODEL", -46.7),

            # Additional shelf stock tags
            (item_map.get("ACC-001003"), "E00401509988A103", 0, "ISO15693_DATA_MODEL", -44.2),
            (item_map.get("ACC-001004"), "E00401509988A104", 0, "ISO15693_DATA_MODEL", -47.1),
            (item_map.get("ACC-001005"), "E00401509988A105", 0, "ISO15693_DATA_MODEL", -43.8),

            (item_map.get("ACC-002002"), "E00401509988A202", 0, "ISO15693_DATA_MODEL", -41.5),
            (item_map.get("ACC-002003"), "E00401509988A203", 0, "ISO15693_DATA_MODEL", -42.9),

            (item_map.get("ACC-003002"), "E00401509988A302", 0, "ISO15693_DATA_MODEL", -49.0),
            (item_map.get("ACC-003003"), "E00401509988A303", 0, "ISO15693_DATA_MODEL", -48.5),
            (item_map.get("ACC-003004"), "E00401509988A304", 0, "ISO15693_DATA_MODEL", -46.0),

            (item_map.get("ACC-004002"), "E00401509988A402", 0, "ISO15693_DATA_MODEL", -45.1),
            (item_map.get("ACC-004003"), "E00401509988A403", 0, "ISO15693_DATA_MODEL", -47.8),
            (item_map.get("ACC-004004"), "E00401509988A404", 0, "ISO15693_DATA_MODEL", -44.9),

            (item_map.get("ACC-005002"), "E00401509988A502", 0, "ISO15693_DATA_MODEL", -43.2),
            (item_map.get("ACC-005003"), "E00401509988A503", 0, "ISO15693_DATA_MODEL", -45.7),

            (item_map.get("ACC-006001"), "E00401509988A601", 0, "ISO15693_DATA_MODEL", -48.2),
            (item_map.get("ACC-006002"), "E00401509988A602", 0, "ISO15693_DATA_MODEL", -46.3),
            (item_map.get("ACC-006003"), "E00401509988A603", 0, "ISO15693_DATA_MODEL", -44.5),

            (item_map.get("ACC-007001"), "E00401509988A701", 0, "ISO15693_DATA_MODEL", -47.4),
            (item_map.get("ACC-007002"), "E00401509988A702", 0, "ISO15693_DATA_MODEL", -45.8),
            (item_map.get("ACC-007003"), "E00401509988A703", 0, "ISO15693_DATA_MODEL", -46.1)
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
