"""Catalogue de formations, sessions et inscriptions."""

import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.permissions import Permission, has_permission
from app.models import Invitation, Training, TrainingEnrollment, TrainingSession, User
from app.models.enums import SessionStatus, TrainingKind
from app.schemas.training import SessionRead
from app.services import storage


def _is_manager(user: User) -> bool:
    return has_permission(user, Permission.MANAGE_TRAININGS)


# --- Formations ---------------------------------------------------------------------------


def get_training(session: Session, training_id: uuid.UUID, user: User) -> Training:
    training = session.get(Training, training_id)
    if not training or training.deleted_at is not None:
        raise NotFoundError("Formation introuvable")
    if not training.is_active and not _is_manager(user):
        raise NotFoundError("Formation introuvable")
    return training


def list_trainings(
    session: Session,
    user: User,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    category: str | None = None,
    kind: TrainingKind | None = None,
) -> tuple[list[Training], int]:
    query = select(Training).where(Training.deleted_at.is_(None))
    if not _is_manager(user):
        query = query.where(Training.is_active.is_(True))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Training.title.ilike(pattern), Training.description.ilike(pattern)))
    if category:
        query = query.where(Training.category == category)
    if kind:
        query = query.where(Training.kind == kind)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(query.order_by(Training.title).limit(limit).offset(offset)).all()
    return list(items), total


def create_training(session: Session, data) -> Training:
    training = Training(**data.model_dump())
    session.add(training)
    session.commit()
    return training


