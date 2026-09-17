import logging
from typing import List, Dict
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.rfp import RFP
from app.models.website import Website
from app.models.notification_receiver import NotificationReceiver
from app.models.notification import Notification
from app.workers.email_worker.tasks import send_batch_rfp_email
import app.core.scheduler

logger = logging.getLogger(__name__)


def get_eligible_receivers_for_rfp(db: Session, rfp: RFP, all_active_receivers: List[NotificationReceiver]) -> List[NotificationReceiver]:
    """
    Determines which active NotificationReceivers are eligible to receive alerts for a specific RFP.
    Website-level logic:
    - If RFP's website has notify_all_receivers=True: all active receivers are eligible.
    - If RFP's website has notify_all_receivers=False: only active receivers linked to that website are eligible.
    - Resolves website if rfp.website_id is missing, and prevents broadcasting unmapped RFPs.
    """
    website = None
    if rfp.website_id:
        website = db.query(Website).filter(Website.id == rfp.website_id).first()

    if not website:
        # Attempt to match website by source_url domain or organization name
        all_websites = db.query(Website).all()
        if rfp.source_url and rfp.source_url.startswith("http") and rfp.source_url != "bulk_crawl":
            from urllib.parse import urlparse
            source_domain = urlparse(rfp.source_url).netloc.lower()
            for w in all_websites:
                w_domain = urlparse(w.base_url or w.start_url or "").netloc.lower()
                if w_domain and (w_domain in source_domain or source_domain in w_domain):
                    website = w
                    rfp.website_id = w.id
                    break

        if not website and rfp.organization:
            import re
            norm_org = re.sub(r'[^a-zA-Z0-9]', '', rfp.organization).lower()
            for w in all_websites:
                norm_w = re.sub(r'[^a-zA-Z0-9]', '', w.name).lower()
                if norm_w in norm_org or norm_org in norm_w:
                    website = w
                    rfp.website_id = w.id
                    break

    if not website:
        # If the RFP genuinely cannot be associated with any monitored website,
        # do NOT blast it to all receivers indiscriminately.
        return []

    if website.notify_all_receivers:
        return all_active_receivers

    # Only active receivers explicitly linked to this website
    linked_receiver_ids = {r.id for r in website.notification_receivers if r.status == "active"}
    return [r for r in all_active_receivers if r.id in linked_receiver_ids]


import threading
from datetime import datetime, timezone, timedelta

_dispatch_lock = threading.Lock()


def has_active_crawls(db: Session) -> bool:
    """
    Checks whether any website crawl is currently actively executing.
    """
    from app.models.crawl_run import CrawlRun
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    active_count = (
        db.query(CrawlRun)
        .filter(CrawlRun.status == "running", CrawlRun.created_at >= cutoff)
        .count()
    )
    return active_count > 0


def flush_pending_notifications(db: Session = None):
    """
    Flushes all PENDING notifications across all crawled websites.
    Groups them by receiver_id, marks them QUEUED, and dispatches EXACTLY ONE
    consolidated email per receiver, formatted website-by-website.
    """
    from app.db.session import SessionLocal
    from app.workers.email_worker.tasks import send_batch_rfp_email

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        with _dispatch_lock:
            pending_notifs = (
                db.query(Notification)
                .filter(Notification.status == "PENDING")
                .all()
            )
            if not pending_notifs:
                return

            receiver_to_notifs: Dict[int, List[int]] = defaultdict(list)
            for n in pending_notifs:
                if n.receiver_id:
                    receiver_to_notifs[n.receiver_id].append(n.id)
                    n.status = "QUEUED"

            db.commit()

            for receiver_id, notif_ids in receiver_to_notifs.items():
                if not notif_ids:
                    continue
                logger.info(
                    f"Dispatching single consolidated email with {len(notif_ids)} RFP(s) for receiver_id {receiver_id}"
                )
                if (
                    hasattr(app.core.scheduler, "scheduler")
                    and app.core.scheduler.scheduler
                    and app.core.scheduler.scheduler.running
                ):
                    app.core.scheduler.scheduler.add_job(
                        send_batch_rfp_email,
                        kwargs={"receiver_id": receiver_id, "notification_ids": notif_ids},
                    )
                else:
                    threading.Thread(
                        target=send_batch_rfp_email,
                        kwargs={"receiver_id": receiver_id, "notification_ids": notif_ids},
                        daemon=True,
                    ).start()
    finally:
        if close_db:
            db.close()


