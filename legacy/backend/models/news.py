#!/usr/bin/env python3
"""Domain model for news items."""

from .base import BaseModel


class News(BaseModel):
    """News item with basic validation for title and optional metadata.

    Attributes:
        title (str): Article headline (required, max 500 chars).
        source (str | None): Publisher name.
        summary (str | None): Short article summary.
        url (str | None): Link to the original article.
        published_at (datetime | None): Original publication datetime.
    """

    def __init__(self, title, source=None, summary=None, url=None, published_at=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.source = source
        self.summary = summary
        self.url = url
        self.published_at = published_at

    @property
    def title(self):
        """str: The article headline."""
        return self._title

    @title.setter
    def title(self, value):
        """Set and validate the news title.

        Args:
            value (str): Article headline; must be non-empty and ≤ 500 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds the length limit.
        """
        if not isinstance(value, str):
            raise TypeError("News title must be a string")
        value = value.strip()
        if not value:
            raise ValueError("News title cannot be empty")
        if len(value) > 500:
            raise ValueError("News title must be 500 characters or fewer")
        self._title = value
