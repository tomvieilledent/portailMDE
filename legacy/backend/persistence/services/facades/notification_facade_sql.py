"""Notification persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.db import SessionLocal
from backend.persistence.models import Notification as ORMNotification
from ._common_sql import isoformat, session_scope


class NotificationFacade:
    """SQLAlchemy-backed facade for notification CRUD operations."""

    def create(self, recipient_id, content, is_read=False, **kwargs):
        """Persist a new notification.

        Args:
            recipient_id (str): UUID of the notification recipient.
            content (str): Notification body text (stripped before storage).
            is_read (bool): Initial read state. Defaults to ``False``.
            **kwargs: Optional ``created_at`` datetime override.

        Returns:
            dict: Newly created notification as a serialisable dict.
        """
        with session_scope() as db:
            notification = ORMNotification(
                recipient_id=recipient_id,
                content=content.strip(),
                is_read=is_read,
                created_at=kwargs.get('created_at') or datetime.now(timezone.utc),
            )
            db.add(notification)
            db.flush()
            db.refresh(notification)
            return self._to_dict(notification)

    def get(self, notification_id):
        """Retrieve a notification by primary key.

        Args:
            notification_id (str): Notification UUID.

        Returns:
            dict | None: Notification dict, or ``None`` if not found.
        """
        with session_scope() as db:
            notification: Any = db.query(ORMNotification).filter(
                ORMNotification.id == notification_id).first()
            return self._to_dict(notification) if notification else None

    def list(self, limit=100):
        """Return notifications ordered by creation date (newest first).

        Args:
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised notification dicts.
        """
        with session_scope() as db:
            rows = db.query(ORMNotification).order_by(
                ORMNotification.created_at.desc()).limit(limit).all()
            return [self._to_dict(row) for row in rows]

    def list_by_recipient(self, recipient_id, limit=100):
        """Return notifications for a specific recipient, newest first.

        Args:
            recipient_id (str): Recipient UUID.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised notification dicts.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMNotification)
                .filter(ORMNotification.recipient_id == recipient_id)
                .order_by(ORMNotification.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(row) for row in rows]

    def mark_read(self, notification_id):
        """Mark a notification as read.

        Args:
            notification_id (str): Notification UUID.

        Returns:
            bool: ``True`` when updated, ``False`` when not found.
        """
        with session_scope() as db:
            notification: Any = db.query(ORMNotification).filter(
                ORMNotification.id == notification_id).first()
            if not notification:
                return False
            notification.is_read = True
            db.add(notification)
            return True

    def delete(self, notification_id):
        """Permanently delete a notification row.

        Args:
            notification_id (str): Notification UUID.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        with session_scope() as db:
            notification: Any = db.query(ORMNotification).filter(
                ORMNotification.id == notification_id).first()
            if not notification:
                return False
            db.delete(notification)
            return True

    def _to_dict(self, notification):
        return {
            'id': notification.id,
            'recipient_id': notification.recipient_id,
            'content': notification.content,
            'is_read': notification.is_read,
            'created_at': isoformat(notification.created_at),
            'updated_at': isoformat(getattr(notification, 'updated_at', None)),
            'deactivate_by': getattr(notification, 'deactivate_by', None),
            'delete_by': getattr(notification, 'delete_by', None),
            'uploaded_at': isoformat(getattr(notification, 'uploaded_at', None)),
        }
