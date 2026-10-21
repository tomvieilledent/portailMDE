"""Invitations (RSVP) à un événement ou à une session de formation."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models import Event, Invitation, TrainingSession, User
from app.models.enums import InvitationStatus
from app.services import notifications


def invite(
    session: Session,
    inviter: User,
    user_ids: list[uuid.UUID],
    *,
    event_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    label: str = "",
) -> list[Invitation]:
    """Invite des utilisateurs (ignore ceux déjà invités ou soi-même)."""
    wanted = {uid for uid in user_ids if uid != inviter.id}
    found = set(
        session.scalars(
            select(User.id).where(
                User.id.in_(wanted), User.deleted_at.is_(None), User.is_active.is_(True)
            )
        ).all()
    )
    if found != wanted:
        raise NotFoundError("Un ou plusieurs utilisateurs sont introuvables")
    target = Invitation.event_id == event_id if event_id else Invitation.session_id == session_id
    already = set(
        session.scalars(
            select(Invitation.invitee_id).where(target, Invitation.invitee_id.in_(wanted))
        )
    )
    created = [
        Invitation(event_id=event_id, session_id=session_id, inviter_id=inviter.id, invitee_id=uid)
        for uid in wanted - already
    ]
    session.add_all(created)
    session.commit()
    notifications.notify(
        session,
        [i.invitee_id for i in created],
        f"{notifications.display_name(inviter)} vous invite : {label}".strip(" :"),
        kind="invitation",
        data={
            "event_id": str(event_id) if event_id else None,
            "session_id": str(session_id) if session_id else None,
        },
    )
    return created


def list_for_user(
    session: Session, user: User, status: InvitationStatus | None = None
) -> list[tuple[Invitation, str | None]]:
    """Invitations reçues, avec le titre de la cible, les plus récentes d'abord."""
    query = select(Invitation).where(Invitation.invitee_id == user.id)
    if status:
        query = query.where(Invitation.status == status)
    invitations = session.scalars(query.order_by(Invitation.created_at.desc())).all()
    result = []
    for invitation in invitations:
        if invitation.event_id:
            target = session.get(Event, invitation.event_id)
            title = target.title if target else None
        else:
            target = session.get(TrainingSession, invitation.session_id)
            title = target.training.title if target else None
        result.append((invitation, title))
    return result


def respond(
    session: Session, user: User, invitation_id: uuid.UUID, status: InvitationStatus
) -> Invitation:
    if status == InvitationStatus.PENDING:
        raise AppError("La réponse doit être 'accepted' ou 'declined'")
    invitation = session.get(Invitation, invitation_id)
    if not invitation or invitation.invitee_id != user.id:
        raise NotFoundError("Invitation introuvable")
    invitation.status = status
    invitation.is_read = True
    invitation.responded_at = datetime.now(UTC)
    session.commit()
    verb = "accepté" if status == InvitationStatus.ACCEPTED else "décliné"
    notifications.notify(
        session,
        [invitation.inviter_id],
        f"{notifications.display_name(user)} a {verb} votre invitation",
        kind="invitation_response",
        data={"invitation_id": str(invitation.id)},
    )
    return invitation


def mark_read(session: Session, user: User, invitation_id: uuid.UUID) -> Invitation:
    invitation = session.get(Invitation, invitation_id)
    if not invitation or invitation.invitee_id != user.id:
        raise NotFoundError("Invitation introuvable")
    invitation.is_read = True
    session.commit()
    return invitation
