"""Conversation participant persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.models import ConversationParticipant as ORMConversationParticipant
from ._common_sql import isoformat, session_scope


class ConversationParticipantFacade:
    """SQLAlchemy-backed facade managing participant rows in conversations."""

    def create(self, conversation_id, user_id, **kwargs):
        """Link a user to a conversation.

        Args:
            conversation_id (str): Conversation UUID.
            user_id (str): User UUID.
            **kwargs: Optional ``created_at`` datetime override.

        Returns:
            dict: Newly created participant association as a serialisable dict.
        """
        with session_scope() as db:
            participant = ORMConversationParticipant(
                conversation_id=conversation_id,
                user_id=user_id,
                created_at=kwargs.get(
                    'created_at') or datetime.now(timezone.utc),
            )
            db.add(participant)
            db.flush()
            db.refresh(participant)
            return self._to_dict(participant)

    def get(self, participant_id):
        """Retrieve a participant row by primary key.

        Args:
            participant_id (str): Participant association UUID.

        Returns:
            dict | None: Participant dict, or ``None`` if not found.
        """
        with session_scope() as db:
            participant: Any = db.query(ORMConversationParticipant).filter(
                ORMConversationParticipant.id == participant_id).first()
            return self._to_dict(participant) if participant else None

    def is_participant(self, conversation_id, user_id):
        with session_scope() as db:
            row = db.query(ORMConversationParticipant).filter(
                ORMConversationParticipant.conversation_id == conversation_id,
                ORMConversationParticipant.user_id == user_id).first()
            return row is not None

    def list(self, limit=100):
        """Return participant rows, newest first.

        Args:
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised participant dicts.
        """
        with session_scope() as db:
            rows = db.query(ORMConversationParticipant).order_by(
                ORMConversationParticipant.created_at.desc()).limit(limit).all()
            return [self._to_dict(row) for row in rows]

    def list_by_conversation(self, conversation_id, limit=100):
        """Return participants for a specific conversation.

        Args:
            conversation_id (str): Conversation UUID.
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised participant dicts, oldest first.
        """
        with session_scope() as db:
            rows = (
                db.query(ORMConversationParticipant)
                .filter(ORMConversationParticipant.conversation_id == conversation_id)
                .order_by(ORMConversationParticipant.created_at.asc())
                .limit(limit)
                .all()
            )
            return [self._to_dict(row) for row in rows]

    def delete(self, participant_id):
        """Permanently delete a participant row.

        Args:
            participant_id (str): Participant association UUID.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        with session_scope() as db:
            participant: Any = db.query(ORMConversationParticipant).filter(
                ORMConversationParticipant.id == participant_id).first()
            if not participant:
                return False
            db.delete(participant)
            return True

    def _to_dict(self, participant):
        return {
            'id': participant.id,
            'conversation_id': participant.conversation_id,
            'user_id': participant.user_id,
            'created_at': isoformat(participant.created_at),
            'uploaded_at': isoformat(getattr(participant, 'uploaded_at', None)),
            'updated_at': isoformat(getattr(participant, 'updated_at', None)),
            'deactivate_by': getattr(participant, 'deactivate_by', None),
            'delete_by': getattr(participant, 'delete_by', None),
        }
