import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import SessionStatus, TrainingKind
from app.schemas.chat import UserBrief


class TrainingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    picture_path: str | None
    category: str | None
    kind: TrainingKind
    documents: list[str]
    company_id: uuid.UUID | None
    is_active: bool
    created_at: datetime


class TrainingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    kind: TrainingKind = TrainingKind.FORMATION
    company_id: uuid.UUID | None = None


class TrainingUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    kind: TrainingKind | None = None
    company_id: uuid.UUID | None = None


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    training_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    max_participants: int
    location: str | None
    link: str | None
    status: SessionStatus
    is_public: bool
    created_by: uuid.UUID | None
    enrolled_count: int = 0
    is_enrolled: bool = False


class SessionCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    max_participants: int = Field(gt=0)
    location: str | None = Field(None, max_length=512)
    link: str | None = Field(None, max_length=512)
    is_public: bool = False

    @model_validator(mode="after")
    def _dates(self):
        if self.end_at < self.start_at:
            raise ValueError("end_at doit être postérieure à start_at")
        return self


class SessionUpdate(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    max_participants: int | None = Field(None, gt=0)
    location: str | None = Field(None, max_length=512)
    link: str | None = Field(None, max_length=512)
    status: SessionStatus | None = None
    is_public: bool | None = None


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    training_id: uuid.UUID
    session_id: uuid.UUID | None
    interested: bool
    enrolled_at: datetime | None
    completed_at: datetime | None
    user: UserBrief | None = None
