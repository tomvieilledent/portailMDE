import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InvitationStatus


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    event_date: date
    event_time: time | None
    color: str | None
    is_public: bool
    created_by: uuid.UUID | None
    created_at: datetime


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    event_date: date
    event_time: time | None = None
    color: str | None = Field(None, max_length=50)
    is_public: bool = False
    invitee_ids: list[uuid.UUID] = []


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    event_date: date | None = None
    event_time: time | None = None
    color: str | None = Field(None, max_length=50)
    is_public: bool | None = None


class InviteRequest(BaseModel):
    user_ids: list[uuid.UUID] = Field(min_length=1)


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID | None
    session_id: uuid.UUID | None
    inviter_id: uuid.UUID
    invitee_id: uuid.UUID
    status: InvitationStatus
    is_read: bool
    created_at: datetime
    responded_at: datetime | None
    target_title: str | None = None


class InvitationResponse(BaseModel):
    status: InvitationStatus
