"""Routes des notifications : consultation, lecture, suppression et diffusion."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.core.permissions import Permission
from app.models import User
from app.schemas.notification import BroadcastRequest, NotificationRead, UnreadCount
from app.services import notifications as service

router = APIRouter(prefix="/notifications", tags=["notifications"])
NewsManager = Annotated[User, Depends(require_permission(Permission.MANAGE_NEWS))]


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    session: SessionDep,
    current: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    unread_only: bool = False,
):
    """Liste les notifications de l'utilisateur courant."""
    return service.list_notifications(
        session, current, limit=limit, offset=offset, unread_only=unread_only
    )


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(session: SessionDep, current: CurrentUser):
    """Retourne le nombre de notifications non lues."""
    return UnreadCount(count=service.unread_count(session, current))


@router.post("/read-all", status_code=204)
def read_all(session: SessionDep, current: CurrentUser):
    """Marque toutes les notifications comme lues."""
    service.mark_all_read(session, current)
    return Response(status_code=204)


@router.post("/broadcast", status_code=204)
def broadcast(body: BroadcastRequest, session: SessionDep, _: NewsManager):
    """Diffuse une notification à des utilisateurs (ou à tous si aucun n'est précisé)."""
    service.broadcast(session, body.content, body.user_ids)
    return Response(status_code=204)


@router.post("/{notification_id}/read", response_model=NotificationRead)
def read(notification_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Marque une notification comme lue."""
    return service.mark_read(session, current, notification_id)


@router.delete("/{notification_id}", status_code=204)
def delete(notification_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Supprime une notification."""
    service.delete(session, current, notification_id)
    return Response(status_code=204)
