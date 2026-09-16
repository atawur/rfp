from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.website import Website
from app.repositories.website_repo import website_repo
from app.schemas.website import WebsiteCreate, WebsiteUpdate
from app.services.rfp_service import rfp_service
from app.workers.crawl_worker.tasks import crawl_website
import app.core.scheduler


class WebsiteService:
    def get_websites(self, db: Session, skip: int = 0, limit: int = 100) -> List[Website]:
        return website_repo.get_multi(db, skip=skip, limit=limit)

    def get_website_by_id(self, db: Session, website_id: int) -> Website:
        website = website_repo.get(db, id=website_id)
        if not website:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Website not found",
            )
        return website

    def create_website(self, db: Session, website_in: WebsiteCreate) -> Website:
        return website_repo.create(db, obj_in=website_in)

    def update_website(self, db: Session, website_id: int, website_in: WebsiteUpdate) -> Website:
        website = self.get_website_by_id(db, website_id=website_id)
        return website_repo.update(db, db_obj=website, obj_in=website_in)

    def get_active_websites(self, db: Session) -> List[Website]:
        return website_repo.get_active_websites(db)

    def trigger_website_crawl(self, db: Session, website_id: int) -> Dict[str, Any]:
        # Ensure the website exists before scheduling
        website = self.get_website_by_id(db, website_id=website_id)
        from datetime import datetime, timezone, timedelta
        from app.models.crawl_run import CrawlRun

        # Check if already actively running in the last 15 minutes
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        existing_run = (
            db.query(CrawlRun)
            .filter(
                CrawlRun.website_id == website_id,
                CrawlRun.status == "running",
                CrawlRun.created_at >= cutoff,
            )
            .first()
        )
        if existing_run:
            return {
                "message": f"Crawl already in progress for '{website.name}'",
                "crawl_run_id": existing_run.id,
                "website_id": website_id,
            }

        crawl_run = CrawlRun(website_id=website_id, status="running")
        db.add(crawl_run)
        db.commit()
        db.refresh(crawl_run)

        job = app.core.scheduler.scheduler.add_job(
            crawl_website,
            args=[website_id, crawl_run.id],
        )
        return {
            "message": f"Crawl task started for '{website.name}'",
            "job_id": job.id,
            "crawl_run_id": crawl_run.id,
            "website_id": website_id,
        }

    def trigger_all_active_websites_crawl(self, db: Session) -> Dict[str, Any]:
        active_websites = self.get_active_websites(db)
        if not active_websites:
            return {
                "message": "No active websites found to crawl",
                "website_ids": [],
            }

        from datetime import datetime, timezone, timedelta
        from app.models.crawl_run import CrawlRun

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        triggered_ids = []

        for website in active_websites:
            # Check if this website is already actively crawling
            existing_run = (
                db.query(CrawlRun)
                .filter(
                    CrawlRun.website_id == website.id,
                    CrawlRun.status == "running",
                    CrawlRun.created_at >= cutoff,
                )
                .first()
            )
            if existing_run:
                triggered_ids.append(website.id)
                continue

            crawl_run = CrawlRun(website_id=website.id, status="running")
            db.add(crawl_run)
            db.commit()
            db.refresh(crawl_run)

            app.core.scheduler.scheduler.add_job(
                crawl_website,
                args=[website.id, crawl_run.id],
            )
            triggered_ids.append(website.id)

        return {
            "message": f"Initiated crawl for {len(triggered_ids)} active website(s)",
            "website_ids": triggered_ids,
        }

    def test_extraction(self, db: Session, url: str) -> Dict[str, Any]:
        results = rfp_service.extract_and_process_url(db, url=url)
        return {
            "message": "Extraction and processing successful",
            "results": results,
        }


website_service = WebsiteService()
