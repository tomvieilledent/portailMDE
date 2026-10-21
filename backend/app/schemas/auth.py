"""Schémas d'authentification : connexion, jetons et réinitialisation du mot de passe."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Identifiants de connexion."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Demande de renouvellement des jetons."""

    refresh_token: str


class TokenPair(BaseModel):
    """Paire de jetons d'accès et de rafraîchissement."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """Demande de réinitialisation du mot de passe."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Nouveau mot de passe accompagné du jeton de réinitialisation."""

    token: str
    new_password: str = Field(min_length=8, max_length=256)
