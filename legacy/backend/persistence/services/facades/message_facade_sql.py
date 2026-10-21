"""Message persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, or_

from backend.persistence.db import SessionLocal
from backend.persistence.models import Message as ORMMessage
from ._common_sql import isoformat, normalize_text, session_scope


class MessageFacade:
    """SQLAlchemy-backed facade for message CRUD operations.

    All public methods return plain dicts suitable for JSON serialisation.
    """

    def create(self, author_id, content, recipient_id=None, conversation_id=None,
               file_url=None, file_name=None, **kwargs):
        """Persist a new message.

        Args:
            author_id (str): UUID of the message author.
            content (str): Message body text.
            recipient_id (str | None): Optional direct recipient UUID.
            conversation_id (str | None): Optional conversation UUID.
            file_url (str | None): Optional URL of an attached file.
            file_name (str | None): Original filename of the attachment.
            **kwargs: Optional ``created_at`` datetime override.

        Returns:
            dict: Newly created message as a serialisable dict.
        """
        with session_scope() as db:
            message = ORMMessage(
                author_id=author_id,
                recipient_id=recipient_id,
                conversation_id=conversation_id,
                content=normalize_text(content),
                file_url=file_url,
                file_name=file_name,
                created_at=kwargs.get('created_at') or datetime.now(timezone.utc),
            )
            db.add(message)
            db.flush()
            db.refresh(message)
            return self._to_dict(message)

    def get(self, message_id):
        """Retrieve a message by primary key.

        Args:
            message_id (str): Message UUID.

        Returns:
            dict | None: Message dict, or ``None`` if not found.
        """
        with session_scope() as db:
            message: Any = db.query(ORMMessage).filter(
                ORMMessage.id == message_id,
                ORMMessage.is_active.isnot(False)).first()
            return self._to_dict(message) if message else None

    def list(self, limit=100):
        """Return the most recent messages across all conversations.

        Args:
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised message dicts, newest first.
        """
        with session_scope() as db:
            rows = db.query(ORMMessage).filter(
                ORMMessage.is_active.isnot(False)).order_by(
                ORMMessage.created_at.desc()).limit(limit).all()
            return [self._to_dict(row) for row in rows]

    def list_by_conversation(self, conversation_id, limit=100):
        """Return messages for a specific conversation in chronological order.

        Args:
            conversation_id (str): Conversation UUID.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised message dicts, oldest first.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMMessage)
                .filter(ORMMessage.conversation_id == conversation_id,
                        ORMMessage.is_active.isnot(False))
                .order_by(ORMMessage.created_at.asc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(row) for row in rows]

    def list_direct(self, user_a, user_b, limit=100):
        """Return the direct-message thread between two users.

        Direct messages carry a ``recipient_id`` and no ``conversation_id``;
        this returns both directions (a→b and b→a) in chronological order.

        Args:
            user_a (str): One participant's UUID.
            user_b (str): The other participant's UUID.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised message dicts, oldest first.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMMessage)
                .filter(
                    ORMMessage.conversation_id.is_(None),
                    ORMMessage.is_active.isnot(False),
                    or_(
                        and_(ORMMessage.author_id == user_a,
                             ORMMessage.recipient_id == user_b),
                        and_(ORMMessage.author_id == user_b,
                             ORMMessage.recipient_id == user_a),
                    ),
                )
                .order_by(ORMMessage.created_at.asc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(row) for row in rows]

    def list_by_author(self, author_id, limit=100):
        """Return messages sent by a specific author.

        Args:
            author_id (str): Author UUID.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised message dicts, newest first.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMMessage)
                .filter(ORMMessage.author_id == author_id,
                        ORMMessage.is_active.isnot(False))
                .order_by(ORMMessage.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(row) for row in rows]

    def mark_read(self, message_id, user_id):
        """Mark a single message as read on behalf of a reader.

        A message is only flagged when the reader is *not* its author
        (you don't "read" your own message). Idempotent.

        Args:
            message_id (str): Message UUID.
            user_id (str): UUID of the reader.

        Returns:
            dict | None: Updated message dict, or ``None`` if not found.
        """
        with session_scope() as db:
            message: Any = db.query(ORMMessage).filter(
                ORMMessage.id == message_id,
                ORMMessage.is_active.isnot(False)).first()
            if not message:
                return None
            if message.author_id != user_id and not message.is_read:
                message.is_read = True
                db.flush()
                db.refresh(message)
            return self._to_dict(message)

    def mark_conversation_read(self, conversation_id, user_id):
        """Mark every message in a conversation as read for a given user.

        Only messages the user did not author are affected.

        Args:
            conversation_id (str): Conversation UUID.
            user_id (str): UUID of the reader.

        Returns:
            int: Number of messages newly marked as read.
        """
        with session_scope() as db:
            return db.query(ORMMessage).filter(
                ORMMessage.conversation_id == conversation_id,
                ORMMessage.author_id != user_id,
                ORMMessage.is_read.is_(False),
                ORMMessage.is_active.isnot(False),
            ).update({ORMMessage.is_read: True}, synchronize_session=False)

    def count_unread_for_conversations(self, conversation_ids, user_id):
        """Count unread messages across the given conversations for a user.

        Args:
            conversation_ids (list[str]): Conversation UUIDs to scan.
            user_id (str): UUID of the reader.

        Returns:
            int: Number of unread messages not authored by the user.
        """
        if not conversation_ids:
            return 0
        with session_scope() as db:
            return db.query(ORMMessage).filter(
                ORMMessage.conversation_id.in_(conversation_ids),
                ORMMessage.author_id != user_id,
                ORMMessage.is_read.is_(False),
                ORMMessage.is_active.isnot(False),
            ).count()

    def count_unread_dms(self, user_id):
        """Count unread direct messages addressed to a user.

        Direct messages are those with a ``recipient_id`` and no
        ``conversation_id``.

        Args:
            user_id (str): Recipient UUID.

        Returns:
            int: Number of unread direct messages.
        """
        with session_scope() as db:
            return db.query(ORMMessage).filter(
                ORMMessage.recipient_id == user_id,
                ORMMessage.conversation_id.is_(None),
                ORMMessage.is_read.is_(False),
                ORMMessage.is_active.isnot(False),
            ).count()

    def count_unread_dms_by_sender(self, user_id):
        """Count unread direct messages addressed to a user, grouped by sender.

        Args:
            user_id (str): Recipient UUID.

        Returns:
            dict[str, int]: Mapping ``author_id -> unread count``.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMMessage.author_id, func.count(ORMMessage.id))
                .filter(
                    ORMMessage.recipient_id == user_id,
                    ORMMessage.conversation_id.is_(None),
                    ORMMessage.is_read.is_(False),
                    ORMMessage.is_active.isnot(False),
                )
                .group_by(ORMMessage.author_id)
                .all()
            )
            return {author_id: count for author_id, count in rows}

    def mark_direct_read(self, reader_id, sender_id):
        """Mark the direct messages from ``sender_id`` to ``reader_id`` as read.

        Args:
            reader_id (str): UUID of the recipient marking messages read.
            sender_id (str): UUID of the message author.

        Returns:
            int: Number of messages newly marked as read.
        """
        with session_scope() as db:
            return db.query(ORMMessage).filter(
                ORMMessage.author_id == sender_id,
                ORMMessage.recipient_id == reader_id,
                ORMMessage.conversation_id.is_(None),
                ORMMessage.is_read.is_(False),
                ORMMessage.is_active.isnot(False),
            ).update({ORMMessage.is_read: True}, synchronize_session=False)

    def deactivate(self, message_id):
        """Soft-delete a message (mark it inactive, keep the row).

        Soft-deleted messages are excluded from every read/list/count
        method, so they disappear from the API while staying auditable.

        Args:
            message_id (str): Message UUID.

        Returns:
            bool: ``True`` when deactivated, ``False`` when not found or
            already inactive.
        """
        with session_scope() as db:
            message: Any = db.query(ORMMessage).filter(
                ORMMessage.id == message_id,
                ORMMessage.is_active.isnot(False)).first()
            if not message:
                return False
            message.is_active = False
            return True

    def delete(self, message_id):
        """Permanently delete a message row.

        Args:
            message_id (str): Message UUID.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        with session_scope() as db:
            message: Any = db.query(ORMMessage).filter(
                ORMMessage.id == message_id).first()
            if not message:
                return False
            db.delete(message)
            return True

    def _to_dict(self, message):
        return {
            'id': message.id,
            'author_id': message.author_id,
            'recipient_id': message.recipient_id,
            'conversation_id': message.conversation_id,
            'content': message.content,
            'file_url': getattr(message, 'file_url', None),
            'file_name': getattr(message, 'file_name', None),
            'is_read': bool(message.is_read),
            'is_active': bool(getattr(message, 'is_active', True)),
            'created_at': isoformat(message.created_at),
            'updated_at': isoformat(getattr(message, 'updated_at', None)),
            'deactivate_by': getattr(message, 'deactivate_by', None),
            'delete_by': getattr(message, 'delete_by', None),
            'uploaded_at': isoformat(getattr(message, 'uploaded_at', None)),
        }
