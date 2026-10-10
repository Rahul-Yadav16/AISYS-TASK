"""
Cataloguing and discovery API routes for AISYS.
Handles full-text search, bibliographic records, items, spine labels, and virtual bookshelf.
Fulfills FR 01, FR 02.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from src.services.cataloguing_service import CataloguingService, BibliographicCreate, ItemCreate
from src.services.search_service import SearchService

router = APIRouter(prefix="/api/catalog", tags=["Cataloguing & Search"])

class NetCatalogRequest(BaseModel):
    query: str

@router.get("/search")
def search_catalog(
    q: str = Query("", description="Full text search query"),
    material_type: Optional[str] = Query(None),
    is_reference: Optional[bool] = Query(None),
    shelf: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Full-text search powered by SQLite FTS5 engine. Fulfills FR 02.
    """
    return SearchService.search(
        query=q,
        material_type=material_type,
        is_reference=is_reference,
        shelf=shelf,
        limit=limit,
        offset=offset
    )

@router.post("/bibliographic")
def create_bibliographic_record(data: BibliographicCreate):
    try:
        bib_id = CataloguingService.create_bibliographic_record(data)
        return {"success": True, "id": bib_id, "title": data.title}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bibliographic/{biblio_id}")
def get_bibliographic_record(biblio_id: int):
    record = CataloguingService.get_bibliographic_record(biblio_id)
    if not record:
        raise HTTPException(status_code=404, detail="Bibliographic record not found.")
    return record

@router.post("/items")
def create_item(data: ItemCreate):
    try:
        item_id = CataloguingService.create_item(data)
        return {"success": True, "item_id": item_id, "accession_number": data.accession_number}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/items/accession/{accession_number}")
def get_item_by_accession(accession_number: str):
    item = CataloguingService.get_item_by_accession(accession_number)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item

@router.get("/items/barcode/{barcode}")
def get_item_by_barcode(barcode: str):
    item = CataloguingService.get_item_by_barcode(barcode)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item

@router.get("/spine-label/{item_id}")
def get_spine_label(item_id: int):
    """
    Generates printable spine and barcode label SVG. Fulfills FR 01.
    """
    try:
        return CataloguingService.generate_spine_label(item_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/bookshelf")
def get_virtual_bookshelf(shelf_id: Optional[str] = Query(None)):
    """
    Virtual bookshelf arrangement. Fulfills FR 02.
    """
    return SearchService.get_virtual_bookshelf(shelf_id)

@router.get("/shelves")
def get_all_shelves():
    """
    Retrieves summary list of all virtual shelves with book counts. Fulfills FR 02.
    """
    return SearchService.get_all_shelves()


@router.post("/net-catalogue")
def net_catalogue_lookup(req: NetCatalogRequest):
    """
    Net cataloguing lookup utility. Fulfills FR 02.
    """
    return SearchService.net_catalogue_lookup(req.query)