def update_training(session: Session, user: User, training_id: uuid.UUID, data) -> Training:
    training = get_training(session, training_id, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(training, field, value)
    session.commit()
    return training


def set_training_active(session: Session, user: User, training_id: uuid.UUID, active: bool):
    training = get_training(session, training_id, user)
    training.is_active = active
    session.commit()
    return training


def delete_training(session: Session, user: User, training_id: uuid.UUID) -> None:
    training = get_training(session, training_id, user)
    training.deleted_at = datetime.now(UTC)
    training.is_active = False
    session.commit()


def set_picture(session: Session, user: User, training_id: uuid.UUID, file: UploadFile):
    training = get_training(session, training_id, user)
    new_path = storage.save_image(file, "trainings")
    old_path = training.picture_path
    training.picture_path = new_path
    session.commit()
    storage.delete_file(old_path)
    return training


def add_document(session: Session, user: User, training_id: uuid.UUID, file: UploadFile):
    training = get_training(session, training_id, user)
    path, _ = storage.save_document(file, "trainings")
    training.documents = [*training.documents, path]
    session.commit()
    return training


# --- Intérêt / inscriptions ---------------------------------------------------------------


def _enrollment(session: Session, user_id: uuid.UUID, training_id: uuid.UUID, create=False):
    enrollment = session.scalar(
        select(TrainingEnrollment).where(
            TrainingEnrollment.user_id == user_id, TrainingEnrollment.training_id == training_id
        )
    )
    if not enrollment and create:
        enrollment = TrainingEnrollment(user_id=user_id, training_id=training_id)
        session.add(enrollment)
    return enrollment


def set_interest(session: Session, user: User, training_id: uuid.UUID, interested: bool):
    training = get_training(session, training_id, user)
    enrollment = _enrollment(session, user.id, training.id, create=interested)
    if enrollment:
        enrollment.interested = interested
    session.commit()
    return enrollment


def list_interested(session: Session, training_id: uuid.UUID, user: User):
    training = get_training(session, training_id, user)
    return list(
        session.scalars(
            select(TrainingEnrollment).where(
                TrainingEnrollment.training_id == training.id,
                TrainingEnrollment.interested.is_(True),
            )
        ).all()
    )


def my_enrollments(session: Session, user: User) -> list[TrainingEnrollment]:
    return list(
        session.scalars(
            select(TrainingEnrollment).where(TrainingEnrollment.user_id == user.id)
        ).all()
    )


# --- Sessions -----------------------------------------------------------------------------


def _enrolled_count(session: Session, session_id: uuid.UUID) -> int:
    return (
        session.scalar(
            select(func.count()).where(
                TrainingEnrollment.session_id == session_id,
                TrainingEnrollment.enrolled_at.is_not(None),
            )
        )
        or 0
    )


def session_view(session: Session, ts: TrainingSession, user: User) -> SessionRead:
    view = SessionRead.model_validate(ts)
    view.enrolled_count = _enrolled_count(session, ts.id)
    view.is_enrolled = bool(
        session.scalar(
            select(TrainingEnrollment.id).where(
                TrainingEnrollment.session_id == ts.id,
                TrainingEnrollment.user_id == user.id,
                TrainingEnrollment.enrolled_at.is_not(None),
            )
        )
    )
    return view


def _session_visible(user: User):
    invited = exists().where(
        Invitation.session_id == TrainingSession.id, Invitation.invitee_id == user.id
    )
    return or_(TrainingSession.is_public.is_(True), TrainingSession.created_by == user.id, invited)


def get_session(session: Session, session_id: uuid.UUID, user: User) -> TrainingSession:
    ts = session.get(TrainingSession, session_id)
    if not ts:
        raise NotFoundError("Session introuvable")
    get_training(session, ts.training_id, user)
    if not _is_manager(user) and not session.scalar(
        select(TrainingSession.id).where(TrainingSession.id == ts.id, _session_visible(user))
    ):
        raise NotFoundError("Session introuvable")
    return ts


def list_sessions(
    session: Session,
    user: User,
    *,
    training_id: uuid.UUID | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[TrainingSession]:
    query = (
        select(TrainingSession)
        .join(Training)
        .where(Training.deleted_at.is_(None), Training.is_active.is_(True))
    )
    if not _is_manager(user):
        query = query.where(_session_visible(user))
    if training_id:
        query = query.where(TrainingSession.training_id == training_id)
    if start:
        query = query.where(TrainingSession.start_at >= start)
    if end:
        query = query.where(TrainingSession.start_at <= end)
    return list(session.scalars(query.order_by(TrainingSession.start_at)).all())


def create_session(session: Session, user: User, training_id: uuid.UUID, data) -> TrainingSession:
    training = get_training(session, training_id, user)
    ts = TrainingSession(training_id=training.id, created_by=user.id, **data.model_dump())
    session.add(ts)
    session.commit()
    return ts


def update_session(session: Session, user: User, session_id: uuid.UUID, data) -> TrainingSession:
    ts = get_session(session, session_id, user)
    values = data.model_dump(exclude_unset=True)
    if "max_participants" in values and values["max_participants"] < _enrolled_count(
        session, ts.id
    ):
        raise AppError("Capacité inférieure au nombre d'inscrits")
    for field, value in values.items():
        setattr(ts, field, value)
    if ts.end_at < ts.start_at:
        raise AppError("La fin doit être postérieure au début")
    session.commit()
    return ts


def delete_session(session: Session, user: User, session_id: uuid.UUID) -> None:
    ts = get_session(session, session_id, user)
    session.delete(ts)
    session.commit()


def enroll(session: Session, user: User, session_id: uuid.UUID) -> TrainingEnrollment:
    ts = get_session(session, session_id, user)
    if ts.status in (SessionStatus.DONE, SessionStatus.CANCELLED):
        raise AppError("Les inscriptions à cette session sont closes")
    enrollment = _enrollment(session, user.id, ts.training_id, create=True)
    if enrollment.session_id == ts.id and enrollment.enrolled_at:
        raise ConflictError("Vous êtes déjà inscrit à cette session")
    # Verrou sur la session pour éviter un dépassement de capacité en cas de concurrence.
    session.execute(select(TrainingSession.id).where(TrainingSession.id == ts.id).with_for_update())
    if _enrolled_count(session, ts.id) >= ts.max_participants:
        session.rollback()
        raise ConflictError("Session complète")
    enrollment.session_id = ts.id
    enrollment.enrolled_at = datetime.now(UTC)
    enrollment.completed_at = None
    session.commit()
    return enrollment


def unenroll(session: Session, user: User, session_id: uuid.UUID) -> None:
    ts = get_session(session, session_id, user)
    enrollment = _enrollment(session, user.id, ts.training_id)
    if not enrollment or enrollment.session_id != ts.id or not enrollment.enrolled_at:
        raise NotFoundError("Vous n'êtes pas inscrit à cette session")
    enrollment.session_id = None
    enrollment.enrolled_at = None
    session.commit()


def list_enrollments(session: Session, user: User, session_id: uuid.UUID):
    ts = get_session(session, session_id, user)
    return list(
        session.scalars(
            select(TrainingEnrollment).where(
                TrainingEnrollment.session_id == ts.id,
                TrainingEnrollment.enrolled_at.is_not(None),
            )
        ).all()
    )


def mark_completed(
    session: Session, user: User, session_id: uuid.UUID, user_id: uuid.UUID
) -> TrainingEnrollment:
    ts = get_session(session, session_id, user)
    enrollment = _enrollment(session, user_id, ts.training_id)
    if not enrollment or enrollment.session_id != ts.id:
        raise NotFoundError("Inscription introuvable")
    enrollment.completed_at = datetime.now(UTC)
    session.commit()
    return enrollment
