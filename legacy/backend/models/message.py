#!/usr/bin/env python3
"""Domain model for messages exchanged between users."""

from .base import BaseModel


class Message(BaseModel):
    """Message entity containing author, content and optional references.

    Attributes:
        content (str): Text body of the message (required, max 5 000 chars).
    """

    @property
    def content(self):
        """str: The message text."""
        return self._content

    @content.setter
    def content(self, value):
        """Set and validate the message content.

        Args:
            value (str): Message text; must be non-empty and ≤ 5 000 characters.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds the length limit.
        """
        if not isinstance(value, str):
            raise TypeError("Message content must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Message content cannot be empty")
        if len(value) > 5000:
            raise ValueError("Message content must be 5000 characters or fewer")
        self._content = value
