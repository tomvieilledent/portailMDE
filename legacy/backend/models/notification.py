#!/usr/bin/env python3
"""Domain model for user notifications."""

from .base import BaseModel


class Notification(BaseModel):
    """Notification entity with recipient, content and read-state.

    Attributes:
        content (str): Notification body text (required, max 1 000 chars).
    """

    @property
    def content(self):
        """str: The notification body text."""
        return self._content

    @content.setter
    def content(self, value):
        """Set and validate the notification content.

        Args:
            value (str): Notification text; must be non-empty and ≤ 1 000 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds the length limit.
        """
        if not isinstance(value, str):
            raise TypeError("Notification content must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Notification content cannot be empty")
        if len(value) > 1000:
            raise ValueError("Notification content must be 1000 characters or fewer")
        self._content = value
