"""Authentification : connexion, jetons, révocation et réinitialisation du mot de passe."""

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
    """Émet une paire de jetons (accès et rafraîchissement) pour l'utilisateur."""
    access, _, _ = create_token(str(user.id), "access")
    refresh, _, _ = create_token(str(user.id), "refresh")
    return {"access_token": access, "refresh_token": refresh}


def authenticate(session: Session, email: str, password: str) -> User:
    """Vérifie les identifiants et retourne l'utilisateur ; re-hache le mot de passe si nécessaire."""
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
    """Authentifie l'utilisateur et retourne une paire de jetons."""
    return _issue_pair(authenticate(session, email, password))


def is_revoked(session: Session, jti: str) -> bool:
    """Indique si le jeton (identifié par son ``jti``) a été révoqué."""
    return session.get(RevokedToken, jti) is not None


def revoke(session: Session, payload: dict) -> None:
    """Révoque un jeton jusqu'à son expiration."""
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
    """Révoque le jeton d'accès et, s'il est fourni, le jeton de rafraîchissement."""
    revoke(session, access_payload)
    if refresh_token:
        try:
            revoke(session, decode_token(refresh_token, "refresh"))
        except InvalidTokenError:
            pass


def purge_expired(session: Session) -> int:
    """Supprime les révocations dont le jeton est expiré ; retourne le nombre de lignes supprimées."""
    result = session.execute(
        RevokedToken.__table__.delete().where(RevokedToken.expires_at < datetime.now(UTC))
    )
    session.commit()
    return result.rowcount


# --- Réinitialisation du mot de passe -----------------------------------------------------


def request_password_reset(session: Session, email: str) -> None:
    """Envoie un lien de réinitialisation si le compte existe (réponse identique sinon)."""
    from app.core.config import get_settings
    from app.core.security import password_fingerprint
    from app.emails import templates
    from app.services.mailer import send_later

    user = session.scalar(
        select(User).where(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
    )
    if not user:
        return
    settings = get_settings()
    token, _, _ = create_token(
        str(user.id), "reset", {"pwd": password_fingerprint(user.password_hash)}
    )
    link = f"{settings.frontend_url}/reset-password?token={token}"
    name = user.first_name or user.email
    send_later(user.email, *templates.reset_password(name, link, settings.reset_token_minutes))


def reset_password(session: Session, token: str, new_password: str) -> None:
    """Définit un nouveau mot de passe si le jeton de réinitialisation est valide et non utilisé."""
    from app.core.security import password_fingerprint

    try:
        payload = decode_token(token, "reset")
    except InvalidTokenError as exc:
        raise UnauthorizedError("Lien invalide ou expiré") from exc
    user = session.get(User, payload["sub"])
    if (
        not user
        or not user.is_active
        or user.deleted_at is not None
        or payload.get("pwd") != password_fingerprint(user.password_hash)
    ):
        raise UnauthorizedError("Lien invalide ou expiré")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    session.commit()
