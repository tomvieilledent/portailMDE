"""Dépendances FastAPI : session de base de données, authentification et contrôle des droits."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, PasswordChangeRequiredError, UnauthorizedError
from app.core.permissions import Permission, has_permission
from app.core.security import InvalidTokenError, decode_token
from app.db.session import get_session
from app.models import User
from app.models.enums import UserRole
from app.services import auth as auth_service

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def get_access_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
) -> dict:
    """Extrait et valide le jeton d'accès (type, expiration, révocation) et retourne ses claims."""
    if credentials is None:
        raise UnauthorizedError("Authentification requise")
    try:
        payload = decode_token(credentials.credentials, "access")
    except InvalidTokenError as exc:
        raise UnauthorizedError("Jeton invalide ou expiré") from exc
    if auth_service.is_revoked(session, payload["jti"]):
        raise UnauthorizedError("Jeton révoqué")
    return payload


def get_current_user_allow_pending(
    payload: Annotated[dict, Depends(get_access_payload)], session: SessionDep
) -> User:
    """Retourne l'utilisateur authentifié, même s'il doit encore changer son mot de passe."""
    user = session.get(User, payload["sub"])
    if not user or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Utilisateur inactif ou introuvable")
    return user


def get_current_user(user: Annotated[User, Depends(get_current_user_allow_pending)]) -> User:
    """Retourne l'utilisateur authentifié ; refuse tant que le mot de passe temporaire est actif."""
    if user.must_change_password:
        raise PasswordChangeRequiredError("Vous devez d'abord changer votre mot de passe")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
# Routes accessibles avant le changement du mot de passe temporaire (profil, mot de passe, déconnexion).
PendingUser = Annotated[User, Depends(get_current_user_allow_pending)]


def require_permission(permission: Permission):
    """Dépendance : l'utilisateur doit détenir ``permission`` (super admin inclus)."""

    def checker(user: CurrentUser) -> User:
        """Vérifie que l'utilisateur courant détient la permission requise."""
        if not has_permission(user, permission):
            raise ForbiddenError("Droits insuffisants")
        return user

    return checker


def require_super_admin(user: CurrentUser) -> User:
    """Dépendance : réserve la route au super administrateur."""
    if user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Réservé au super administrateur")
    return user
