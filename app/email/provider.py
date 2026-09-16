import logging
from typing import Optional
import smtplib
import uuid
from email.message import EmailMessage
from app.core.config import settings


logger = logging.getLogger(__name__)

class EmailProvider:
    """
    Abstracts the email sending logic (e.g. via AWS SES, Resend, SMTP).
    """
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> Optional[str]:
        """
        Sends an email (with optional rich HTML payload) and returns a provider-specific
        message ID on success. Raises an exception on failure.
        """
        logger.info(f"Sending email to {to_email}")
        logger.debug(f"Subject: {subject}")
        logger.debug(f"Body: {body}")
        
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_FROM_EMAIL]):
            logger.warning("SMTP settings are not fully configured. Email not sent.")
            return f"mock_msg_id_{uuid.uuid4().hex[:8]}"

        msg = EmailMessage()
        msg.set_content(body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            message_id = msg.get('Message-ID', f"msg_{uuid.uuid4().hex}")
            return str(message_id)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise e

email_provider = EmailProvider()

