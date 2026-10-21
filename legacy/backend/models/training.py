#!/usr/bin/env python3
"""Domain model for trainings."""

from .base import BaseModel


class Training(BaseModel):
    """Training metadata with field validation.

    Attributes:
        title (str): Training title (required, max 200 chars).
        company_id (str | None): Optional owning company id.
        description (str | None): Optional description (max 2 000 chars).
        picture (str | None): Optional picture path/URL (max 512 chars).
        category (str | None): Optional free-text category (max 100 chars).
        type (str): Kind of entry, ``'formation'`` (default) or ``'atelier'``.
    """

    def __init__(self, title, company_id=None, description=None, picture=None,
                 category=None, type=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.company_id = company_id
        self.description = description
        self.picture = picture
        self.category = category
        self.type = type

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        """Set and validate the training title.

        Args:
            value (str): Title text; must be non-empty and ≤ 200 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds the length limit.
        """
        if not isinstance(value, str):
            raise TypeError("Training title must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Training title cannot be empty")
        if len(value) > 200:
            raise ValueError("Training title must be 200 characters or fewer")
        self._title = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        """Set and validate the optional description.

        Args:
            value (str | None): Description text; max 2 000 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* exceeds the length limit.
        """
        if value is None:
            self._description = None
            return
        if not isinstance(value, str):
            raise TypeError("Description must be a string")
        if len(value) > 2000:
            raise ValueError("Description must be 2000 characters or fewer")
        self._description = value.strip()

    @property
    def picture(self):
        return self._picture

    @picture.setter
    def picture(self, value):
        """Set and validate the optional picture path.

        Args:
            value (str | None): Picture path or URL; max 512 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds the length limit.
        """
        if value is None:
            self._picture = None
            return
        if not isinstance(value, str):
            raise TypeError("Picture must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Picture cannot be empty")
        if len(value) > 512:
            raise ValueError("Picture must be 512 characters or fewer")
        self._picture = value

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        """Set the optional free-text category (no fixed list).

        Args:
            value (str | None): Category label; trimmed, max 100 chars.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* exceeds the length limit.
        """
        if value is None:
            self._category = None
            return
        if not isinstance(value, str):
            raise TypeError("Category must be a string")
        value = value.strip()
        if not value:
            self._category = None
            return
        if len(value) > 100:
            raise ValueError("Category must be 100 characters or fewer")
        self._category = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        """Set the training kind: ``'formation'`` (default) or ``'atelier'``.

        Args:
            value (str | None): One of ``'formation'`` / ``'atelier'``;
                ``None`` defaults to ``'formation'``.

        Raises:
            ValueError: If *value* is not a recognised kind.
        """
        if value is None or value == '':
            self._type = 'formation'
            return
        if not isinstance(value, str):
            raise TypeError("Type must be a string")
        value = value.strip().lower()
        if value not in ('formation', 'atelier'):
            raise ValueError("Type must be 'formation' or 'atelier'")
        self._type = value
