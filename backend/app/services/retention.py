"""Purge des données personnelles arrivées au terme de leur durée de conservation."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Message, Notification
from app.services import auth, storage

logger = logging.getLogger(__name__)


def purge_personal_data(session: Session) -> dict[str, int]:
    """Supprime jetons expirés, notifications anciennes et messages supprimés (avec leurs fichiers)."""
    settings = get_settings()
    now = datetime.now(UTC)
    tokens = auth.purge_expired(session)
    notifications = session.execute(
        delete(Notification).where(
            Notification.created_at < now - timedelta(days=settings.notification_retention_days)
        )
    ).rowcount
    cutoff = now - timedelta(days=settings.deleted_message_retention_days)
    old = session.query(Message).filter(Message.deleted_at < cutoff).all()
    files = [m.file_path for m in old]
    for message in old:
        session.delete(message)
    session.commit()
    for path in files:
        storage.delete_file(path)
    result = {"tokens": tokens, "notifications": notifications, "messages": len(old)}
    logger.info("Purge de conservation : %s", result)
    return result
