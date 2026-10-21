import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    kind: str | None
    data: dict[str, Any] | None
    is_read: bool
    created_at: datetime


class BroadcastRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    user_ids: list[uuid.UUID] = []


class UnreadCount(BaseModel):
    count: int
