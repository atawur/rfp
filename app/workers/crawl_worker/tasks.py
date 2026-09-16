import logging

from app.db.session import SessionLocal
from app.models.website import Website
from app.models.crawl_run import CrawlRun

logger = logging.getLogger(__name__)


from typing import Optional

def crawl_website(website_id: int, crawl_run_id: Optional[int] = None) -> str:
    """
    Crawls an active website by delegating directly to the unified extract_rfp_from_url task.
    """
    from app.workers.extraction_worker.tasks import extract_rfp_from_url

    logger.info(f"Starting crawl task for website_id: {website_id} (crawl_run_id={crawl_run_id})")
    db = SessionLocal()

    try:
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            logger.error(f"Website with id {website_id} not found")
            if crawl_run_id:
                crawl_run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
                if crawl_run:
                    from datetime import datetime, timezone
                    crawl_run.status = "failed"
                    crawl_run.completed_at = datetime.now(timezone.utc)
                    crawl_run.error = f"Website with id {website_id} not found"
                    db.commit()
            return f"Failed: Website with id {website_id} not found"

        if str(getattr(website, "status", "")) != "active":
            logger.info(f"Website {website.id} ({website.name}) is inactive (status='{getattr(website, 'status', None)}'). Skipping.")
            if crawl_run_id:
                crawl_run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
                if crawl_run:
                    from datetime import datetime, timezone
                    crawl_run.status = "completed"
                    crawl_run.completed_at = datetime.now(timezone.utc)
                    crawl_run.metrics = {"skipped": "inactive"}
                    db.commit()
            return f"Skipped: Website {website_id} is inactive"

        target_url = str(website.start_url or website.base_url).strip()
        return extract_rfp_from_url(
            url=target_url,
            website_id=website.id,
            notify=True,
            crawl_run_id=crawl_run_id,
        )

    finally:
        db.close()


