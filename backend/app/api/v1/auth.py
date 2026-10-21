from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentUser, SessionDep, get_access_payload
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
def login(body: LoginRequest, session: SessionDep):
    return auth_service.login(session, body.email, body.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, session: SessionDep):
    return auth_service.refresh(session, body.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    session: SessionDep,
    _user: CurrentUser,
    payload: Annotated[dict, Depends(get_access_payload)],
    body: RefreshRequest | None = None,
):
    auth_service.logout(session, payload, body.refresh_token if body else None)
    return Response(status_code=204)


@router.post("/forgot-password", status_code=204)
def forgot_password(body: ForgotPasswordRequest, session: SessionDep):
    """Réponse toujours identique, que le compte existe ou non."""
    auth_service.request_password_reset(session, body.email)
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
def reset_password(body: ResetPasswordRequest, session: SessionDep):
    auth_service.reset_password(session, body.token, body.new_password)
    return Response(status_code=204)
