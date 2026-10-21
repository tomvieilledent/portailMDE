"""Routes de la messagerie : conversations, participants, messages et pièces jointes."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, Query, Response, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import NotFoundError
from app.schemas.chat import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    ParticipantsUpdate,
)
from app.services import chat as service
from app.services import storage
from app.services.realtime import manager

router = APIRouter(tags=["chat"])


def _event(kind: str, conversation_id: uuid.UUID, **data) -> dict:
    """Construit l'événement temps réel diffusé aux participants d'une conversation."""
    return {"type": kind, "conversation_id": str(conversation_id), **data}


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(session: SessionDep, current: CurrentUser):
    """Liste les conversations de l'utilisateur courant."""
    return service.list_conversations(session, current)


@router.post("/conversations", response_model=ConversationRead, status_code=201)
def create_conversation(
    body: ConversationCreate,
    session: SessionDep,
    current: CurrentUser,
    background: BackgroundTasks,
):
    """Crée une conversation directe ou de groupe et en informe les participants."""
    if body.kind == "direct":
        conversation = service.create_direct(session, current, body.user_id)
    else:
        conversation = service.create_group(session, current, body.title, body.user_ids)
    background.add_task(
        manager.send_to_users,
        service.participant_ids(conversation),
        _event("conversation.created", conversation.id),
    )
    return service.to_read(session, conversation, current)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def read_conversation(conversation_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retourne une conversation dont l'utilisateur est participant."""
    conversation = service.get_conversation(session, conversation_id, current)
    return service.to_read(session, conversation, current)


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
def rename_conversation(
    conversation_id: uuid.UUID, body: ConversationUpdate, session: SessionDep, current: CurrentUser
):
    """Renomme une conversation de groupe."""
    conversation = service.get_conversation(session, conversation_id, current)
    service.rename_group(session, conversation, current, body.title)
    return service.to_read(session, conversation, current)


@router.post("/conversations/{conversation_id}/participants", response_model=ConversationRead)
def add_participants(
    conversation_id: uuid.UUID,
    body: ParticipantsUpdate,
    session: SessionDep,
    current: CurrentUser,
    background: BackgroundTasks,
):
    """Ajoute des participants à une conversation de groupe."""
    conversation = service.get_conversation(session, conversation_id, current)
    service.add_participants(session, conversation, current, body.user_ids)
    background.add_task(
        manager.send_to_users,
        service.participant_ids(conversation),
        _event("conversation.updated", conversation.id),
    )
    return service.to_read(session, conversation, current)


@router.delete("/conversations/{conversation_id}/participants/{user_id}", status_code=204)
def remove_participant(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUser,
    background: BackgroundTasks,
):
    """Retire un participant d'une conversation de groupe."""
    conversation = service.get_conversation(session, conversation_id, current)
    audience = service.participant_ids(conversation)
    service.remove_participant(session, conversation, current, user_id)
    background.add_task(
        manager.send_to_users, audience, _event("conversation.updated", conversation_id)
    )
    return Response(status_code=204)


@router.post("/conversations/{conversation_id}/read", status_code=204)
def mark_read(conversation_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Marque la conversation comme lue par l'utilisateur courant."""
    conversation = service.get_conversation(session, conversation_id, current)
    service.mark_read(session, conversation, current)
    return Response(status_code=204)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    before: datetime | None = None,
):
    """Liste les messages d'une conversation, du plus récent au plus ancien, avec pagination."""
    conversation = service.get_conversation(session, conversation_id, current)
    return service.list_messages(session, conversation, limit=limit, before=before)


@router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageRead, status_code=201
)
def send_message(
    conversation_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUser,
    background: BackgroundTasks,
    content: Annotated[str, Form()] = "",
    file: UploadFile | None = None,
):
    """Envoie un message (texte et/ou pièce jointe) et le diffuse en temps réel."""
    conversation = service.get_conversation(session, conversation_id, current)
    message = service.send_message(session, conversation, current, content, file)
    payload = MessageRead.model_validate(message).model_dump(mode="json")
    background.add_task(
        manager.send_to_users,
        service.participant_ids(conversation),
        _event("message.new", conversation.id, message=payload),
    )
    return message


@router.delete("/messages/{message_id}", status_code=204)
def delete_message(
    message_id: uuid.UUID, session: SessionDep, current: CurrentUser, background: BackgroundTasks
):
    """Supprime un message et en informe les participants."""
    message = service.delete_message(session, message_id, current)
    conversation = service.get_conversation(session, message.conversation_id, current)
    background.add_task(
        manager.send_to_users,
        service.participant_ids(conversation),
        _event("message.deleted", message.conversation_id, message_id=str(message.id)),
    )
    return Response(status_code=204)


@router.get("/messages/{message_id}/file")
def download_attachment(message_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Pièce jointe, réservée aux participants de la conversation."""
    message = service.get_message(session, message_id, current)
    if not message.file_path:
        raise NotFoundError("Aucune pièce jointe")
    path = storage.upload_root() / message.file_path
    if not path.is_file():
        raise NotFoundError("Fichier introuvable")
    return FileResponse(path, filename=message.file_name)
