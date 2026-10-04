"""
Test suite for Core ILMS, Search, and Reporting functions.
Verifies FR 01, FR 02, FR 08.
"""
from fastapi.testclient import TestClient
from src.services.cataloguing_service import CataloguingService, BibliographicCreate, ItemCreate
from src.services.search_service import SearchService
from src.services.report_service import ReportService

def test_create_bibliographic_and_item():
    bib_data = BibliographicCreate(
        title="Modern Operating Systems",
        author="Andrew S. Tanenbaum",
        isbn="9780133591620",
        publisher="Pearson",
        publication_year=2015,
        edition="4th Edition",
        call_number="005.43 TAN",
        subject="Computer Science, OS",
        material_type="BOOK",
        virtual_shelf="Shelf-A-01",
        is_reference=False
    )
    bib_id = CataloguingService.create_bibliographic_record(bib_data)
    assert bib_id > 0

    item_data = ItemCreate(
        biblio_id=bib_id,
        accession_number="ACC-TEST-001",
        barcode="BC-TEST-001",
        shelf_location="Shelf-A-01"
    )
    item_id = CataloguingService.create_item(item_data)
    assert item_id > 0

    # Query item
    item = CataloguingService.get_item_by_accession("ACC-TEST-001")
    assert item is not None
    assert item["title"] == "Modern Operating Systems"
    assert item["status"] == "AVAILABLE"

def test_fts5_fulltext_search():
    # Search for term indexed in FTS5
    results = SearchService.search("Algorithms")
    assert results["total"] >= 1
    assert any("Algorithms" in r["title"] for r in results["results"])

def test_spine_label_generation():
    item = CataloguingService.get_item_by_accession("ACC-001001")
    assert item is not None

    label = CataloguingService.generate_spine_label(item["id"])
    assert label["item_id"] == item["id"]
    assert "svg" in label["svg_label"].lower()
    assert item["barcode"] in label["svg_label"]

def test_virtual_bookshelf():
    shelf_items = SearchService.get_virtual_bookshelf("Shelf-A-01")
    assert len(shelf_items) >= 1

def test_dashboard_and_filterable_reports(client: TestClient):
    response = client.get("/api/reports/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "catalog" in data
    assert "patrons" in data
    assert "circulation" in data
    assert "security" in data
    assert data["catalog"]["total_titles"] > 0
