import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from app.db.session import SessionLocal
from app.workers.crawl_worker.tasks import crawl_website

logger = logging.getLogger(__name__)

jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'
)


def crawl_all_active_websites():
    """
    Scheduled background job:
    Fetches all active websites and executes individual crawls with CrawlRun tracking.
    """
    logger.info("Running scheduled job: crawl_all_active_websites")
    db = SessionLocal()
    try:
        from app.services.website_service import website_service
        return website_service.trigger_all_active_websites_crawl(db)
    except Exception as e:
        logger.error(f"Error in scheduled job crawl_all_active_websites: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
        }
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        logger.info("Starting APScheduler...")
        # Schedule the job to run every 12 hours
        #scheduler.add_job(crawl_all_active_websites, trigger='cron', hour='0,12')
        scheduler.add_job(crawl_all_active_websites,trigger='cron',hour=14,minute=25,timezone='Asia/Dhaka'  # or your preferred timezone
)

        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        logger.info("Shutting down APScheduler...")
        scheduler.shutdown(wait=True)
