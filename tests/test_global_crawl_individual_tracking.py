import pytest
import uuid
from unittest.mock import patch, MagicMock
import app.db.base
from app.db.session import SessionLocal
from app.models.website import Website
from app.models.crawl_run import CrawlRun
from app.services.website_service import website_service
from app.workers.extraction_worker.tasks import extract_rfp_from_url


def test_global_crawl_creates_individual_crawl_runs_and_tracks_them():
    db = SessionLocal()
    slug = uuid.uuid4().hex[:8]

    # Create two test active websites and one inactive website
    website_1 = Website(
        name=f"Active Site 1 {slug}",
        base_url=f"https://site1-{slug}.example.com",
        start_url=f"https://site1-{slug}.example.com/rfps",
        status="active",
    )
    website_2 = Website(
        name=f"Active Site 2 {slug}",
        base_url=f"https://site2-{slug}.example.com",
        start_url=f"https://site2-{slug}.example.com/rfps",
        status="active",
    )
    website_inactive = Website(
        name=f"Inactive Site {slug}",
        base_url=f"https://inactive-{slug}.example.com",
        start_url=f"https://inactive-{slug}.example.com/rfps",
        status="inactive",
    )
    db.add_all([website_1, website_2, website_inactive])
    db.commit()
    db.refresh(website_1)
    db.refresh(website_2)
    db.refresh(website_inactive)

    try:
        # Mock scheduler to avoid running actual network crawling in this test
        mock_job = MagicMock()
        mock_job.id = "mock-job-id"
        with patch("app.core.scheduler.scheduler.add_job", return_value=mock_job) as mock_add_job:
            res = website_service.trigger_all_active_websites_crawl(db)

            # Check return structure
            assert "website_ids" in res
            assert website_1.id in res["website_ids"]
            assert website_2.id in res["website_ids"]
            assert website_inactive.id not in res["website_ids"]

            # Verify CrawlRun records were created with status="running"
            run_1 = (
                db.query(CrawlRun)
                .filter(CrawlRun.website_id == website_1.id, CrawlRun.status == "running")
                .first()
            )
            run_2 = (
                db.query(CrawlRun)
                .filter(CrawlRun.website_id == website_2.id, CrawlRun.status == "running")
                .first()
            )

            assert run_1 is not None
            assert run_2 is not None

            # Verify add_job was called for both active websites with their respective crawl_run.id
            assert mock_add_job.call_count >= 2
            called_args = [call.kwargs.get("args") or call.args[1] for call in mock_add_job.call_args_list]
            assert any(args[0] == website_1.id and args[1] == run_1.id for args in called_args)
            assert any(args[0] == website_2.id and args[1] == run_2.id for args in called_args)

            # Test duplicate protection: calling trigger_all_active_websites_crawl again
            # while runs are still active should not create duplicate runs
            mock_add_job.reset_mock()
            res_second = website_service.trigger_all_active_websites_crawl(db)
            assert website_1.id in res_second["website_ids"]
            assert website_2.id in res_second["website_ids"]
            # No new add_job calls should be made because they are already actively running
            assert mock_add_job.call_count == 0

    finally:
        # Cleanup
        db.query(CrawlRun).filter(
            CrawlRun.website_id.in_([website_1.id, website_2.id, website_inactive.id])
        ).delete(synchronize_session=False)
        db.delete(website_1)
        db.delete(website_2)
        db.delete(website_inactive)
        db.commit()
        db.close()


def test_extract_rfp_from_url_updates_existing_crawl_run():
    db = SessionLocal()
    slug = uuid.uuid4().hex[:8]

    website = Website(
        name=f"Site Extract Test {slug}",
        base_url=f"https://extract-{slug}.example.com",
        start_url=f"https://extract-{slug}.example.com/rfps",
        status="active",
    )
    db.add(website)
    db.commit()
    db.refresh(website)

    crawl_run = CrawlRun(website_id=website.id, status="running")
    db.add(crawl_run)
    db.commit()
    db.refresh(crawl_run)

    try:
        with patch("app.services.rfp_service.rfp_service.extract_and_process_url", return_value=[{"status": "inserted"}]):
            res = extract_rfp_from_url(
                url=website.start_url,
                website_id=website.id,
                notify=False,
                crawl_run_id=crawl_run.id,
            )

        # Refresh crawl_run from db
        db.refresh(crawl_run)
        assert crawl_run.status == "completed"
        assert crawl_run.completed_at is not None
        assert crawl_run.metrics == {
            "candidates_found": 1,
            "new_rfps": 1,
            "updated_rfps": 0,
            "ignored": 0,
        }

    finally:
        db.query(CrawlRun).filter(CrawlRun.website_id == website.id).delete(synchronize_session=False)
        db.delete(website)
        db.commit()
        db.close()
