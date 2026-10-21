"""Model package exports.

This module re-exports domain model classes for convenient imports like
`from backend.models import User`.
"""

from .base import BaseModel
from .user import User
from .company import Company
from .training import Training
from .training_session import TrainingSession
from .formation_user import FormationUser
from .conversation import Conversation
from .message import Message
from .notification import Notification
from .news import News

__all__ = [
    "BaseModel",
    "User",
    "Company",
    "Training",
    "TrainingSession",
    "FormationUser",
    "Conversation",
    "Message",
    "Notification",
    "News",
]

Enrollment = FormationUser
