import logging
from typing import Optional

from app.db.session import SessionLocal
from app.models.crawl_run import CrawlRun

logger = logging.getLogger(__name__)


def extract_rfp_from_url(
    url: str,
    website_id: Optional[int] = None,
    notify: bool = True,
    crawl_run_id: Optional[int] = None,
) -> str:
    """
    Unified extraction background task:
    Fetches, extracts with AI agent, validates, deduplicates, persists,
    records CrawlRun metrics if website_id is provided, and asynchronously alerts eligible users.
    """
    from datetime import datetime, timezone
    from app.services.rfp_service import rfp_service

    logger.info(f"Starting extraction task for URL: {url} (website_id={website_id}, crawl_run_id={crawl_run_id})")
    db = SessionLocal()
    crawl_run = None

    try:
        # 1. If crawl_run_id is provided, reuse existing CrawlRun; otherwise create if website_id present
        if crawl_run_id:
            crawl_run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
        elif website_id:
            crawl_run = CrawlRun(website_id=website_id, status="running")  # type: ignore
            db.add(crawl_run)
            db.commit()
            db.refresh(crawl_run)

        # 2. Execute extraction pipeline
        results = rfp_service.extract_and_process_url(
            db=db,
            url=url,
            website_id=website_id,
            notify=notify,
        )

        # 3. Calculate metrics
        candidates_found = len(results)
        inserted_count = sum(1 for r in results if r.get("status") == "inserted")
        updated_count = sum(1 for r in results if r.get("status") == "updated")
        ignored_count = sum(1 for r in results if r.get("status") == "ignored")

        # 4. Finalize CrawlRun if present
        if crawl_run:
            crawl_run.status = "completed"  # type: ignore
            crawl_run.completed_at = datetime.now(timezone.utc)  # type: ignore
            crawl_run.metrics = {  # type: ignore
                "candidates_found": candidates_found,
                "new_rfps": inserted_count,
                "updated_rfps": updated_count,
                "ignored": ignored_count,
            }
            db.commit()

        # Check if all active website crawls have finished; if so, dispatch consolidated email
        try:
            from app.services.notification_service import has_active_crawls, flush_pending_notifications
            if not has_active_crawls(db):
                flush_pending_notifications(db)
        except Exception as flush_err:
            logger.warning(f"Failed to flush pending notifications on crawl completion: {flush_err}")

        summary_msg = (
            f"Success: Processed {candidates_found} items for {url} "
            f"(inserted: {inserted_count}, updated: {updated_count}, ignored: {ignored_count})"
        )
        logger.info(summary_msg)
        return summary_msg

    except Exception as e:
        logger.error(f"Extraction failed for {url}: {str(e)}")
        if crawl_run:
            try:
                crawl_run.status = "failed"  # type: ignore
                crawl_run.completed_at = datetime.now(timezone.utc)  # type: ignore
                crawl_run.error = str(e)  # type: ignore
                db.commit()
            except Exception as db_err:
                logger.error(f"Failed to record crawl failure status: {db_err}")

        # In case of failure, also check if this was the last active crawl
        try:
            from app.services.notification_service import has_active_crawls, flush_pending_notifications
            if not has_active_crawls(db):
                flush_pending_notifications(db)
        except Exception as flush_err:
            logger.warning(f"Failed to flush pending notifications on crawl failure: {flush_err}")

        return f"Failed: {str(e)}"
    finally:
        db.close()
