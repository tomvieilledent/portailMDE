"""Routes d'authentification : connexion, jetons, déconnexion et réinitialisation du mot de passe."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import CurrentUser, SessionDep, get_access_payload
from app.core import ratelimit
from app.core.errors import UnauthorizedError
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, session: SessionDep, request: Request):
    """Authentifie un utilisateur et retourne une paire de jetons (débit limité, verrou par email)."""
    email_key = body.email.lower()
    ratelimit.login_ip.hit(ratelimit.client_ip(request))
    ratelimit.login_failures.check(email_key)
    try:
        tokens = auth_service.login(session, body.email, body.password)
    except UnauthorizedError:
        ratelimit.login_failures.record(email_key)
        raise
    ratelimit.login_failures.reset(email_key)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, session: SessionDep):
    """Renouvelle la paire de jetons à partir d'un jeton de rafraîchissement."""
    return auth_service.refresh(session, body.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    session: SessionDep,
    _user: CurrentUser,
    payload: Annotated[dict, Depends(get_access_payload)],
    body: RefreshRequest | None = None,
):
    """Révoque le jeton d'accès courant (et le jeton de rafraîchissement fourni)."""
    auth_service.logout(session, payload, body.refresh_token if body else None)
    return Response(status_code=204)


@router.post("/forgot-password", status_code=204)
def forgot_password(body: ForgotPasswordRequest, session: SessionDep, request: Request):
    """Réponse toujours identique, que le compte existe ou non (débit limité)."""
    ratelimit.forgot_ip.hit(ratelimit.client_ip(request))
    ratelimit.forgot_email.hit(body.email.lower())
    auth_service.request_password_reset(session, body.email)
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
def reset_password(body: ResetPasswordRequest, session: SessionDep, request: Request):
    """Définit un nouveau mot de passe à partir d'un jeton de réinitialisation (débit limité)."""
    ratelimit.reset_ip.hit(ratelimit.client_ip(request))
    auth_service.reset_password(session, body.token, body.new_password)
    return Response(status_code=204)
