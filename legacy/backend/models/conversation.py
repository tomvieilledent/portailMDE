#!/usr/bin/env python3
"""Domain model for conversations (chat rooms)."""

from .base import BaseModel


class Conversation(BaseModel):
    """Conversation model representing a chat room.

    Attributes:
        participant_ids (list[str]): List of user UUIDs participating in the room.
        title (str | None): Optional group name (named group chat when set).
    """

    def __init__(self, participant_ids=None, title=None, **kwargs):
        super().__init__(**kwargs)
        self.participant_ids = participant_ids or []
        self.title = title

    @property
    def participant_ids(self):
        return self._participant_ids

    @participant_ids.setter
    def participant_ids(self, value):
        if value is None:
            self._participant_ids = []
            return
        if not isinstance(value, (list, tuple)):
            raise TypeError("participant_ids must be a list of UUIDs")
        self._participant_ids = list(value)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if value is None:
            self._title = None
            return
        if not isinstance(value, str):
            raise TypeError("title must be a string")
        value = value.strip()
        if len(value) > 200:
            raise ValueError("title must be at most 200 characters")
        self._title = value or None
