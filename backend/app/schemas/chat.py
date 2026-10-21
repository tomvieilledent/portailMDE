"""Schémas de la messagerie : conversations, participants et messages."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class UserBrief(BaseModel):
    """Résumé d'un utilisateur (identité et avatar)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str | None
    last_name: str | None
    avatar_path: str | None


class MessageRead(BaseModel):
    """Message d'une conversation, avec l'URL de sa pièce jointe éventuelle."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    author_id: uuid.UUID | None
    author: UserBrief | None
    content: str
    file_name: str | None
    file_path: str | None = Field(None, exclude=True)
    created_at: datetime

    @computed_field
    @property
    def file_url(self) -> str | None:
        """URL de téléchargement de la pièce jointe, si elle existe."""
        return f"/api/v1/messages/{self.id}/file" if self.file_path else None


class ConversationCreate(BaseModel):
    """Création d'une conversation directe ou de groupe."""

    kind: Literal["direct", "group"]
    user_id: uuid.UUID | None = None
    user_ids: list[uuid.UUID] = []
    title: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def _check(self):
        """Vérifie les champs requis selon le type de conversation."""
        if self.kind == "direct" and not self.user_id:
            raise ValueError("user_id est requis pour une conversation directe")
        if self.kind == "group" and (not self.title or not self.user_ids):
            raise ValueError("title et user_ids sont requis pour un groupe")
        return self


class ConversationUpdate(BaseModel):
    """Renommage d'une conversation de groupe."""

    title: str = Field(min_length=1, max_length=200)


class ParticipantsUpdate(BaseModel):
    """Liste d'utilisateurs à ajouter à une conversation."""

    user_ids: list[uuid.UUID] = Field(min_length=1)


class ConversationRead(BaseModel):
    """Conversation avec ses participants, son dernier message et son nombre de messages non lus."""

    id: uuid.UUID
    kind: str
    title: str | None
    creator_id: uuid.UUID | None
    participants: list[UserBrief]
    last_message: MessageRead | None
    unread_count: int
    created_at: datetime
