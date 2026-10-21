import uuid
from datetime import UTC, date, datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, NotFoundError
from app.core.permissions import Permission, has_permission
from app.models import Event, Invitation, User
from app.services import invitations


def _can_see_all(user: User) -> bool:
    return has_permission(user, Permission.MANAGE_TRAININGS)


def _visible_filter(user: User):
    invited = exists().where(Invitation.event_id == Event.id, Invitation.invitee_id == user.id)
    return or_(Event.is_public.is_(True), Event.created_by == user.id, invited)


def get_event(session: Session, event_id: uuid.UUID, user: User) -> Event:
    event = session.get(Event, event_id)
    if not event or event.deleted_at is not None:
        raise NotFoundError("Événement introuvable")
    if not _can_see_all(user):
        visible = session.scalar(
            select(Event.id).where(Event.id == event_id, _visible_filter(user))
        )
        if not visible:
            raise NotFoundError("Événement introuvable")
    return event


def list_events(
    session: Session, user: User, *, start: date | None = None, end: date | None = None
) -> list[Event]:
    query = select(Event).where(Event.deleted_at.is_(None))
    if not _can_see_all(user):
        query = query.where(_visible_filter(user))
    if start:
        query = query.where(Event.event_date >= start)
    if end:
        query = query.where(Event.event_date <= end)
    return list(session.scalars(query.order_by(Event.event_date, Event.event_time)).all())


def create_event(session: Session, user: User, data) -> Event:
    values = data.model_dump(exclude={"invitee_ids"})
    event = Event(**values, created_by=user.id)
    session.add(event)
    session.commit()
    if data.invitee_ids:
        invitations.invite(session, user, data.invitee_ids, event_id=event.id, label=event.title)
    return event


def _ensure_owner(event: Event, user: User) -> None:
    if event.created_by != user.id and not _can_see_all(user):
        raise ForbiddenError("Seul le créateur peut modifier cet événement")


def update_event(session: Session, user: User, event_id: uuid.UUID, data) -> Event:
    event = get_event(session, event_id, user)
    _ensure_owner(event, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    session.commit()
    return event


def delete_event(session: Session, user: User, event_id: uuid.UUID) -> None:
    event = get_event(session, event_id, user)
    _ensure_owner(event, user)
    event.deleted_at = datetime.now(UTC)
    session.commit()


def invite_to_event(session: Session, user: User, event_id: uuid.UUID, user_ids):
    event = get_event(session, event_id, user)
    _ensure_owner(event, user)
    return invitations.invite(session, user, user_ids, event_id=event.id, label=event.title)


def list_event_invitations(session: Session, user: User, event_id: uuid.UUID) -> list[Invitation]:
    event = get_event(session, event_id, user)
    _ensure_owner(event, user)
    return list(session.scalars(select(Invitation).where(Invitation.event_id == event.id)).all())


def export_ics(events: list[Event], domain: str = "portailmde") -> str:
    """Calendrier iCalendar (RFC 5545) des événements fournis."""

    def esc(text: str) -> str:
        return (
            text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
        )

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//portailMDE//FR", "CALSCALE:GREGORIAN"]
    for event in events:
        lines += ["BEGIN:VEVENT", f"UID:{event.id}@{domain}", f"DTSTAMP:{stamp}"]
        day = event.event_date.strftime("%Y%m%d")
        if event.event_time:
            lines.append(f"DTSTART:{day}T{event.event_time.strftime('%H%M%S')}")
        else:
            lines.append(f"DTSTART;VALUE=DATE:{day}")
        lines.append(f"SUMMARY:{esc(event.title)}")
        if event.description:
            lines.append(f"DESCRIPTION:{esc(event.description)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
