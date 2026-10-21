#!/usr/bin/env python3
"""Base domain model providing common identity and timestamp fields."""

import uuid
from datetime import datetime, timezone


class BaseModel:
    """Lightweight non-ORM base used by all domain models.

    Attributes:
        id (uuid.UUID): Unique identifier, auto-generated if not provided.
        is_active (bool): Soft-delete flag.
        created_at (datetime): UTC creation timestamp.
        updated_at (datetime | None): UTC last-update timestamp.
        uploaded_at (datetime | None): UTC upload timestamp for file resources.
        deactivate_by (str | None): Id of the actor who deactivated the record.
        delete_by (str | None): Id of the actor who deleted the record.
    """

    def __init__(self, **kwargs):
        self.id = kwargs.get("id") or uuid.uuid4()
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at") or datetime.now(timezone.utc)
        self.updated_at = kwargs.get("updated_at")
        self.uploaded_at = kwargs.get("uploaded_at")
        self.deactivate_by = kwargs.get("deactivate_by")
        self.delete_by = kwargs.get("delete_by")

    def to_dict(self):
        """Return a dict of all public instance attributes.

        Returns:
            dict: Mapping of attribute names to values, excluding private
                attributes whose names start with an underscore.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