def schedule_flush_fallback(delay_seconds: int = 45):
    """
    Schedules a fallback flush in APScheduler to ensure notifications are never held
    indefinitely if any crawl runs unexpectedly long or gets interrupted.
    """
    run_date = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    if (
        hasattr(app.core.scheduler, "scheduler")
        and app.core.scheduler.scheduler
        and app.core.scheduler.scheduler.running
    ):
        try:
            app.core.scheduler.scheduler.add_job(
                flush_pending_notifications,
                trigger="date",
                run_date=run_date,
                id="flush_pending_notifications_fallback",
                replace_existing=True,
            )
        except Exception as e:
            logger.warning(f"Failed to schedule flush fallback: {e}")
    else:
        timer = threading.Timer(delay_seconds, flush_pending_notifications)
        timer.daemon = True
        timer.start()


def evaluate_and_notify_users_batch(db: Session, rfps: List[RFP]) -> List[Notification]:
    """
    Notification Eligibility Engine:
    Given a list of newly discovered RFPs/RFQs, determines eligible active NotificationReceivers
    based on each RFP's source website notification settings.
    Creates PENDING notifications and schedules consolidated delivery.
    """
    if not rfps:
        return []

    # Fetch all active notification receivers
    all_active_receivers: List[NotificationReceiver] = (
        db.query(NotificationReceiver)
        .filter(NotificationReceiver.status == "active")
        .all()
    )

    if not all_active_receivers:
        logger.info("No active notification receivers registered; skipping email alerts.")
        return []

    # Map receiver_id -> list of matching RFPs
    receiver_to_rfps: Dict[int, List[RFP]] = defaultdict(list)
    receiver_map = {r.id: r for r in all_active_receivers}

    for rfp in rfps:
        eligible_receivers = get_eligible_receivers_for_rfp(db, rfp, all_active_receivers)
        for receiver in eligible_receivers:
            receiver_to_rfps[receiver.id].append(rfp)

    all_created_notifications: List[Notification] = []

    for receiver_id, matching_rfps in receiver_to_rfps.items():
        receiver = receiver_map.get(receiver_id)
        if not receiver or not matching_rfps:
            continue

        receiver_notifications = []
        for rfp in matching_rfps:
            # Prevent duplicates: ensure notification doesn't already exist for this receiver and RFP
            existing = (
                db.query(Notification)
                .filter(
                    Notification.receiver_id == receiver.id,
                    Notification.rfp_id == rfp.id,
                    Notification.type == "NEW_RFP",
                )
                .first()
            )
            if not existing:
                notif = Notification(
                    receiver_id=receiver.id,
                    rfp_id=rfp.id,
                    type="NEW_RFP",
                    status="PENDING",
                )
                db.add(notif)
                receiver_notifications.append(notif)

        if receiver_notifications:
            db.commit()
            for notif in receiver_notifications:
                db.refresh(notif)
            all_created_notifications.extend(receiver_notifications)

    # Consolidation Dispatch:
    # If other websites are currently crawling, wait for them to finish or fire via fallback.
    # If no other crawls are actively running, flush immediately.
    if all_created_notifications:
        if has_active_crawls(db):
            logger.info(
                f"Active crawls in progress; holding {len(all_created_notifications)} notification(s) for consolidation and scheduling fallback."
            )
            schedule_flush_fallback(delay_seconds=45)
        else:
            logger.info("No other active crawls in progress; flushing consolidated notifications immediately.")
            flush_pending_notifications(db)

    return all_created_notifications


def evaluate_and_notify_users(db: Session, rfp: RFP) -> List[Notification]:
    """
    Single-RFP helper that delegates to evaluate_and_notify_users_batch.
    """
    return evaluate_and_notify_users_batch(db, [rfp])


