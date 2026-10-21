"""SQLAlchemy ORM models used for persistence.

This module defines the tables and columns used by Alembic migrations and
by the persistence layer.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, UniqueConstraint
from .db import Base
import uuid
from datetime import datetime, timezone


class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    email = Column(String(254), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    job_title = Column(String(120))
    phone = Column(String(30))
    profile_picture = Column(String(256))
    business_card = Column(String(256))
    is_super_admin = Column(Boolean, default=False)
    is_company_admin = Column(Boolean, default=False)
    # Platform staff: a non-super-admin account holding a configurable subset
    # of admin rights, stored as a CSV of permission keys in ``permissions``.
    is_staff = Column(Boolean, default=False)
    permissions = Column(String(512))
    company_id = Column(String(36))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True),
                        onupdate=lambda: datetime.now(timezone.utc))
    deactivate_by = Column(String(36))
    delete_by = Column(String(36))


class Company(Base):
    __tablename__ = 'companies'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(String(2000))
    location = Column(String(200))
    website_link = Column(String(512))
    company_picture = Column(String(512))
    admin_email = Column(String(254))
    admin_id = Column(String(36))
    # 'company' (entreprise hébergée) ou 'trainer' (formateur).
    kind = Column(String(20), default='company')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True),
                        onupdate=lambda: datetime.now(timezone.utc))
    deactivate_by = Column(String(36))
    delete_by = Column(String(36))


class Training(Base):
    __tablename__ = 'trainings'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    company_id = Column(String(36))
    description = Column(String(2000))
    picture = Column(String(512))
    # Free-text category (no fixed list) and kind: 'formation' or 'atelier'.
    category = Column(String(100))
    type = Column(String(20), default='formation')
    # Attachments (e.g. scanned brochures) stored as a CSV of upload paths.
    documents = Column(String(2000))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True),
                        onupdate=lambda: datetime.now(timezone.utc))
    deactivate_by = Column(String(36))
    delete_by = Column(String(36))


class Message(Base):
    __tablename__ = 'messages'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    author_id = Column(String(36), nullable=False)
    recipient_id = Column(String(36))
    conversation_id = Column(String(36))
    content = Column(String(5000), nullable=False)
    file_url = Column(String(1000))
    file_name = Column(String(500))
    is_read = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))


class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    # Optional group name. A conversation with a title is a named group chat;
    # untitled conversations are treated as ad-hoc rooms.
    title = Column(String(200))
    # UUID of the user who created the group. Only the creator may rename it
    # or add/remove members; other participants may only leave.
    creator_id = Column(String(36))
    # participant_ids stored as a comma-separated string for simplicity
    participant_ids = Column(String(1000))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))


class ConversationParticipant(Base):
    __tablename__ = 'conversation_participants'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    uploaded_at = Column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), nullable=False)
    content = Column(String(1000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))


class News(Base):
    __tablename__ = 'news'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    source = Column(String(200))
    summary = Column(String(2000))
    url = Column(String(512))
    category = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))


class SavedNews(Base):
    """Per-user bookmark of a news article.

    A self-contained snapshot of the article (title/url/summary/…) so it stays
    visible to the user even after the rolling-month purge removes the original
    row from ``news``. ``news_id`` keeps a soft link to the source article when
    it still exists, and prevents duplicate bookmarks per user.
    """

    __tablename__ = 'saved_news'
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='uq_saved_news_user_article'),
    )
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    news_id = Column(String(36))
    title = Column(String(500), nullable=False)
    source = Column(String(200))
    summary = Column(String(2000))
    url = Column(String(512))
    category = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    saved_at = Column(DateTime(timezone=True),
                      default=lambda: datetime.now(timezone.utc))


class Event(Base):
    __tablename__ = 'events'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    # date/time stored as plain strings ('YYYY-MM-DD' / 'HH:MM') to map
    # directly to the agenda UI without timezone parsing.
    date = Column(String(10), nullable=False)
    time = Column(String(5))
    color = Column(String(50))
    description = Column(String(2000))
    creator = Column(String(120))
    created_by = Column(String(36))
    # Public events are visible to everyone and included in the monthly export
    # sheet; private ones stay invitation-only.
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        onupdate=lambda: datetime.now(timezone.utc))


class TrainingSession(Base):
    __tablename__ = 'training_sessions'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    training_id = Column(String(36), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    max_participants = Column(Integer(), nullable=False)
    location = Column(String(512))
    link = Column(String(512))
    status = Column(String(50), default='upcoming')
    # Public sessions are visible to everyone and included in the monthly
    # export sheet; private ones stay invitation-only.
    is_public = Column(Boolean, default=False)
    created_by = Column(String(36))
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        onupdate=lambda: datetime.now(timezone.utc))


class FormationUser(Base):
    __tablename__ = 'formation_users'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    training_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    type = Column(String(50))
    saved = Column(Boolean, default=False)
    enrolled_at = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))


class Invitation(Base):
    """An RSVP invitation to an event or a training, one row per invitee."""
    __tablename__ = 'invitations'
    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    target_type = Column(String(20), nullable=False)   # 'event' | 'training'
    target_id = Column(String(36), nullable=False)
    target_title = Column(String(300))                 # denormalised for display
    inviter_id = Column(String(36), nullable=False)
    invitee_id = Column(String(36), nullable=False)
    status = Column(String(20), default='pending')     # pending|accepted|declined
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime(timezone=True))


class SiteContent(Base):
    """Editable site content blocks, keyed by name (e.g. 'landing').

    `value` holds a JSON document so a whole structured block (slogan,
    subtitle, cards…) can be stored and edited from the admin UI.
    """
    __tablename__ = 'site_content'
    key = Column(String(100), primary_key=True)
    value = Column(String(8000))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
