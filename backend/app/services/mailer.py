"""Envoi d'emails : SMTP (Mailpit en développement), console, ou mémoire (tests)."""

import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Mail:
    """Email à envoyer (destinataire, sujet, texte et HTML optionnel)."""

    to: str
    subject: str
    text: str
    html: str | None = None


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mailer")

# Boîte d'envoi du backend « memory », inspectée par les tests.
outbox: list[Mail] = []


def _mask(address: str) -> str:
    """Masque l'adresse pour les journaux (``a***@domaine``)."""
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}"


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Envoie un email. Une erreur d'envoi est journalisée mais ne fait jamais échouer l'appelant."""
    settings = get_settings()
    mail = Mail(to, subject, text, html)
    backend = settings.mail_backend
    if backend == "memory":
        outbox.append(mail)
        return
    if backend == "console":
        logger.info("EMAIL (console) — %s", subject)
        return
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=10) as smtp:
            if settings.mail_use_tls:
                smtp.starttls()
            if settings.mail_username:
                smtp.login(settings.mail_username, settings.mail_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Échec de l'envoi de l'email « %s » à %s", subject, _mask(to))


def send_later(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Envoi asynchrone (thread dédié) pour ne pas ralentir la requête ; immédiat en test/console."""
    if get_settings().mail_backend in ("memory", "console"):
        send_email(to, subject, text, html)
    else:
        _executor.submit(send_email, to, subject, text, html)
