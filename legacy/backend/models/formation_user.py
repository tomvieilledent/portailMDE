#!/usr/bin/env python3
"""Domain model representing a user's relation to a training."""

from .base import BaseModel
from datetime import datetime, timezone


VALID_TYPES = {'interested', 'enrolled', 'completed'}


class FormationUser(BaseModel):
    """Association linking a user to a training with lifecycle tracking.

    A single row exists per ``(user_id, training_id)`` pair. The *type* field
    represents the current state in the lifecycle:

    - ``interested`` — user expressed interest; no session assigned yet.
    - ``enrolled`` — user is registered for a specific session.
    - ``completed`` — user attended the training; session is completed.
    - ``None`` — no active lifecycle state; the row only carries a personal
      bookmark (``saved`` is ``True``).

    Attributes:
        user_id (str): User identifier (required).
        training_id (str): Training identifier (required).
        session_id (str | None): Session the user is enrolled in; ``None``
            when the type is ``interested``.
        type (str | None): Lifecycle state — one of ``interested``,
            ``enrolled``, ``completed``, or ``None`` for a bookmark-only row.
        saved (bool): Personal bookmark flag, independent of the lifecycle.
            Lets a user save a training to review and filter it later.
        enrolled_at (datetime): UTC timestamp when the record was created.
        completed_at (datetime | None): UTC timestamp when the training was
            completed. Set automatically when status reaches ``completed``.
    """

    def __init__(self, user_id, training_id, session_id=None,
                 type='interested', saved=False, enrolled_at=None,
                 completed_at=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.training_id = training_id
        self.session_id = session_id
        self.type = type
        self.saved = saved
        self.enrolled_at = enrolled_at or datetime.now(timezone.utc)
        self.completed_at = completed_at

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        """Set the user id.

        Args:
            value (str): Non-empty user identifier.

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("user_id is required")
        self._user_id = value

    @property
    def training_id(self):
        return self._training_id

    @training_id.setter
    def training_id(self, value):
        """Set the training id.

        Args:
            value (str): Non-empty training identifier.

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("training_id is required")
        self._training_id = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        """Set the lifecycle type.

        Args:
            value (str | None): One of ``interested``, ``enrolled``,
                ``completed``, or ``None`` for a bookmark-only row.

        Raises:
            ValueError: If *value* is neither ``None`` nor in
                :data:`VALID_TYPES`.
        """
        if value is not None and value not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES} or None")
        self._type = value

    @property
    def saved(self):
        return self._saved

    @saved.setter
    def saved(self, value):
        """Set the personal bookmark flag.

        Args:
            value (bool): Whether the user has saved this training.
        """
        self._saved = bool(value)
