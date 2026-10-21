#!/usr/bin/env python3
"""Domain model linking a user to a conversation."""

from .base import BaseModel


class ConversationParticipant(BaseModel):
    """Association between a conversation and a participant user.

    Attributes:
        conversation_id (str): Conversation identifier (required).
        user_id (str): User identifier (required).
    """

    def __init__(self, conversation_id, user_id, **kwargs):
        super().__init__(**kwargs)
        self.conversation_id = conversation_id
        self.user_id = user_id

    @property
    def conversation_id(self):
        return self._conversation_id

    @conversation_id.setter
    def conversation_id(self, value):
        self._conversation_id = self.validate_conversation_id(value)

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        self._user_id = self.validate_user_id(value)

    @staticmethod
    def validate_conversation_id(value):
        """Validate a conversation id value.

        Args:
            value (str): Value to validate as a conversation id.

        Returns:
            str: Stripped, validated conversation id.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or only whitespace.
        """
        if not isinstance(value, str):
            raise TypeError('conversation_id must be a string')
        v = value.strip()
        if not v:
            raise ValueError('conversation_id is required')
        return v

    @staticmethod
    def validate_user_id(value):
        """Validate a user id value.

        Args:
            value (str): Value to validate as a user id.

        Returns:
            str: Stripped, validated user id.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or only whitespace.
        """
        if not isinstance(value, str):
            raise TypeError('user_id must be a string')
        v = value.strip()
        if not v:
            raise ValueError('user_id is required')
        return v
