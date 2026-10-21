from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import UnauthorizedError
from app.core.security import InvalidTokenError, decode_token
from app.db.session import get_session
from app.models import User
from app.services import auth as auth_service

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def get_access_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
) -> dict:
    if credentials is None:
        raise UnauthorizedError("Authentification requise")
    try:
        payload = decode_token(credentials.credentials, "access")
    except InvalidTokenError as exc:
        raise UnauthorizedError("Jeton invalide ou expiré") from exc
    if auth_service.is_revoked(session, payload["jti"]):
        raise UnauthorizedError("Jeton révoqué")
    return payload


def get_current_user(
    payload: Annotated[dict, Depends(get_access_payload)], session: SessionDep
) -> User:
    user = session.get(User, payload["sub"])
    if not user or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Utilisateur inactif ou introuvable")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
