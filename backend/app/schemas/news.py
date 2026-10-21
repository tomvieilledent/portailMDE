import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str | None
    summary: str | None
    url: str | None
    category: str | None
    published_at: datetime | None


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source: str | None = Field(None, max_length=200)
    summary: str | None = None
    url: str | None = Field(None, max_length=512)
    category: str | None = Field(None, max_length=100)
    published_at: datetime | None = None


class SavedArticleRead(ArticleRead):
    article_id: uuid.UUID | None
    saved_at: datetime


class SyncResult(BaseModel):
    created: int


class ContentRead(BaseModel):
    key: str
    value: dict[str, Any]


class ContentUpdate(BaseModel):
    value: dict[str, Any]
