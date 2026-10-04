"""
Cataloguing and physical item management service for AISYS.
Handles bibliographic records, physical copies, serials, and spine/barcode label generation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.database import db_manager
from src.core.audit import AuditService
from src.core.logger import logger

class BibliographicCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    edition: Optional[str] = None
    call_number: str = Field(..., min_length=1)
    subject: Optional[str] = None
    material_type: str = "BOOK" # BOOK, REFERENCE, PERIODICAL, MEDIA, THESIS
    virtual_shelf: str = "Shelf-A-01"
    is_reference: bool = False
    source_system: str = "AISYS"

class ItemCreate(BaseModel):
    biblio_id: int
    accession_number: str = Field(..., min_length=1)
    barcode: str = Field(..., min_length=1)
    shelf_location: str = "Shelf-A-01"

class CataloguingService:
    @staticmethod
    def create_bibliographic_record(data: BibliographicCreate, user_id: Optional[int] = None) -> int:
        with db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bibliographic_records (
                    title, author, isbn, publisher, publication_year,
                    edition, call_number, subject, material_type,
                    virtual_shelf, is_reference, source_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.title.strip(),
                data.author.strip(),
                data.isbn.strip() if data.isbn else None,
                data.publisher.strip() if data.publisher else None,
                data.publication_year,
                data.edition.strip() if data.edition else None,
                data.call_number.strip(),
                data.subject.strip() if data.subject else None,
                data.material_type.upper(),
                data.virtual_shelf.strip(),
                1 if data.is_reference else 0,
                data.source_system
            ))
            biblio_id = cursor.lastrowid

        AuditService.log(
            action="CREATE_BIBLIO",
            entity="BIBLIOGRAPHIC_RECORD",
            entity_id=str(biblio_id),
            user_id=user_id,
            details={"title": data.title, "call_number": data.call_number, "is_reference": data.is_reference}
        )
        logger.info(f"Bibliographic record created: ID {biblio_id} - {data.title}")
        return biblio_id

    @staticmethod
    def get_bibliographic_record(biblio_id: int) -> Optional[Dict[str, Any]]:
        record = db_manager.execute_one(
            "SELECT * FROM bibliographic_records WHERE id = ?", (biblio_id,)
        )
        if not record:
            return None

        # Fetch associated physical items
        items = db_manager.execute_query("""
            SELECT i.*, r.tag_uid, r.eas_status, r.last_scanned_at
            FROM items i
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.biblio_id = ?
        """, (biblio_id,))
        record["items"] = items
        return record

    @staticmethod
    def create_item(data: ItemCreate, user_id: Optional[int] = None) -> int:
        # Verify biblio exists
        bib = db_manager.execute_one("SELECT id FROM bibliographic_records WHERE id = ?", (data.biblio_id,))
        if not bib:
            raise ValueError(f"Bibliographic record ID {data.biblio_id} not found.")

        # Check uniqueness of accession_number and barcode
        existing = db_manager.execute_one(
            "SELECT id FROM items WHERE accession_number = ? OR barcode = ?",
            (data.accession_number, data.barcode)
        )
        if existing:
            raise ValueError(f"Accession number '{data.accession_number}' or barcode '{data.barcode}' already exists.")

        item_id = db_manager.execute_mutation("""
            INSERT INTO items (biblio_id, accession_number, barcode, status, shelf_location, is_tagged)
            VALUES (?, ?, ?, 'AVAILABLE', ?, 0)
        """, (data.biblio_id, data.accession_number, data.barcode, data.shelf_location))

        AuditService.log(
            action="CREATE_ITEM",
            entity="ITEM",
            entity_id=str(item_id),
            user_id=user_id,
            details={"accession_number": data.accession_number, "barcode": data.barcode}
        )
        return item_id

    @staticmethod
    def get_item_by_accession(accession_number: str) -> Optional[Dict[str, Any]]:
        return db_manager.execute_one("""
            SELECT i.*, b.title, b.author, b.call_number, b.is_reference, b.material_type,
                   r.tag_uid, r.eas_status
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.accession_number = ?
        """, (accession_number,))

    @staticmethod
    def get_item_by_barcode(barcode: str) -> Optional[Dict[str, Any]]:
        return db_manager.execute_one("""
            SELECT i.*, b.title, b.author, b.call_number, b.is_reference, b.material_type,
                   r.tag_uid, r.eas_status
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            LEFT JOIN rfid_tags r ON i.id = r.item_id
            WHERE i.barcode = ?
        """, (barcode,))

    @staticmethod
    def generate_spine_label(item_id: int) -> Dict[str, Any]:
        """
        Generates spine and barcode label layout metadata and formatted SVG markup.
        Fulfills FR 01 barcode and spine-label workflows.
        """
        item = db_manager.execute_one("""
            SELECT i.id, i.accession_number, i.barcode, i.shelf_location,
                   b.title, b.author, b.call_number, b.material_type
            FROM items i
            JOIN bibliographic_records b ON i.biblio_id = b.id
            WHERE i.id = ?
        """, (item_id,))
        if not item:
            raise ValueError(f"Item ID {item_id} not found.")

        # Create structured spine label data
        call_parts = item["call_number"].split()
        prefix = call_parts[0] if len(call_parts) > 0 else item["call_number"]
        author_code = call_parts[1] if len(call_parts) > 1 else ""

        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150" viewBox="0 0 300 150">
  <rect width="298" height="148" x="1" y="1" fill="#fff" stroke="#333" stroke-width="2" rx="4"/>
  <rect width="90" height="148" x="1" y="1" fill="#f8fafc" stroke="#94a3b8" stroke-width="1"/>
  <!-- Spine Section -->
  <text x="45" y="25" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle" fill="#0f172a">{item['shelf_location']}</text>
  <text x="45" y="55" font-family="monospace" font-size="14" font-weight="bold" text-anchor="middle" fill="#1e293b">{prefix}</text>
  <text x="45" y="80" font-family="monospace" font-size="14" font-weight="bold" text-anchor="middle" fill="#1e293b">{author_code}</text>
  <text x="45" y="125" font-family="monospace" font-size="10" text-anchor="middle" fill="#64748b">{item['accession_number']}</text>
  <!-- Barcode / Book Label Section -->
  <text x="105" y="25" font-family="sans-serif" font-size="11" font-weight="bold" fill="#0f172a">AISYS ACADEMIC LIBRARY</text>
  <text x="105" y="45" font-family="sans-serif" font-size="10" fill="#334155">{item['title'][:26]}</text>
  <text x="105" y="60" font-family="sans-serif" font-size="9" fill="#64748b">By: {item['author'][:28]}</text>
  <!-- Emulated Barcode lines -->
  <rect x="105" y="75" width="3" height="35" fill="#000"/>
  <rect x="111" y="75" width="2" height="35" fill="#000"/>
  <rect x="116" y="75" width="4" height="35" fill="#000"/>
  <rect x="123" y="75" width="2" height="35" fill="#000"/>
  <rect x="128" y="75" width="5" height="35" fill="#000"/>
  <rect x="136" y="75" width="2" height="35" fill="#000"/>
  <rect x="141" y="75" width="3" height="35" fill="#000"/>
  <rect x="147" y="75" width="6" height="35" fill="#000"/>
  <rect x="156" y="75" width="2" height="35" fill="#000"/>
  <rect x="161" y="75" width="4" height="35" fill="#000"/>
  <rect x="168" y="75" width="3" height="35" fill="#000"/>
  <rect x="174" y="75" width="2" height="35" fill="#000"/>
  <rect x="179" y="75" width="5" height="35" fill="#000"/>
  <rect x="187" y="75" width="2" height="35" fill="#000"/>
  <rect x="192" y="75" width="4" height="35" fill="#000"/>
  <rect x="199" y="75" width="3" height="35" fill="#000"/>
  <rect x="205" y="75" width="2" height="35" fill="#000"/>
  <rect x="210" y="75" width="4" height="35" fill="#000"/>
  <rect x="217" y="75" width="2" height="35" fill="#000"/>
  <rect x="222" y="75" width="5" height="35" fill="#000"/>
  <rect x="230" y="75" width="3" height="35" fill="#000"/>
  <text x="168" y="125" font-family="monospace" font-size="11" text-anchor="middle" fill="#0f172a">{item['barcode']}</text>
</svg>"""

        return {
            "item_id": item["id"],
            "accession_number": item["accession_number"],
            "barcode": item["barcode"],
            "title": item["title"],
            "call_number": item["call_number"],
            "shelf_location": item["shelf_location"],
            "svg_label": svg_content
        }
