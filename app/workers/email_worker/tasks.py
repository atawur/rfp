import logging
from typing import List, Optional
from sqlalchemy.sql import func

from app.db.session import SessionLocal
from app.models.notification import Notification
from app.models.notification_receiver import NotificationReceiver
from app.models.email_log import EmailLog
from app.models.rfp import RFP
from app.models.user import User
from app.models.website import Website
from app.email.provider import email_provider
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_batch_rfp_email(
    receiver_id: Optional[int] = None,
    notification_ids: Optional[List[int]] = None,
    user_id: Optional[int] = None,
) -> str:
    """
    Email Worker: Sends a consolidated, professional email containing all new RFPs/RFQs
    to an eligible notification receiver (or legacy user).
    Groups items by Monitored Website/Source Portal, displaying the Source Name first.
    """
    if not notification_ids:
        return "No notifications to process"

    logger.info(
        f"Processing consolidated email for receiver_id={receiver_id}, user_id={user_id} with {len(notification_ids)} notification(s)"
    )
    db = SessionLocal()

    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.id.in_(notification_ids))
            .all()
        )
        if not notifications:
            return f"Failed: No notifications found for IDs {notification_ids}"

        # Resolve recipient name and email
        recipient_name = "Valued Member"
        recipient_email = None

        if receiver_id is not None:
            receiver = db.query(NotificationReceiver).filter(NotificationReceiver.id == receiver_id).first()
            if not receiver:
                return f"Failed: NotificationReceiver {receiver_id} not found"
            if receiver.status != "active":
                return f"Skipped: NotificationReceiver {receiver_id} ({receiver.email}) is inactive"
            recipient_name = receiver.name
            recipient_email = receiver.email
        elif user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return f"Failed: User {user_id} not found"
            recipient_name = user.name
            recipient_email = user.email
        else:
            # Fallback to inspecting notification records
            first_notif = notifications[0]
            if first_notif.receiver_id:
                receiver = db.query(NotificationReceiver).filter(NotificationReceiver.id == first_notif.receiver_id).first()
                if receiver and receiver.status == "active":
                    recipient_name = receiver.name
                    recipient_email = receiver.email
            elif first_notif.user_id:
                user = db.query(User).filter(User.id == first_notif.user_id).first()
                if user:
                    recipient_name = user.name
                    recipient_email = user.email

        if not recipient_email:
            return "Failed: Recipient email could not be resolved"

        # Mark notifications as QUEUED
        for notif in notifications:
            notif.status = "QUEUED"
        db.commit()

        # Fetch associated RFPs
        rfp_ids = [n.rfp_id for n in notifications if n.rfp_id]
        rfps = db.query(RFP).filter(RFP.id.in_(rfp_ids)).all()

        if not rfps:
            for notif in notifications:
                notif.status = "FAILED"
            db.commit()
            return f"Failed: No RFPs found for notification IDs {notification_ids}"

        frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")

        # Group RFPs by Website/Source Portal so different websites are clearly distinguished
        portal_groups = {}
        all_websites = db.query(Website).all()

        for rfp in rfps:
            website = None
            if rfp.website_id:
                website = db.query(Website).filter(Website.id == rfp.website_id).first()

            # If website is missing, match by source URL or organization name
            if not website and rfp.source_url and rfp.source_url.startswith("http") and rfp.source_url != "bulk_crawl":
                from urllib.parse import urlparse
                source_domain = urlparse(rfp.source_url).netloc.lower()
                for w in all_websites:
                    w_domain = urlparse(w.base_url or w.start_url or "").netloc.lower()
                    if w_domain and (w_domain in source_domain or source_domain in w_domain):
                        website = w
                        break

            if not website and rfp.organization:
                import re
                norm_org = re.sub(r'[^a-zA-Z0-9]', '', rfp.organization).lower()
                for w in all_websites:
                    norm_w = re.sub(r'[^a-zA-Z0-9]', '', w.name).lower()
                    if norm_w in norm_org or norm_org in norm_w:
                        website = w
                        break

            if website:
                group_key = f"website_{website.id}"
                portal_name = website.name.strip()
                clean_website_url = website.start_url or website.base_url
            else:
                import re
                # Clean and title-case organization so "BRAC Bank PLC" and "BRAC BANK PLC." merge
                raw_org = str(rfp.organization or "Public Procurement Portal").strip()
                clean_org = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', raw_org)).strip().title()
                group_key = f"org_{clean_org.lower()}"
                portal_name = clean_org or "Public Procurement Portal"
                clean_website_url = None

            portal_url = (
                clean_website_url
                if clean_website_url and str(clean_website_url).startswith("http")
                else (rfp.source_url if rfp.source_url and rfp.source_url.startswith("http") and rfp.source_url != "bulk_crawl" else f"{frontend_base}/rfps")
            )

            if group_key not in portal_groups:
                portal_groups[group_key] = {
                    "website": website,
                    "portal_name": portal_name,
                    "portal_url": portal_url,
                    "clean_website_url": clean_website_url,
                    "rfps": [],
                }
            portal_groups[group_key]["rfps"].append(rfp)

        portal_names = [g["portal_name"] for g in portal_groups.values()]

        # Build Subject: Highlight Website Name First
        if len(portal_names) == 1:
            primary_portal = portal_names[0]
            if len(rfps) == 1:
                subject = f"[{primary_portal}] New Procurement Opportunity: {rfps[0].title}"
            else:
                subject = f"[{primary_portal}] {len(rfps)} New Procurement Opportunities Discovered"
        else:
            subject = f"New Procurement Alerts: {len(rfps)} Opportunities across {len(portal_names)} Portals"

        # Build Plaintext Body (Source Name first, then content)
        text_lines = [
            f"Hello {recipient_name},",
            "",
            f"New procurement opportunities matching your monitored sources have been discovered by RFP Intelligence:",
            "",
        ]

        for group_key, group in portal_groups.items():
            text_lines.append("=" * 70)
            text_lines.append(f"SOURCE PORTAL: {group['portal_name'].upper()}")
            text_lines.append(f"Listing URL: {group['portal_url']}")
            text_lines.append(f"New Opportunities: {len(group['rfps'])}")
            text_lines.append("=" * 70)
            text_lines.append("")

            for idx, rfp in enumerate(group["rfps"], start=1):
                org_name = str(rfp.organization or "Procuring Entity").strip()
                deadline_str = str(rfp.submission_deadline or "Not Specified").strip()
                ref_line = f"   • Reference No: {rfp.reference_number}\n" if rfp.reference_number else ""
                cat_line = f"   • Classification: {rfp.primary_category}\n" if rfp.primary_category else ""
                budget_line = f"   • Budget: {rfp.estimated_budget} {rfp.currency or ''}\n" if rfp.estimated_budget else ""
                desc_snippet = f"   • Overview: {rfp.description[:200]}...\n" if rfp.description else ""

                # Ensure valid HTTP opportunity and platform URLs
                raw_source = str(rfp.source_url or "").strip()
                if raw_source.startswith("http") and raw_source != "bulk_crawl" and not raw_source.startswith("http://bulk_crawl"):
                    valid_source_url = raw_source
                elif group.get("clean_website_url") and str(group["clean_website_url"]).startswith("http"):
                    valid_source_url = group["clean_website_url"]
                else:
                    valid_source_url = f"{frontend_base}/rfps/{rfp.id}"

                platform_rfp_url = f"{frontend_base}/rfps/{rfp.id}"

                text_lines.append(
                    f"[{idx}] {rfp.title}\n"
                    f"   • Organization: {org_name}\n"
                    f"{ref_line}"
                    f"   • Submission Deadline: {deadline_str}\n"
                    f"{cat_line}"
                    f"{budget_line}"
                    f"{desc_snippet}"
                    f"   • Direct Opportunity URL: {valid_source_url}\n"
                    f"   • View on Platform: {platform_rfp_url}\n"
                )
            text_lines.append("")

        text_lines.extend([
            "----------------------------------------------------------------------",
            "View and download official tender documents directly through the links above.",
            "",
            "Best regards,",
            "RFP Intelligence & Monitoring Platform",
        ])
        body_text = "\n".join(text_lines)

        # Build Professional HTML Body (Source Name prominently first, then content cards)
        html_portal_sections = []
        for group_key, group in portal_groups.items():
            rfp_cards = []
            for rfp in group["rfps"]:
                org_name = str(rfp.organization or "Procuring Entity").strip()
                deadline_str = str(rfp.submission_deadline or "Not Specified").strip()
                ref_badge = f'<span style="background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-family: monospace;">Ref: {rfp.reference_number}</span>' if rfp.reference_number else ""
                cat_badge = f'<span style="background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{rfp.primary_category}</span>' if rfp.primary_category else ""
                budget_info = f'<div style="font-size: 12px; color: #047857; font-weight: 600; margin-top: 4px;">💰 Est. Budget: {rfp.estimated_budget} {rfp.currency or ""}</div>' if rfp.estimated_budget else ""
                desc_preview = f'<div style="font-size: 13px; color: #475569; margin: 8px 0; line-height: 1.5;">{rfp.description[:260]}...</div>' if rfp.description else ""

                # Ensure valid HTTP opportunity and platform URLs
                raw_source = str(rfp.source_url or "").strip()
                if raw_source.startswith("http") and raw_source != "bulk_crawl" and not raw_source.startswith("http://bulk_crawl"):
                    valid_source_url = raw_source
                elif group.get("clean_website_url") and str(group["clean_website_url"]).startswith("http"):
                    valid_source_url = group["clean_website_url"]
                else:
                    valid_source_url = f"{frontend_base}/rfps/{rfp.id}"

                platform_rfp_url = f"{frontend_base}/rfps/{rfp.id}"

                rfp_cards.append(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;">
                        <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #0f172a; line-height: 1.4;">
                            <a href="{valid_source_url}" target="_blank" style="color: #2563eb; text-decoration: none;">{rfp.title}</a>
                        </h3>
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                        {cat_badge}
                        {ref_badge}
                    </div>
                    <div style="font-size: 13px; color: #334155; margin-bottom: 4px;">
                        <strong>Organization:</strong> {org_name}
                    </div>
                    <div style="font-size: 13px; color: #b45309; font-weight: 600; margin-bottom: 4px;">
                        ⏳ <strong>Submission Deadline:</strong> {deadline_str}
                    </div>
                    {budget_info}
                    {desc_preview}
                    <div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <a href="{valid_source_url}" target="_blank" style="display: inline-block; background: #2563eb; color: #ffffff; padding: 8px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; text-decoration: none;">
                            View Opportunity & Documents &rarr;
                        </a>
                        <a href="{platform_rfp_url}" target="_blank" style="display: inline-block; background: #f8fafc; color: #0284c7; border: 1px solid #cbd5e1; padding: 8px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; text-decoration: none;">
                            Inspect on Platform
                        </a>
                    </div>
                </div>
                """)

            html_portal_sections.append(f"""
            <div style="margin-bottom: 24px; border: 1px solid #cbd5e1; border-radius: 10px; overflow: hidden;">
                <!-- Website Source Header First -->
                <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #38bdf8; padding: 14px 18px; border-bottom: 2px solid #38bdf8;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 700;">
                        Monitored Source Portal
                    </div>
                    <div style="font-size: 18px; font-weight: 800; color: #ffffff; margin: 4px 0;">
                        🌐 {group['portal_name']}
                    </div>
                    <div style="font-size: 12px; color: #93c5fd;">
                        <a href="{group['portal_url']}" target="_blank" style="color: #67e8f9; text-decoration: underline;">{group['portal_url']}</a>
                        &bull; {len(group['rfps'])} opportunity item(s)
                    </div>
                </div>
                <!-- Content Area -->
                <div style="padding: 16px; background: #f8fafc;">
                    {''.join(rfp_cards)}
                </div>
            </div>
            """)

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; color: #0f172a;">
            <div style="max-width: 660px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
                <!-- Platform Brand Header -->
                <div style="background: #090d16; padding: 20px 24px; border-bottom: 1px solid #1e293b; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">
                            RFP <span style="color: #06b6d4;">Intellect</span>
                        </div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                            Automated Procurement Intelligence & Source Monitoring
                        </div>
                    </div>
                    <div style="background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.4); padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #22d3ee; text-transform: uppercase;">
                        New Discovery
                    </div>
                </div>

                <!-- Intro Greeting -->
                <div style="padding: 24px 24px 12px 24px;">
                    <h2 style="margin: 0 0 8px 0; font-size: 18px; color: #0f172a;">Hello {recipient_name},</h2>
                    <p style="margin: 0; font-size: 14px; color: #475569; line-height: 1.5;">
                        New procurement opportunities matching your monitored sources have been extracted and processed. Each portal is identified below with direct links:
                    </p>
                </div>

                <!-- Distinguishable Portals & Content -->
                <div style="padding: 12px 24px;">
                    {''.join(html_portal_sections)}
                </div>

                <!-- Footer -->
                <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; font-size: 12px; color: #64748b; text-align: center; line-height: 1.5;">
                    This automated email alert was dispatched to <strong>{recipient_email}</strong> based on active notification settings in the RFP Intelligence Platform.<br>
                    &copy; RFP Intelligence & Monitoring Platform
                </div>
            </div>
        </body>
        </html>
        """

        msg_id = email_provider.send_email(
            to_email=str(recipient_email),
            subject=subject,
            body=body_text,
            html_body=html_body,
        )

        # Mark notifications as SENT and record email logs
        for notif in notifications:
            notif.status = "SENT"
            notif.sent_at = func.now()
            email_log = EmailLog(
                notification_id=notif.id,
                provider="EmailProvider",
                status="SUCCESS",
            )
            db.add(email_log)

        db.commit()
        logger.info(
            f"Consolidated email ({len(rfps)} RFPs across {len(portal_names)} portal(s)) successfully delivered to {recipient_email} (msg_id: {msg_id})"
        )
        return f"Successfully sent single email with {len(rfps)} RFPs to {recipient_email}"

    except Exception as e:
        logger.error(f"Failed to send consolidated email: {str(e)}")
        try:
            for notif_id in notification_ids:
                notif_record = db.query(Notification).filter(Notification.id == notif_id).first()
                if notif_record:
                    notif_record.status = "FAILED"
                    fail_log = EmailLog(
                        notification_id=notif_record.id,
                        provider="EmailProvider",
                        status="FAILED",
                        error=str(e),
                    )
                    db.add(fail_log)
            db.commit()
        except Exception as log_err:
            logger.error(f"Failed to record failure logs: {str(log_err)}")

        return f"Failed: {str(e)}"
    finally:
        db.close()


def send_rfp_email(notification_id: int) -> str:
    """
    Backwards-compatible single-notification email sender.
    Delegates to send_batch_rfp_email.
    """
    db = SessionLocal()
    receiver_id = None
    user_id = None
    try:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return f"Notification {notification_id} not found"
        receiver_id = notif.receiver_id
        user_id = notif.user_id
    finally:
        db.close()

    return send_batch_rfp_email(
        receiver_id=receiver_id,
        user_id=user_id,
        notification_ids=[notification_id],
    )


