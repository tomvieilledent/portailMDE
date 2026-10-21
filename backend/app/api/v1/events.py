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

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventRead])
def list_events(
    session: SessionDep, current: CurrentUser, start: date | None = None, end: date | None = None
):
    return service.list_events(session, current, start=start, end=end)


@router.get("/events/export.ics")
def export_events(
    session: SessionDep, current: CurrentUser, start: date | None = None, end: date | None = None
):
    events = service.list_events(session, current, start=start, end=end)
    return Response(
        service.export_ics(events),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="agenda.ics"'},
    )


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(body: EventCreate, session: SessionDep, current: CurrentUser):
    return service.create_event(session, current, body)


@router.get("/events/{event_id}", response_model=EventRead)
def read_event(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.get_event(session, event_id, current)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: uuid.UUID, body: EventUpdate, session: SessionDep, current: CurrentUser):
    return service.update_event(session, current, event_id, body)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    service.delete_event(session, current, event_id)
    return Response(status_code=204)


@router.get("/events/{event_id}/invitations", response_model=list[InvitationRead])
def event_invitations(event_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.list_event_invitations(session, current, event_id)


@router.post("/events/{event_id}/invitations", response_model=list[InvitationRead], status_code=201)
def invite_to_event(
    event_id: uuid.UUID, body: InviteRequest, session: SessionDep, current: CurrentUser
):
    return service.invite_to_event(session, current, event_id, body.user_ids)


@router.get("/invitations/me", response_model=list[InvitationRead])
def my_invitations(
    session: SessionDep, current: CurrentUser, status: InvitationStatus | None = None
):
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
    return invitations.respond(session, current, invitation_id, body.status)


@router.post("/invitations/{invitation_id}/read", response_model=InvitationRead)
def read_invitation(invitation_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return invitations.mark_read(session, current, invitation_id)
