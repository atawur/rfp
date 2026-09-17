import pytest
import uuid
from unittest.mock import patch, MagicMock
import app.db.base
from app.db.session import SessionLocal
from app.models.website import Website
from app.models.notification_receiver import NotificationReceiver
from app.models.notification import Notification
from app.models.rfp import RFP
from app.models.crawl_run import CrawlRun
from app.services.notification_service import (
    evaluate_and_notify_users_batch,
    flush_pending_notifications,
    has_active_crawls,
)


def test_multi_website_consolidated_single_email():
    db = SessionLocal()
    slug = uuid.uuid4().hex[:8]

    # Create Receiver
    receiver = NotificationReceiver(
        name=f"Consolidated Receiver {slug}",
        email=f"consolidated-{slug}@example.com",
        status="active",
    )
    db.add(receiver)
    db.commit()
    db.refresh(receiver)

    # Create Website A and Website B
    website_a = Website(
        name=f"Alpha Bank {slug}",
        base_url=f"https://alpha-{slug}.example.com",
        start_url=f"https://alpha-{slug}.example.com/rfps",
        notify_all_receivers=True,
        status="active",
    )
    website_b = Website(
        name=f"Beta Bank {slug}",
        base_url=f"https://beta-{slug}.example.com",
        start_url=f"https://beta-{slug}.example.com/rfps",
        notify_all_receivers=True,
        status="active",
    )
    db.add_all([website_a, website_b])
    db.commit()
    db.refresh(website_a)
    db.refresh(website_b)

    # Create RFPs for Website A and Website B
    rfp_a1 = RFP(
        title=f"Core Banking Upgrade {slug}",
        website_id=website_a.id,
        source_url=f"https://alpha-{slug}.example.com/rfp/1",
        status="NEW",
        primary_category="software",
    )
    rfp_a2 = RFP(
        title=f"ATM Hardware Supply {slug}",
        website_id=website_a.id,
        source_url=f"https://alpha-{slug}.example.com/rfp/2",
        status="NEW",
        primary_category="hardware",
    )
    rfp_b1 = RFP(
        title=f"Cloud Infrastructure Migration {slug}",
        website_id=website_b.id,
        source_url=f"https://beta-{slug}.example.com/rfp/10",
        status="NEW",
        primary_category="infrastructure",
    )
    db.add_all([rfp_a1, rfp_a2, rfp_b1])
    db.commit()
    db.refresh(rfp_a1)
    db.refresh(rfp_a2)
    db.refresh(rfp_b1)

    # Simulate an active crawl run for Website B while Website A finishes
    crawl_run_b = CrawlRun(website_id=website_b.id, status="running")
    db.add(crawl_run_b)
    db.commit()
    db.refresh(crawl_run_b)

    try:
        mock_send_email = MagicMock()
        with patch("app.workers.email_worker.tasks.send_batch_rfp_email", mock_send_email), \
             patch.object(type(app.core.scheduler.scheduler), "running", new=property(lambda self: True)), \
             patch("app.core.scheduler.scheduler.add_job") as mock_scheduler_add:

            # 1. Website A finishes and discovers rfp_a1 and rfp_a2
            notifs_a = evaluate_and_notify_users_batch(db, [rfp_a1, rfp_a2])
            receiver_notifs_a = [n for n in notifs_a if n.receiver_id == receiver.id]
            assert len(receiver_notifs_a) == 2
            # Since crawl_run_b is still 'running', notifications should remain PENDING and NO email dispatched yet!
            assert mock_send_email.call_count == 0
            assert mock_scheduler_add.call_count == 1  # only fallback scheduled

            # 2. Website B finishes and discovers rfp_b1
            notifs_b = evaluate_and_notify_users_batch(db, [rfp_b1])
            receiver_notifs_b = [n for n in notifs_b if n.receiver_id == receiver.id]
            assert len(receiver_notifs_b) == 1
            assert mock_send_email.call_count == 0

            # 3. Mark crawl_run_b as completed (no active crawls remaining)
            crawl_run_b.status = "completed"
            db.commit()

            assert has_active_crawls(db) is False

            # 4. Flush pending notifications
            flush_pending_notifications(db)

            # Verification: Exactly ONE consolidated email task must be dispatched for this receiver!
            # It must contain all 3 notifications (2 from Website A + 1 from Website B)
            # Find the call corresponding to this receiver
            receiver_email_calls = [
                call for call in mock_scheduler_add.call_args_list
                if (call.kwargs.get("kwargs") or {}).get("receiver_id") == receiver.id
            ]
            assert len(receiver_email_calls) == 1
            call_kwargs = receiver_email_calls[0].kwargs.get("kwargs") or {}
            assert set(call_kwargs.get("notification_ids", [])) == {
                receiver_notifs_a[0].id,
                receiver_notifs_a[1].id,
                receiver_notifs_b[0].id,
            }

            # All notifications in DB for this receiver should now be QUEUED
            updated_notifs = db.query(Notification).filter(
                Notification.id.in_([
                    receiver_notifs_a[0].id,
                    receiver_notifs_a[1].id,
                    receiver_notifs_b[0].id,
                ])
            ).all()
            assert all(n.status == "QUEUED" for n in updated_notifs)

    finally:
        # Cleanup
        db.query(Notification).filter(
            (Notification.receiver_id == receiver.id) | (Notification.rfp_id.in_([rfp_a1.id, rfp_a2.id, rfp_b1.id]))
        ).delete(synchronize_session=False)
        db.commit()
        db.delete(crawl_run_b)
        db.delete(rfp_a1)
        db.delete(rfp_a2)
        db.delete(rfp_b1)
        db.delete(website_a)
        db.delete(website_b)
        db.delete(receiver)
        db.commit()
        db.close()
