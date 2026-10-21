#!/usr/bin/env python3
"""Domain model for a scheduled training session."""

from .base import BaseModel


VALID_STATUSES = {'upcoming', 'full', 'completed', 'cancelled'}


class TrainingSession(BaseModel):
    """A scheduled instance of a training.

    A training can have multiple sessions; each session tracks its own
    capacity via *max_participants*.

    Attributes:
        training_id (str): Id of the parent training (required).
        start_date (datetime): Session start datetime (required).
        end_date (datetime): Session end datetime (required).
        max_participants (int): Maximum number of enrolled users (≥ 1).
        location (str | None): Optional physical location description.
        link (str | None): Optional remote meeting link.
        status (str): Lifecycle status — one of ``upcoming``, ``full``,
            ``completed``, ``cancelled``. Defaults to ``upcoming``.
    """

    def __init__(self, training_id, start_date, end_date, max_participants,
                 location=None, link=None, status='upcoming', **kwargs):
        super().__init__(**kwargs)
        self.training_id = training_id
        self.start_date = start_date
        self.end_date = end_date
        self.max_participants = max_participants
        self.location = location
        self.link = link
        self.status = status

    @property
    def training_id(self):
        return self._training_id

    @training_id.setter
    def training_id(self, value):
        """Set the parent training id.

        Args:
            value (str): Non-empty training identifier.

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("training_id is required")
        self._training_id = value

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        """Set the session start date.

        Args:
            value (datetime): Non-None start datetime.

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("start_date is required")
        self._start_date = value

    @property
    def end_date(self):
        return self._end_date

    @end_date.setter
    def end_date(self, value):
        """Set the session end date.

        Args:
            value (datetime): Non-None end datetime.

        Raises:
            ValueError: If *value* is falsy.
        """
        if not value:
            raise ValueError("end_date is required")
        self._end_date = value

    @property
    def max_participants(self):
        return self._max_participants

    @max_participants.setter
    def max_participants(self, value):
        """Set the participant capacity.

        Args:
            value (int | str): Capacity value, coerced to int.

        Raises:
            TypeError: If *value* cannot be converted to an integer.
            ValueError: If the resulting integer is less than 1.
        """
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise TypeError("max_participants must be an integer")
        if v < 1:
            raise ValueError("max_participants must be at least 1")
        self._max_participants = v

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        """Set the session status.

        Args:
            value (str): One of ``upcoming``, ``full``, ``completed``,
                ``cancelled``.

        Raises:
            ValueError: If *value* is not in :data:`VALID_STATUSES`.
        """
        if value not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        self._status = value
