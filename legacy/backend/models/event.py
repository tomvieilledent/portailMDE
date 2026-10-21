#!/usr/bin/env python3
"""Domain model for a calendar event (agenda)."""

from .base import BaseModel


class Event(BaseModel):
    """A simple agenda event, visible by everyone.

    Attributes:
        title (str): Event title (required).
        date (str): Event day as ``YYYY-MM-DD`` (required).
        time (str | None): Optional time as ``HH:MM``.
        color (str | None): Optional UI color class.
        description (str | None): Optional free-text description.
        creator (str | None): Optional free-text creator label.
        created_by (str | None): Id of the user who created the event.
    """

    def __init__(self, title, date, time=None, color=None, description=None,
                 creator=None, created_by=None, is_public=False, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.date = date
        self.time = time
        self.color = color
        self.description = description
        self.creator = creator
        self.created_by = created_by
        self.is_public = bool(is_public)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        """Set the event title.

        Args:
            value (str): Non-empty title.

        Raises:
            ValueError: If *value* is falsy or blank.
        """
        if not value or not str(value).strip():
            raise ValueError("title is required")
        self._title = str(value).strip()

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        """Set the event date.

        Args:
            value (str): Non-empty date string (``YYYY-MM-DD``).

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("date is required")
        self._date = value
