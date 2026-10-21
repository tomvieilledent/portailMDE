"""Notifications utilisateur : création, push temps réel, lecture."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Notification, User
from app.schemas.notification import NotificationRead
from app.services.realtime import push


def notify(
    session: Session,
    recipient_ids: list[uuid.UUID],
    content: str,
    *,
    kind: str | None = None,
    data: dict | None = None,
) -> list[Notification]:
    """Crée une notification par destinataire et la pousse en temps réel."""
    notifications = [
        Notification(recipient_id=uid, content=content[:1000], kind=kind, data=data)
        for uid in set(recipient_ids)
    ]
    if not notifications:
        return []
    session.add_all(notifications)
    session.commit()
    for notification in notifications:
        payload = NotificationRead.model_validate(notification).model_dump(mode="json")
        push([notification.recipient_id], {"type": "notification.new", "notification": payload})
    return notifications


def display_name(user: User) -> str:
    """Nom affiché d'un utilisateur : prénom et nom, ou à défaut son email."""
    name = " ".join(filter(None, [user.first_name, user.last_name]))
    return name or user.email


def list_notifications(
    session: Session, user: User, *, limit: int, offset: int, unread_only: bool = False
) -> list[Notification]:
    """Liste les notifications de l'utilisateur, les plus récentes d'abord."""
    query = select(Notification).where(Notification.recipient_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    return list(
        session.scalars(
            query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )


def unread_count(session: Session, user: User) -> int:
    """Compte les notifications non lues de l'utilisateur."""
    return (
        session.scalar(
            select(func.count()).where(
                Notification.recipient_id == user.id, Notification.is_read.is_(False)
            )
        )
        or 0
    )


def _get_own(session: Session, user: User, notification_id: uuid.UUID) -> Notification:
    """Retourne une notification appartenant à l'utilisateur, ou lève une erreur."""
    notification = session.get(Notification, notification_id)
    if not notification or notification.recipient_id != user.id:
        raise NotFoundError("Notification introuvable")
    return notification


def mark_read(session: Session, user: User, notification_id: uuid.UUID) -> Notification:
    """Marque une notification comme lue."""
    notification = _get_own(session, user, notification_id)
    notification.is_read = True
    session.commit()
    return notification


def mark_all_read(session: Session, user: User) -> None:
    """Marque toutes les notifications de l'utilisateur comme lues."""
    session.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    session.commit()


def delete(session: Session, user: User, notification_id: uuid.UUID) -> None:
    """Supprime une notification de l'utilisateur."""
    session.delete(_get_own(session, user, notification_id))
    session.commit()


def broadcast(
    session: Session, content: str, user_ids: list[uuid.UUID] | None = None
) -> list[Notification]:
    """Annonce à une liste d'utilisateurs, ou à tous les comptes actifs si ``user_ids`` est vide."""
    if not user_ids:
        user_ids = list(
            session.scalars(
                select(User.id).where(User.is_active.is_(True), User.deleted_at.is_(None))
            ).all()
        )
    return notify(session, user_ids, content, kind="announcement")
