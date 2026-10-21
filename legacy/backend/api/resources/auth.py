"""Authentication endpoints: register, login, token refresh and logout."""

from datetime import timedelta

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
)
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.state import BLOCKLIST
from backend.models.user import User as DomainUser
from backend.persistence.services import UserService
from backend.services import mailer


service = UserService()


class AuthRegisterResource(Resource):
    """Register a new user account.

    Validates the request body with the domain model before persisting.
    Returns the new user object along with access and refresh tokens.
    """

    def post(self):
        """Create a new user and return JWT tokens.

        Expected JSON body:
            email (str): Valid email address.
            password (str): Password (min 8 chars).
            first_name (str | None): Optional first name.

        Returns:
            tuple[dict, int]: ``{user, access_token, refresh_token}`` and 201.
        """
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        if not email or not password:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'email and password required', 400)
        try:
            DomainUser(email=email, password=password, first_name=first_name)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        try:
            user = service.register(email, password, first_name=first_name)
        except IntegrityError:
            return error_response(
                ERROR_CODES['CONFLICT'],
                'a user with this email already exists', 409)
        except Exception as exc:
            return error_response(ERROR_CODES['CONFLICT'], 'could not create user', 409, str(exc))
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        return {'user': user, 'access_token': access_token, 'refresh_token': refresh_token}, 201


class AuthLoginResource(Resource):
    """Authenticate a user and return JWT tokens."""

    def post(self):
        """Validate credentials and issue access/refresh tokens.

        Expected JSON body:
            email (str): Registered email address.
            password (str): Account password.

        Returns:
            tuple[dict, int]: ``{access_token, refresh_token, user}`` and 200.
        """
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'email and password required', 400)
        user = service.login(email, password)
        if not user:
            return error_response(ERROR_CODES['INVALID_CREDENTIALS'], 'invalid credentials', 401)
        token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        return {'access_token': token, 'refresh_token': refresh_token, 'user': user}


class AuthRefreshResource(Resource):
    """Exchange a valid refresh token for a new access token."""

    @jwt_required(refresh=True)
    def post(self):
        """Issue a fresh access token using the provided refresh token.

        Returns:
            tuple[dict, int]: ``{access_token}`` and 200.
        """
        user_id = get_jwt_identity()
        return {'access_token': create_access_token(identity=user_id)}


class AuthLogoutResource(Resource):
    """Revoke the current JWT by adding its JTI to the in-memory blocklist."""

    @jwt_required()
    def post(self):
        """Add the current token's JTI to the blocklist.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200.
        """
        jwt_data = get_jwt()
        BLOCKLIST.add(jwt_data['jti'])
        return {'msg': 'logged out'}


# Marker claim that identifies a short-lived password-reset token.
RESET_PURPOSE = 'pwd_reset'


def _send_reset_email(email: str, reset_token: str) -> bool:
    """Email a password-reset link to the user. Returns whether it was sent."""
    link = f'{mailer.frontend_url()}/?reset_token={reset_token}'
    subject = 'Réinitialisation de votre mot de passe'
    text_body = (
        "Bonjour,\n\n"
        "Vous avez demandé la réinitialisation de votre mot de passe pour la "
        "Maison de l'Économie – Rodez Agglomération.\n\n"
        f"Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe "
        f"(valable 15 minutes) :\n{link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email : "
        "votre mot de passe restera inchangé.\n\n"
        "— Maison de l'Économie, Rodez Agglomération"
    )
    html_body = (
        "<div style=\"font-family:Arial,sans-serif;color:#1f2937;line-height:1.6\">"
        "<p>Bonjour,</p>"
        "<p>Vous avez demandé la réinitialisation de votre mot de passe pour la "
        "<strong>Maison de l'Économie – Rodez Agglomération</strong>.</p>"
        "<p>Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe "
        "(lien valable 15&nbsp;minutes) :</p>"
        f"<p style=\"margin:24px 0\"><a href=\"{link}\" "
        "style=\"background:#1a3a2a;color:#ffffff;padding:12px 22px;border-radius:10px;"
        "text-decoration:none;font-weight:bold;display:inline-block\">"
        "Réinitialiser mon mot de passe</a></p>"
        f"<p style=\"font-size:12px;color:#6b7280\">Ou copiez ce lien : {link}</p>"
        "<p style=\"font-size:12px;color:#6b7280\">Si vous n'êtes pas à l'origine de "
        "cette demande, ignorez cet email : votre mot de passe restera inchangé.</p>"
        "<p style=\"font-size:12px;color:#6b7280\">— Maison de l'Économie, Rodez Agglomération</p>"
        "</div>"
    )
    return mailer.send_email(email, subject, text_body, html_body=html_body)


class AuthForgotPasswordResource(Resource):
    """Start a password reset for the account matching an email."""

    def post(self):
        """Issue a short-lived password-reset token and email a reset link.

        Expected JSON body:
            email (str): Account email address.

        Returns ``{msg}`` always (no account enumeration). When SMTP is not
        configured, the token is returned in ``reset_token`` as a dev fallback
        so the flow remains testable without a mail server.
        """
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        if not email:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'email is required', 400)
        generic = {'msg': 'if the account exists, a reset link has been sent'}
        user = service.facade.get_by_email(email)
        if not user:
            return generic
        reset_token = create_access_token(
            identity=user['id'],
            expires_delta=timedelta(minutes=15),
            additional_claims={'purpose': RESET_PURPOSE},
        )
        sent = _send_reset_email(email, reset_token)
        if sent:
            return generic
        # DEV fallback: no mail server configured — return the token directly.
        return {**generic, 'reset_token': reset_token}


class AuthResetPasswordResource(Resource):
    """Complete a password reset using a token from /auth/forgot-password."""

    def post(self):
        """Set a new password given a valid reset token.

        Expected JSON body:
            reset_token (str): Token issued by /auth/forgot-password.
            password (str): New password (min 8 chars).

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or an error.
        """
        data = request.get_json(silent=True) or {}
        reset_token = data.get('reset_token')
        password = data.get('password')
        if not reset_token or not password:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'reset_token and password are required', 400)
        if len(password) < 8:
            return error_response(ERROR_CODES['VALIDATION_ERROR'],
                                  'password must be at least 8 characters', 400)
        try:
            decoded = decode_token(reset_token)
        except Exception:
            return error_response(ERROR_CODES['INVALID_TOKEN'], 'invalid or expired token', 401)
        if decoded.get('purpose') != RESET_PURPOSE:
            return error_response(ERROR_CODES['INVALID_TOKEN'], 'invalid reset token', 401)
        user_id = decoded.get('sub')
        if not service.reset_password(user_id, password):
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'msg': 'password updated'}
