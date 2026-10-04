"""
Reporting and Analytics API routes for AISYS.
Provides dashboard metrics and filterable operational reports.
Fulfills FR 08, AC 08.
"""
from typing import Optional
from fastapi import APIRouter, Query
from src.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["Reports & Dashboards"])

@router.get("/dashboard")
def get_dashboard():
    """
    Returns executive dashboard metrics (catalog, patrons, circulation, gate security).
    Fulfills FR 08, AC 08.
    """
    return ReportService.get_dashboard_summary()

@router.get("/tagged-items")
def get_tagged_items_report(
    shelf: Optional[str] = Query(None),
    eas_status: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Filterable report for RFID tagged items.
    """
    return ReportService.get_tagged_items_report(
        shelf_location=shelf,
        eas_status=eas_status,
        limit=limit,
        offset=offset
    )

@router.get("/circulation")
def get_circulation_report(
    tx_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Filterable report for circulation transactions.
    """
    return ReportService.get_circulation_report(
        transaction_type=tx_type,
        status=status,
        limit=limit,
        offset=offset
    )

@router.get("/operators")
def get_operators_report():
    """
    Activity and productivity metrics for staff operators.
    """
    return ReportService.get_operator_activity_report()

@router.get("/gate-events")
def get_gate_events_report(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Filterable security gate log report.
    """
    return ReportService.get_gate_events_report(limit=limit, offset=offset)
