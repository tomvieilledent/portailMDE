"""Conversation persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.db import SessionLocal
from backend.persistence.models import Conversation as ORMConversation
from ._common_sql import from_csv, isoformat, session_scope, to_csv


class ConversationFacade:
    """SQLAlchemy-backed facade for conversation CRUD and participant management.

    Participant ids are stored as a comma-separated string in the database
    and exposed as a list via :meth:`_to_dict`.
    """

    def create(self, participant_ids=None, title=None, creator_id=None, **kwargs):
        """Persist a new conversation.

        Args:
            participant_ids (list[str] | None): Initial participant UUIDs.
            title (str | None): Optional group name.
            creator_id (str | None): UUID of the user creating the group.
                Only this user may later rename it or add/remove members.
            **kwargs: Optional ``is_active`` and ``created_at`` overrides.

        Returns:
            dict: Newly created conversation as a serialisable dict.
        """
        with session_scope() as db:
            conversation = ORMConversation(
                title=title,
                creator_id=creator_id,
                participant_ids=to_csv(participant_ids or []),
                is_active=kwargs.get('is_active', True),
                created_at=kwargs.get(
                    'created_at') or datetime.now(timezone.utc),
            )
            db.add(conversation)
            db.flush()
            db.refresh(conversation)
            return self._to_dict(conversation)

    def get(self, conversation_id):
        """Retrieve a conversation by primary key.

        Args:
            conversation_id(str): Conversation UUID.

        Returns:
            dict | None: Conversation dict, or ``None`` if not found.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            return self._to_dict(conversation) if conversation else None

    def list(self, limit=100):
        """Return a list of conversations, newest first.

        Args:
            limit(int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised conversation dicts.
        """
        with session_scope() as db:
            rows = db.query(ORMConversation).order_by(
                ORMConversation.created_at.desc()).limit(limit).all()
            return [self._to_dict(row) for row in rows]

    def list_by_participant(self, user_id, limit=100):
        """Return conversations the given user participates in, newest first.

        Args:
            user_id (str): User UUID to filter on.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised conversation dicts the user belongs to.
        """
        with session_scope() as db:
            rows: Any = db.query(ORMConversation).order_by(
                ORMConversation.created_at.desc()).all()
            result = []
            for row in rows:
                if user_id in from_csv(row.participant_ids):
                    result.append(self._to_dict(row))
                    if len(result) >= limit:
                        break
            return result

    def is_participant(self, conversation_id, user_id):
        """Check whether a user belongs to a conversation.

        Reads the ``participant_ids`` CSV column, which is the source of
        truth written by :meth:`create` / :meth:`add_participant`.

        Args:
            conversation_id (str): Conversation UUID.
            user_id (str): User UUID.

        Returns:
            bool: ``True`` when the user is a participant.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return False
            return user_id in from_csv(conversation.participant_ids)

    def is_creator(self, conversation_id, user_id):
        """Check whether a user is the creator/owner of a conversation.

        Args:
            conversation_id (str): Conversation UUID.
            user_id (str): User UUID.

        Returns:
            bool: ``True`` when the user created the conversation.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return False
            return getattr(conversation, 'creator_id', None) == user_id

    def add_participant(self, conversation_id, user_id):
        """Add a participant to a conversation(idempotent).

        Args:
            conversation_id(str): Conversation UUID.
            user_id(str): User UUID to add.

        Returns:
            dict | None: Updated conversation dict, or ``None`` if not found.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return None
            participants = from_csv(conversation.participant_ids)
            if user_id not in participants:
                participants.append(user_id)
                conversation.participant_ids = to_csv(participants)
            db.add(conversation)
            db.flush()
            db.refresh(conversation)
            return self._to_dict(conversation)

    def remove_participant(self, conversation_id, user_id):
        """Remove a participant from a conversation.

        Args:
            conversation_id(str): Conversation UUID.
            user_id(str): User UUID to remove.

        Returns:
            dict | None: Updated conversation dict, or ``None`` if not found.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return None
            participants = from_csv(conversation.participant_ids)
            participants = [item for item in participants if item != user_id]
            conversation.participant_ids = to_csv(participants)
            db.add(conversation)
            db.flush()
            db.refresh(conversation)
            return self._to_dict(conversation)

    def set_title(self, conversation_id, title):
        """Rename a conversation (set or clear its group title).

        Args:
            conversation_id (str): Conversation UUID.
            title (str | None): New group name, or ``None`` to clear it.

        Returns:
            dict | None: Updated conversation dict, or ``None`` if not found.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return None
            conversation.title = title
            db.add(conversation)
            db.flush()
            db.refresh(conversation)
            return self._to_dict(conversation)

    def deactivate(self, conversation_id):
        """Soft-deactivate a conversation.

        Args:
            conversation_id(str): Conversation UUID.

        Returns:
            bool: ``True`` when deactivated, ``False`` when not found.
        """
        with session_scope() as db:
            conversation: Any = db.query(ORMConversation).filter(
                ORMConversation.id == conversation_id).first()
            if not conversation:
                return False
            conversation.is_active = False
            db.add(conversation)
            return True

    def _to_dict(self, conversation):
        return {
            'id': conversation.id,
            'title': getattr(conversation, 'title', None),
            'creator_id': getattr(conversation, 'creator_id', None),
            'participant_ids': from_csv(conversation.participant_ids),
            'is_active': conversation.is_active,
            'created_at': isoformat(conversation.created_at),
            'updated_at': isoformat(getattr(conversation, 'updated_at', None)),
            'deactivate_by': getattr(conversation, 'deactivate_by', None),
            'delete_by': getattr(conversation, 'delete_by', None),
            'uploaded_at': isoformat(getattr(conversation, 'uploaded_at', None)),
        }
