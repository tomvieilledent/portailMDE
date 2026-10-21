"""Routes des formations : catalogue, sessions, inscriptions et invitations."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.core.permissions import Permission
from app.models import User
from app.models.enums import TrainingKind
from app.schemas.common import Page
from app.schemas.event import InvitationRead, InviteRequest
from app.schemas.training import (
    EnrollmentRead,
    SessionCreate,
    SessionRead,
    SessionUpdate,
    TrainingCreate,
    TrainingRead,
    TrainingUpdate,
)
from app.services import invitations
from app.services import trainings as service

router = APIRouter(tags=["trainings"])
Manager = Annotated[User, Depends(require_permission(Permission.MANAGE_TRAININGS))]


# --- Formations ---------------------------------------------------------------------------


@router.get("/trainings", response_model=Page[TrainingRead])
def list_trainings(
    session: SessionDep,
    current: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    category: str | None = None,
    kind: TrainingKind | None = None,
):
    """Liste les formations avec pagination, recherche et filtres."""
    items, total = service.list_trainings(
        session, current, limit=limit, offset=offset, search=search, category=category, kind=kind
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/trainings", response_model=TrainingRead, status_code=201)
def create_training(body: TrainingCreate, session: SessionDep, _: Manager):
    """Crée une formation."""
    return service.create_training(session, body)


@router.get("/trainings/mine", response_model=list[EnrollmentRead])
def my_trainings(session: SessionDep, current: CurrentUser):
    """Liste les inscriptions et marques d'intérêt de l'utilisateur courant."""
    return service.my_enrollments(session, current)


@router.get("/trainings/{training_id}", response_model=TrainingRead)
def read_training(training_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retourne une formation."""
    return service.get_training(session, training_id, current)


@router.patch("/trainings/{training_id}", response_model=TrainingRead)
def update_training(
    training_id: uuid.UUID, body: TrainingUpdate, session: SessionDep, current: Manager
):
    """Met à jour une formation."""
    return service.update_training(session, current, training_id, body)


@router.post("/trainings/{training_id}/deactivate", response_model=TrainingRead)
def deactivate_training(training_id: uuid.UUID, session: SessionDep, current: Manager):
    """Désactive une formation."""
    return service.set_training_active(session, current, training_id, False)


@router.post("/trainings/{training_id}/reactivate", response_model=TrainingRead)
def reactivate_training(training_id: uuid.UUID, session: SessionDep, current: Manager):
    """Réactive une formation."""
    return service.set_training_active(session, current, training_id, True)


@router.delete("/trainings/{training_id}", status_code=204)
def delete_training(training_id: uuid.UUID, session: SessionDep, current: Manager):
    """Supprime une formation."""
    service.delete_training(session, current, training_id)
    return Response(status_code=204)


@router.put("/trainings/{training_id}/picture", response_model=TrainingRead)
def upload_picture(training_id: uuid.UUID, session: SessionDep, current: Manager, file: UploadFile):
    """Téléverse l'image d'une formation."""
    return service.set_picture(session, current, training_id, file)


@router.post("/trainings/{training_id}/documents", response_model=TrainingRead)
def upload_document(
    training_id: uuid.UUID, session: SessionDep, current: Manager, file: UploadFile
):
    """Ajoute un document à une formation."""
    return service.add_document(session, current, training_id, file)


@router.put("/trainings/{training_id}/interest", status_code=204)
def mark_interest(training_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Marque l'intérêt de l'utilisateur courant pour une formation."""
    service.set_interest(session, current, training_id, True)
    return Response(status_code=204)


@router.delete("/trainings/{training_id}/interest", status_code=204)
def unmark_interest(training_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retire l'intérêt de l'utilisateur courant pour une formation."""
    service.set_interest(session, current, training_id, False)
    return Response(status_code=204)


@router.get("/trainings/{training_id}/interested", response_model=list[EnrollmentRead])
def interested(training_id: uuid.UUID, session: SessionDep, current: Manager):
    """Liste les utilisateurs intéressés par une formation."""
    return service.list_interested(session, training_id, current)


# --- Sessions -----------------------------------------------------------------------------


@router.get("/trainings/{training_id}/sessions", response_model=list[SessionRead])
def training_sessions(training_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Liste les sessions d'une formation."""
    service.get_training(session, training_id, current)
    sessions = service.list_sessions(session, current, training_id=training_id)
    return [service.session_view(session, s, current) for s in sessions]


@router.post("/trainings/{training_id}/sessions", response_model=SessionRead, status_code=201)
def create_session(
    training_id: uuid.UUID, body: SessionCreate, session: SessionDep, current: Manager
):
    """Crée une session pour une formation."""
    ts = service.create_session(session, current, training_id, body)
    return service.session_view(session, ts, current)


@router.get("/training-sessions", response_model=list[SessionRead])
def list_sessions(
    session: SessionDep,
    current: CurrentUser,
    start: datetime | None = None,
    end: datetime | None = None,
):
    """Liste les sessions de toutes les formations sur une période."""
    sessions = service.list_sessions(session, current, start=start, end=end)
    return [service.session_view(session, s, current) for s in sessions]


@router.get("/training-sessions/{session_id}", response_model=SessionRead)
def read_session(session_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retourne une session."""
    ts = service.get_session(session, session_id, current)
    return service.session_view(session, ts, current)


@router.patch("/training-sessions/{session_id}", response_model=SessionRead)
def update_session(
    session_id: uuid.UUID, body: SessionUpdate, session: SessionDep, current: Manager
):
    """Met à jour une session."""
    ts = service.update_session(session, current, session_id, body)
    return service.session_view(session, ts, current)


@router.delete("/training-sessions/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, session: SessionDep, current: Manager):
    """Supprime une session."""
    service.delete_session(session, current, session_id)
    return Response(status_code=204)


@router.post(
    "/training-sessions/{session_id}/enroll", response_model=EnrollmentRead, status_code=201
)
def enroll(session_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Inscrit l'utilisateur courant à une session."""
    return service.enroll(session, current, session_id)


@router.delete("/training-sessions/{session_id}/enroll", status_code=204)
def unenroll(session_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Annule l'inscription de l'utilisateur courant à une session."""
    service.unenroll(session, current, session_id)
    return Response(status_code=204)


@router.get("/training-sessions/{session_id}/enrollments", response_model=list[EnrollmentRead])
def enrollments(session_id: uuid.UUID, session: SessionDep, current: Manager):
    """Liste les inscriptions d'une session."""
    return service.list_enrollments(session, current, session_id)


@router.post(
    "/training-sessions/{session_id}/enrollments/{user_id}/complete", response_model=EnrollmentRead
)
def complete(session_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep, current: Manager):
    """Marque la participation d'un utilisateur à une session comme terminée."""
    return service.mark_completed(session, current, session_id, user_id)


@router.post(
    "/training-sessions/{session_id}/invitations",
    response_model=list[InvitationRead],
    status_code=201,
)
def invite(session_id: uuid.UUID, body: InviteRequest, session: SessionDep, current: Manager):
    """Invite des utilisateurs à une session de formation."""
    ts = service.get_session(session, session_id, current)
    return invitations.invite(
        session, current, body.user_ids, session_id=ts.id, label=ts.training.title
    )
