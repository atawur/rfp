import pytest
import app.db.base
from app.db.session import SessionLocal

from app.models.notification_receiver import NotificationReceiver
from app.models.website import Website
from app.models.rfp import RFP
from app.models.notification import Notification
from app.services.notification_service import (
    get_eligible_receivers_for_rfp,
    evaluate_and_notify_users_batch,
)
from app.workers.email_worker.tasks import send_batch_rfp_email
from unittest.mock import patch


def test_notification_receiver_eligibility_and_dispatch():
    db = SessionLocal()
    try:
        # 1. Create two receivers: one active, one inactive
        r1 = NotificationReceiver(
            name="Alice Active",
            email="alice.test@example.com",
            status="active",
        )
        r2 = NotificationReceiver(
            name="Bob Inactive",
            email="bob.test@example.com",
            status="inactive",
        )
        r3 = NotificationReceiver(
            name="Charlie Specific",
            email="charlie.test@example.com",
            status="active",
        )
        db.add_all([r1, r2, r3])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)
        db.refresh(r3)

        # 2. Create Website with notify_all_receivers=False, linked only to r3
        site_specific = Website(
            name="Specific Portal X",
            base_url="https://portal-x.example.com",
            start_url="https://portal-x.example.com/rfps",
            status="active",
            notify_all_receivers=False,
            notification_receivers=[r3],
        )
        # Website with notify_all_receivers=True
        site_all = Website(
            name="Public Portal Y",
            base_url="https://portal-y.example.com",
            start_url="https://portal-y.example.com/rfps",
            status="active",
            notify_all_receivers=True,
        )
        db.add_all([site_specific, site_all])
        db.commit()
        db.refresh(site_specific)
        db.refresh(site_all)

        # 3. Create RFPs
        rfp_specific = RFP(
            website_id=site_specific.id,
            title="Specific Network Security Tender",
            organization="Specific Agency",
            source_url="https://portal-x.example.com/rfps/1",
            status="NEW",
        )
        rfp_all = RFP(
            website_id=site_all.id,
            title="General Cloud Infrastructure RFP",
            organization="General Ministry",
            source_url="https://portal-y.example.com/rfps/2",
            status="NEW",
        )
        db.add_all([rfp_specific, rfp_all])
        db.commit()
        db.refresh(rfp_specific)
        db.refresh(rfp_all)

        all_active = [r1, r3]

        # Test eligibility for rfp_specific (notify_all_receivers=False)
        eligible_specific = get_eligible_receivers_for_rfp(db, rfp_specific, all_active)
        assert len(eligible_specific) == 1
        assert eligible_specific[0].id == r3.id

        # Test eligibility for rfp_all (notify_all_receivers=True)
        eligible_all = get_eligible_receivers_for_rfp(db, rfp_all, all_active)
        assert len(eligible_all) == 2
        assert {r.id for r in eligible_all} == {r1.id, r3.id}

        # 4. Test evaluate_and_notify_users_batch creating notifications
        with patch("app.workers.email_worker.tasks.send_batch_rfp_email") as mock_send:
            created_notifs = evaluate_and_notify_users_batch(db, [rfp_specific])
            assert len(created_notifs) == 1
            assert created_notifs[0].receiver_id == r3.id

        # 5. Test send_batch_rfp_email template contains Website Name First
        test_notif = Notification(
            receiver_id=r3.id,
            rfp_id=rfp_specific.id,
            type="NEW_RFP",
            status="PENDING",
        )
        db.add(test_notif)
        db.commit()
        db.refresh(test_notif)

        with patch("app.email.provider.email_provider.send_email") as mock_email:
            mock_email.return_value = "mock_msg_123"
            res = send_batch_rfp_email(receiver_id=r3.id, notification_ids=[test_notif.id])
            assert "Successfully sent" in res
            assert mock_email.called
            call_kwargs = mock_email.call_args.kwargs
            subject = call_kwargs["subject"]
            body = call_kwargs["body"]
            html_body = call_kwargs["html_body"]

            # Website / Source Name must be displayed FIRST
            assert "[Specific Portal X]" in subject
            assert "SOURCE PORTAL: SPECIFIC PORTAL X" in body
            assert "Specific Portal X" in html_body
            assert "Specific Network Security Tender" in body

    finally:
        # Cleanup test records safely
        try:
            receiver_ids = [r.id for r in [r1, r2, r3] if 'id' in dir(r) and r.id]
            if receiver_ids:
                notif_ids = [n.id for n in db.query(Notification).filter(Notification.receiver_id.in_(receiver_ids)).all()]
                if notif_ids:
                    from app.models.email_log import EmailLog
                    db.query(EmailLog).filter(EmailLog.notification_id.in_(notif_ids)).delete(synchronize_session=False)
                    db.query(Notification).filter(Notification.id.in_(notif_ids)).delete(synchronize_session=False)
                for r in [r1, r2, r3]:
                    db.query(NotificationReceiver).filter(NotificationReceiver.id == r.id).delete(synchronize_session=False)

            rfp_ids = [rfp.id for rfp in [rfp_specific, rfp_all] if 'id' in dir(rfp) and rfp.id]
            if rfp_ids:
                db.query(RFP).filter(RFP.id.in_(rfp_ids)).delete(synchronize_session=False)

            site_ids = [s.id for s in [site_specific, site_all] if 'id' in dir(s) and s.id]
            if site_ids:
                db.query(Website).filter(Website.id.in_(site_ids)).delete(synchronize_session=False)

            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


