import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()

TokenType = Literal["access", "refresh", "reset"]


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def _is_legacy_bcrypt(password_hash: str) -> bool:
    return password_hash.startswith(("$2a$", "$2b$", "$2y$"))


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe (Argon2, ou bcrypt hérité de l'ancienne application)."""
    if _is_legacy_bcrypt(password_hash):
        try:
            return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
        except ValueError:
            return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Vrai pour un hash bcrypt hérité ou des paramètres Argon2 obsolètes (re-hash à la connexion)."""
    return _is_legacy_bcrypt(password_hash) or _hasher.check_needs_rehash(password_hash)


def create_token(
    subject: str, token_type: TokenType, extra: dict | None = None
) -> tuple[str, str, datetime]:
    """Retourne ``(jwt, jti, expiration)``. ``extra`` ajoute des claims personnalisés."""
    settings = get_settings()
    now = datetime.now(UTC)
    lifetime = {
        "access": timedelta(minutes=settings.access_token_minutes),
        "refresh": timedelta(days=settings.refresh_token_days),
        "reset": timedelta(minutes=settings.reset_token_minutes),
    }[token_type]
    expires_at = now + lifetime
    jti = uuid.uuid4().hex
    payload = {
        **(extra or {}),
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str, expected_type: TokenType) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise InvalidTokenError("Type de jeton invalide")
    return payload


def password_fingerprint(password_hash: str) -> str:
    """Empreinte du hash actuel : un jeton de réinitialisation devient invalide après usage."""
    import hashlib

    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]
