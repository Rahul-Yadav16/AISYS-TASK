"""
Search and discovery service for AISYS.
Integrates SQLite FTS5 full-text indexing, relevance scoring, and virtual bookshelf organization.
"""
from typing import Any, Dict, List, Optional
from src.core.database import db_manager

class SearchService:
    @staticmethod
    def search(
        query: str,
        material_type: Optional[str] = None,
        is_reference: Optional[bool] = None,
        shelf: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Executes full-text search against biblio_fts virtual table, joined with physical item status.
        """
        params: List[Any] = []
        conditions: List[str] = []

        q_clean = query.strip()
        if q_clean:
            # FTS match query
            # Escape problematic FTS chars
            fts_query = '"' + q_clean.replace('"', '""') + '"*'
            where_fts = "b.id IN (SELECT rowid FROM biblio_fts WHERE biblio_fts MATCH ?)"
            conditions.append(where_fts)
            params.append(fts_query)

        if material_type:
            conditions.append("b.material_type = ?")
            params.append(material_type.upper())

        if is_reference is not None:
            conditions.append("b.is_reference = ?")
            params.append(1 if is_reference else 0)

        if shelf:
            conditions.append("b.virtual_shelf LIKE ?")
            params.append(f"%{shelf}%")

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_sql = f"SELECT COUNT(*) as total FROM bibliographic_records b {where_clause}"
        total_row = db_manager.execute_one(count_sql, tuple(params))
        total_count = total_row["total"] if total_row else 0

        # Retrieve bibliographic records
        sql = f"""
            SELECT b.*,
                   (SELECT COUNT(*) FROM items WHERE biblio_id = b.id) as total_copies,
                   (SELECT COUNT(*) FROM items WHERE biblio_id = b.id AND status = 'AVAILABLE') as available_copies,
                   (SELECT COUNT(*) FROM items i JOIN rfid_tags r ON i.id = r.item_id WHERE i.biblio_id = b.id) as tagged_copies
            FROM bibliographic_records b
            {where_clause}
            ORDER BY b.id DESC
            LIMIT ? OFFSET ?
        """
        records = db_manager.execute_query(sql, tuple(params + [limit, offset]))

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "query": query,
            "results": records
        }

    @staticmethod
    def get_virtual_bookshelf(shelf_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves visual bookshelf representation ordered by call number.
        Fulfills FR 02 virtual bookshelf.
        """
        base_cols = """
            b.id, b.title, b.author, b.call_number, b.material_type, b.virtual_shelf,
            b.is_reference, b.publisher, b.publication_year, b.isbn, b.subject,
            i.id as item_id, i.accession_number, i.barcode, i.status, i.shelf_location,
            r.tag_uid, r.eas_status, r.memory_format
        """
        if shelf_id and shelf_id.strip() and shelf_id.upper() != "ALL":
            sql = f"""
                SELECT {base_cols}
                FROM bibliographic_records b
                JOIN items i ON b.id = i.biblio_id
                LEFT JOIN rfid_tags r ON i.id = r.item_id
                WHERE b.virtual_shelf = ?
                ORDER BY b.call_number ASC, i.accession_number ASC
            """
            return db_manager.execute_query(sql, (shelf_id.strip(),))
        else:
            sql = f"""
                SELECT {base_cols}
                FROM bibliographic_records b
                JOIN items i ON b.id = i.biblio_id
                LEFT JOIN rfid_tags r ON i.id = r.item_id
                ORDER BY b.virtual_shelf ASC, b.call_number ASC, i.accession_number ASC
                LIMIT 250
            """
            return db_manager.execute_query(sql)

    @staticmethod
    def get_all_shelves() -> List[Dict[str, Any]]:
        """
        Retrieves list of distinct virtual shelves with book counts and availability stats.
        Fulfills FR 02.
        """
        sql = """
            SELECT b.virtual_shelf as shelf_id,
                   COUNT(i.id) as item_count,
                   SUM(CASE WHEN i.status = 'AVAILABLE' THEN 1 ELSE 0 END) as available_count,
                   SUM(CASE WHEN b.is_reference = 1 THEN 1 ELSE 0 END) as reference_count
            FROM bibliographic_records b
            JOIN items i ON b.id = i.biblio_id
            GROUP BY b.virtual_shelf
            ORDER BY b.virtual_shelf ASC
        """
        return db_manager.execute_query(sql)

    @staticmethod
    def net_catalogue_lookup(isbn_or_title: str) -> Dict[str, Any]:
        """
        Net cataloguing mock utility simulating external MARC/Z39.50/Dublin Core retrieval.
        Fulfills FR 02 net cataloguing.
        """
        clean_key = isbn_or_title.strip()
        # Mock networked bibliographic metadata repository
        mock_database = {
            "9780132350884": {
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "publisher": "Prentice Hall",
                "publication_year": 2008,
                "call_number": "005.1 MAR",
                "subject": "Computer Science, Software Engineering, Clean Code",
                "material_type": "BOOK",
                "virtual_shelf": "Shelf-A-04",
                "is_reference": False,
                "source_system": "NET_CATALOG"
            },
            "9780201633610": {
                "title": "Design Patterns: Elements of Reusable Object-Oriented Software",
                "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
                "isbn": "9780201633610",
                "publisher": "Addison-Wesley",
                "publication_year": 1994,
                "call_number": "005.12 GAM",
                "subject": "Design Patterns, Object-Oriented Programming",
                "material_type": "BOOK",
                "virtual_shelf": "Shelf-A-05",
                "is_reference": False,
                "source_system": "NET_CATALOG"
            }
        }

        if clean_key in mock_database:
            return {"found": True, "source": "Z39.50_MOCK_REPO", "record": mock_database[clean_key]}

        # Generic synthesized net catalogue response
        return {
            "found": True,
            "source": "Z39.50_SYNTHETIC_RESOLVER",
            "record": {
                "title": f"Network Retrieved Reference: {clean_key}",
                "author": "Academic Consortium Author",
                "isbn": clean_key if clean_key.isdigit() else "9780000000000",
                "publisher": "Academic Press Global",
                "publication_year": 2023,
                "call_number": "020.1 ACA",
                "subject": "Library and Information Sciences",
                "material_type": "BOOK",
                "virtual_shelf": "Shelf-B-02",
                "is_reference": False,
                "source_system": "NET_CATALOG"
            }
        }
