from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.rbac.security import RoleChecker
from app.schemas.rfp import (
    RFP as RFPSchema,
    RFPCreate,
    RFPImportURLRequest,
    RFPImportResponse,
    PaginatedRFPResponse,
)
from app.services.rfp_service import rfp_service

router = APIRouter()

allow_create_rfps = RoleChecker(["rfps.create"])


@router.get("/", response_model=PaginatedRFPResponse)
def read_rfps(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    skip: Optional[int] = Query(None, ge=0, description="Offset (legacy alternative to page)"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit (legacy alternative to size)"),
    website_id: Optional[int] = Query(None, description="Filter by website ID"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. software, hardware, unclassified)"),
    sub_category: Optional[str] = Query(None, description="Filter by subcategory"),
    procurement_type: Optional[str] = Query(None, description="Filter by procurement type"),
    status: Optional[str] = Query(None, description="Filter by RFP status"),
    search: Optional[str] = Query(None, description="Search query across title, organization, reference number, or category"),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    effective_page = page
    effective_size = size
    if limit is not None:
        effective_size = limit
    if skip is not None:
        effective_page = (skip // effective_size) + 1

    return rfp_service.get_paginated_rfps(
        db,
        page=effective_page,
        size=effective_size,
        website_id=website_id,
        category=category,
        sub_category=sub_category,
        procurement_type=procurement_type,
        status=status,
        search=search,
    )


@router.post("/", response_model=RFPSchema, dependencies=[Depends(allow_create_rfps)])
def create_rfp(
    *,
    db: Session = Depends(deps.get_db),
    rfp_in: RFPCreate,
) -> Any:
    return rfp_service.create_rfp(db, rfp_in=rfp_in)


@router.post("/import-url", response_model=RFPImportResponse, dependencies=[Depends(allow_create_rfps)])
def import_rfp_from_url(
    request: RFPImportURLRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mode A Ingestion: Synchronously fetch, extract, validate, and persist an RFP from a direct URL.
    """
    return rfp_service.import_from_url(db, url=request.url)


@router.get("/{rfp_id}", response_model=RFPSchema)
def read_rfp(
    rfp_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return rfp_service.get_rfp_by_id(db, rfp_id=rfp_id)


@router.post("/{rfp_id}/classify", response_model=RFPSchema)
def classify_rfp_endpoint(
    rfp_id: int,
    force: bool = False,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    On-demand or idempotent re-classification of an individual RFP opportunity.
    """
    from app.services.rfp_classification_service import rfp_classification_service
    classified = rfp_classification_service.classify_existing_rfp(db, rfp_id=rfp_id, force=force)
    if not classified:
        return rfp_service.get_rfp_by_id(db, rfp_id=rfp_id)
    return classified


@router.post("/reprocess-classification")
def reprocess_classification_batch(
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Batch re-attempts classification for unclassified, pending, or failed RFPs.
    """
    from app.services.rfp_classification_service import rfp_classification_service
    return rfp_classification_service.classify_pending_or_failed_rfps(db, limit=limit)
