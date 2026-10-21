"""Routes de l'agenda : événements, export iCalendar et invitations."""

import uuid
from datetime import date

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import InvitationStatus
from app.schemas.event import (
    EventCreate,
    EventRead,
    EventUpdate,
    InvitationRead,
    InvitationResponse,
    InviteRequest,
)
from app.services import events as service
from app.services import invitations
from app.services.agenda_pdf import build_agenda_pdf

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventRead])
def list_events(
    session: SessionDep, current: CurrentUser, start: date | None = None, end: date | None = None
):
    """Liste les événements visibles par l'utilisateur sur une période."""
    return service.list_events(session, current, start=start, end=end)


@router.get("/events/export.ics")
def export_events(
    session: SessionDep, current: CurrentUser, start: date | None = None, end: date | None = None
):
    """Exporte les événements visibles au format iCalendar (.ics)."""
    events = service.list_events(session, current, start=start, end=end)
    return Response(
        service.export_ics(events),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="agenda.ics"'},
    )


@router.get("/events/export.pdf")
def export_events_pdf(
    session: SessionDep, current: CurrentUser, start: date | None = None, end: date | None = None
):
    """Exporte les événements visibles en affiche PDF prête à imprimer ou à afficher."""
    events = service.list_events(session, current, start=start, end=end)
    return Response(
        build_agenda_pdf(events, start, end),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="agenda.pdf"'},
    )


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(body: EventCreate, session: SessionDep, current: CurrentUser):
    """Crée un événement."""
    return service.create_event(session, current, body)


@router.get("/events/{event_id}", response_model=EventRead)
def read_event(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retourne un événement."""
    return service.get_event(session, event_id, current)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: uuid.UUID, body: EventUpdate, session: SessionDep, current: CurrentUser):
    """Met à jour un événement."""
    return service.update_event(session, current, event_id, body)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Supprime un événement."""
    service.delete_event(session, current, event_id)
    return Response(status_code=204)


@router.get("/events/{event_id}/invitations", response_model=list[InvitationRead])
def event_invitations(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Liste les invitations d'un événement."""
    return service.list_event_invitations(session, current, event_id)


@router.post("/events/{event_id}/invitations", response_model=list[InvitationRead], status_code=201)
def invite_to_event(
    event_id: uuid.UUID, body: InviteRequest, session: SessionDep, current: CurrentUser
):
    """Invite des utilisateurs à un événement."""
    return service.invite_to_event(session, current, event_id, body.user_ids)


@router.get("/invitations/me", response_model=list[InvitationRead])
def my_invitations(
    session: SessionDep, current: CurrentUser, status: InvitationStatus | None = None
):
    """Liste les invitations de l'utilisateur courant, filtrables par statut."""
    result = []
    for invitation, title in invitations.list_for_user(session, current, status):
        item = InvitationRead.model_validate(invitation)
        item.target_title = title
        result.append(item)
    return result


@router.post("/invitations/{invitation_id}/respond", response_model=InvitationRead)
def respond(
    invitation_id: uuid.UUID, body: InvitationResponse, session: SessionDep, current: CurrentUser
):
    """Répond à une invitation (accepter ou refuser)."""
    return invitations.respond(session, current, invitation_id, body.status)


@router.post("/invitations/{invitation_id}/read", response_model=InvitationRead)
def read_invitation(invitation_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Marque une invitation comme lue."""
    return invitations.mark_read(session, current, invitation_id)
