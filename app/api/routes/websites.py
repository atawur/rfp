from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.website import (
    Website as WebsiteSchema,
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteTestExtractionRequest,
)
from app.services.website_service import website_service

router = APIRouter()


@router.get("/", response_model=List[WebsiteSchema])
def read_websites(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return website_service.get_websites(db, skip=skip, limit=limit)


@router.get("/crawl-status")
def get_crawl_status(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get IDs of websites that currently have an active/running crawl.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.crawl_run import CrawlRun

    # Check for crawls marked running within the last 15 minutes
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    running_runs = (
        db.query(CrawlRun)
        .filter(CrawlRun.status == "running", CrawlRun.created_at >= cutoff)
        .all()
    )
    running_ids = list(set(run.website_id for run in running_runs))
    return {
        "running_website_ids": running_ids,
        "is_crawling_any": len(running_ids) > 0,
    }


@router.post("/", response_model=WebsiteSchema)
def create_website(
    *,
    db: Session = Depends(deps.get_db),
    website_in: WebsiteCreate,
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return website_service.create_website(db, website_in=website_in)


@router.get("/{website_id}", response_model=WebsiteSchema)
def read_website(
    website_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return website_service.get_website_by_id(db, website_id=website_id)


@router.put("/{website_id}", response_model=WebsiteSchema)
def update_website(
    website_id: int,
    website_in: WebsiteUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return website_service.update_website(
        db, website_id=website_id, website_in=website_in
    )


@router.post("/{website_id}/crawl")
def trigger_website_crawl(
    website_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    return website_service.trigger_website_crawl(db, website_id=website_id)


@router.post("/crawl-all")
def trigger_all_active_websites_crawl(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually trigger a crawl for all active websites.
    """
    return website_service.trigger_all_active_websites_crawl(db)


@router.post("/test-extraction")
def test_extraction_synchronously(
    request: WebsiteTestExtractionRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Synchronously fetch and extract data from a URL using the Pure OpenAI Agent.
    This is useful for manually testing the extraction pipeline without waiting for the scheduler.
    """
    return website_service.test_extraction(db, url=request.url)
