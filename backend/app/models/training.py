"""Modèles des formations : catalogue, sessions et inscriptions."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import SessionStatus, TrainingKind


class Training(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Formation ou atelier du catalogue."""

    __tablename__ = "trainings"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    picture_path: Mapped[str | None] = mapped_column(String(512))
    link: Mapped[str | None] = mapped_column(String(512))
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    kind: Mapped[TrainingKind] = mapped_column(
        String(20),
        nullable=False,
        default=TrainingKind.FORMATION,
        server_default=TrainingKind.FORMATION.value,
    )
    documents: Mapped[list[str]] = mapped_column(
        # chemins de fichiers joints
        ARRAY(String(512)),
        nullable=False,
        default=list,
        server_default="{}",
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    sessions: Mapped[list["TrainingSession"]] = relationship(back_populates="training")


class TrainingSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Session datée d'une formation, avec un nombre de places limité."""

    __tablename__ = "training_sessions"
    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="dates_order"),
        CheckConstraint("max_participants > 0", name="max_participants_positive"),
    )

    training_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trainings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str | None] = mapped_column(String(512))
    link: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[SessionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=SessionStatus.UPCOMING,
        server_default=SessionStatus.UPCOMING.value,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    training: Mapped[Training] = relationship(back_populates="sessions")


class TrainingEnrollment(UUIDPrimaryKeyMixin, Base):
    """Inscription à une session, ou simple intérêt/favori pour une formation."""

    __tablename__ = "training_enrollments"
    __table_args__ = (UniqueConstraint("user_id", "training_id", name="user_training"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    training_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trainings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_sessions.id", ondelete="SET NULL"), index=True
    )
    interested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
