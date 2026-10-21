from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import UnauthorizedError
from app.core.security import (
    InvalidTokenError,
    create_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.models import RevokedToken, User

# Hash factice : vérifié même si l'email est inconnu, pour égaliser le temps de réponse.
_DUMMY_HASH = hash_password("dummy-password")


def _issue_pair(user: User) -> dict[str, str]:
    access, _, _ = create_token(str(user.id), "access")
    refresh, _, _ = create_token(str(user.id), "refresh")
    return {"access_token": access, "refresh_token": refresh}


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.scalar(
        select(User).where(func.lower(User.email) == email.lower(), User.deleted_at.is_(None))
    )
    ok = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise UnauthorizedError("Identifiants invalides")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        session.commit()
    return user


def login(session: Session, email: str, password: str) -> dict[str, str]:
    return _issue_pair(authenticate(session, email, password))


def is_revoked(session: Session, jti: str) -> bool:
    return session.get(RevokedToken, jti) is not None


def revoke(session: Session, payload: dict) -> None:
    if not is_revoked(session, payload["jti"]):
        session.add(
            RevokedToken(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], UTC))
        )
        session.commit()


def refresh(session: Session, refresh_token: str) -> dict[str, str]:
    """Rotation : l'ancien refresh est révoqué, une nouvelle paire est émise."""
    try:
        payload = decode_token(refresh_token, "refresh")
    except InvalidTokenError as exc:
        raise UnauthorizedError("Jeton invalide") from exc
    if is_revoked(session, payload["jti"]):
        raise UnauthorizedError("Jeton révoqué")
    user = session.get(User, payload["sub"])
    if not user or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Utilisateur inactif")
    revoke(session, payload)
    return _issue_pair(user)


def logout(session: Session, access_payload: dict, refresh_token: str | None) -> None:
    revoke(session, access_payload)
    if refresh_token:
        try:
            revoke(session, decode_token(refresh_token, "refresh"))
        except InvalidTokenError:
            pass


def purge_expired(session: Session) -> int:
    result = session.execute(
        RevokedToken.__table__.delete().where(RevokedToken.expires_at < datetime.now(UTC))
    )
    session.commit()
    return result.rowcount
