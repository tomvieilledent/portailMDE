"""Service layer: lightweight wrappers around persistence facades.

Services expose business-oriented methods and delegate persistence to
the corresponding facade implementations.
"""

from typing import Any

from backend.persistence.db import SessionLocal
from backend.persistence.models import User as ORMUser
from backend.persistence.services.facades import (
    UserFacade,
    CompanyFacade,
    TrainingFacade,
    TrainingSessionFacade,
    MessageFacade,
    ConversationFacade,
    ConversationParticipantFacade,
    NotificationFacade,
    NewsFacade,
    SavedNewsFacade,
    FormationUserFacade,
    EventFacade,
    SiteContentFacade,
    InvitationFacade,
)


class UserService:
    """Service exposing common user workflows.

    Methods map 1:1 to the underlying `UserFacade` but keep a stable
    interface for API code to use.
    """

    def __init__(self):
        self.facade = UserFacade()

    def register(self, email, password, first_name=None, last_name=None, **kwargs):
        return self.facade.create_user(email, password, first_name=first_name, last_name=last_name, **kwargs)

    def login(self, email, password):
        if not self.facade.check_password(email, password):
            return None
        return self.facade.get_by_email(email)

    def list_users(self, limit=100):
        return self.facade.list_users(limit=limit)

    def list_users_by_company(self, company_id, limit=100):
        return self.facade.list_users(limit=limit, company_id=company_id)

    def get_by_id(self, user_id):
        return self.facade.get_by_id(user_id)

    def update(self, user_id, **kwargs):
        return self.facade.update(user_id, **kwargs)

    def delete(self, user_id):
        return self.facade.delete(user_id)

    def reset_password(self, user_id, password):
        return self.facade.reset_password(user_id, password)

    def deactivate(self, identifier, by=None):
        return self.facade.deactivate(identifier, by=by)

    def _to_dict(self, user):
        if not user:
            return None
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
        }


class CompanyService:
    """Service facade for company-related operations."""

    def __init__(self):
        self.facade = CompanyFacade()


class TrainingService:
    """Service facade for training operations."""

    def __init__(self):
        self.facade = TrainingFacade()


class MessageService:
    """Service facade for message persistence operations."""

    def __init__(self):
        self.facade = MessageFacade()


class ConversationService:
    """Service facade for conversations."""

    def __init__(self):
        self.facade = ConversationFacade()


class ConversationParticipantService:
    """Service facade for conversation participant associations."""

    def __init__(self):
        self.facade = ConversationParticipantFacade()


class NotificationService:
    """Service facade for notifications."""

    def __init__(self):
        self.facade = NotificationFacade()


class NewsService:
    """Service facade for news ingestion and listing."""

    def __init__(self):
        self.facade = NewsFacade()


class SavedNewsService:
    """Service facade for per-user saved-article (bookmark) operations."""

    def __init__(self):
        self.facade = SavedNewsFacade()


class TrainingSessionService:
    """Service facade for training session operations."""

    def __init__(self):
        self.facade = TrainingSessionFacade()


class FormationUserService:
    """Service facade for formation/user enrollment operations."""

    def __init__(self):
        self.facade = FormationUserFacade()


class EventService:
    """Service facade for agenda event operations."""

    def __init__(self):
        self.facade = EventFacade()


class SiteContentService:
    """Service facade for editable site content blocks."""

    def __init__(self):
        self.facade = SiteContentFacade()


class InvitationService:
    """Service facade for event/training invitations (RSVP)."""

    def __init__(self):
        self.facade = InvitationFacade()
