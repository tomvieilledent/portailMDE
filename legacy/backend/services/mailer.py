"""Best-effort SMTP email sending, configured entirely from the environment.

This helper is intentionally dependency-free (stdlib ``smtplib``). It is used
by the password-reset flow and the public contact form. When SMTP is not
configured (no ``SMTP_HOST``), :func:`send_email` is a no-op that returns
``False`` so callers can degrade gracefully (e.g. keep working in dev without
a mail server).

Environment variables
    SMTP_HOST        SMTP server hostname (enables sending when set).
    SMTP_PORT        SMTP server port. Default 587.
    SMTP_USER        Username for authentication (optional).
    SMTP_PASSWORD    Password for authentication (optional).
    SMTP_USE_TLS     "true"/"false" — STARTTLS. Default "true".
    SMTP_USE_SSL     "true"/"false" — implicit SSL (SMTPS). Default "false".
    MAIL_FROM        From address. Defaults to SMTP_USER.
    MAIL_FROM_NAME   Optional display name for the From header.
    CONTACT_RECIPIENT  Inbox that receives contact-form messages.
    FRONTEND_URL     Public base URL of the frontend (for reset links).
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def is_configured() -> bool:
    """Return ``True`` when a SMTP host is configured."""
    return bool(os.getenv('SMTP_HOST'))


def mail_from() -> str:
    """Resolve the From address from the environment."""
    return os.getenv('MAIL_FROM') or os.getenv('SMTP_USER') or 'no-reply@localhost'


def contact_recipient() -> str | None:
    """Inbox that should receive contact-form submissions."""
    return os.getenv('CONTACT_RECIPIENT') or None


def frontend_url() -> str:
    """Public base URL of the frontend (no trailing slash)."""
    return (os.getenv('FRONTEND_URL') or 'http://localhost:3000').rstrip('/')


def send_email(to, subject: str, text_body: str,
               html_body: str | None = None, reply_to: str | None = None) -> bool:
    """Send an email; returns ``True`` on success, ``False`` otherwise.

    Never raises: connection/auth failures are logged and swallowed so the
    calling request can still succeed. When SMTP is not configured this is a
    no-op returning ``False``.

    Args:
        to: Recipient address, or a list of addresses.
        subject: Email subject line.
        text_body: Plain-text body (always sent).
        html_body: Optional HTML alternative.
        reply_to: Optional Reply-To address.
    """
    if not is_configured():
        logger.info('SMTP not configured; skipping email to %s (%s)', to, subject)
        return False

    recipients = [to] if isinstance(to, str) else list(to)
    if not recipients:
        return False

    msg = EmailMessage()
    from_name = os.getenv('MAIL_FROM_NAME')
    msg['From'] = formataddr((from_name, mail_from())) if from_name else mail_from()
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')

    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASSWORD')
    use_ssl = _env_bool('SMTP_USE_SSL', False)
    use_tls = _env_bool('SMTP_USE_TLS', True)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
        with server:
            if use_tls and not use_ssl:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        logger.info('Email sent to %s (%s)', recipients, subject)
        return True
    except Exception as exc:  # noqa: BLE001 — best-effort, never break the request
        logger.warning('Failed to send email to %s: %s', recipients, exc)
        return False
