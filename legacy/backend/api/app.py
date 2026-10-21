"""Flask application factory and API route registration.

This module exposes `create_app()` which configures Flask, JWT callbacks,
error handlers and registers all API resources for the application.
"""

import atexit
import os

from dotenv import load_dotenv

# Load variables from a local .env file if present. This is a no-op in
# production where real environment variables are set by the platform.
# Existing environment variables always take precedence (override=False),
# so tests and prod configs are never clobbered by a stray .env.
load_dotenv()

from flask import Flask, jsonify, send_from_directory
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import JWTExtendedException, NoAuthorizationError

from backend.api.errors import ERROR_CODES, error_response
from backend.api.uploads import UPLOAD_ROOT, ensure_upload_dirs
from backend.api.swagger import OPENAPI_SPEC, SWAGGER_UI_HTML
from backend.api.resources.auth import (
    AuthForgotPasswordResource,
    AuthLoginResource,
    AuthLogoutResource,
    AuthRefreshResource,
    AuthRegisterResource,
    AuthResetPasswordResource,
)
from backend.api.resources.company import CompanyAssignUserResource, CompanyDeactivateResource, CompanyListResource, CompanyReactivateResource, CompanyResource, CompanyUsersResource
from backend.api.resources.conversation import ConversationListResource, ConversationResource
from backend.api.resources.formation_user import FormationUserListResource, FormationUserResource
from backend.api.resources.message import (
    ConversationMessagesResource,
    ConversationReadResource,
    DirectMessagesResource,
    MessageAttachmentResource,
    MessageListResource,
    MessageReadResource,
    MessageResource,
    PresenceResource,
    UnreadCountResource,
)
from backend.api.resources.event import EventListResource, EventResource
from backend.api.resources.news import (
    NewsListResource, NewsResource, NewsSyncResource,
    SavedNewsListResource, SavedNewsResource,
)
from backend.api.resources.notification import NotificationListResource, NotificationResource
from backend.api.resources.content import ContentResource
from backend.api.resources.contact import ContactResource
from backend.api.resources.export import MonthlyExportResource
from backend.api.resources.invitation import (
    CurrentUserInvitationsResource,
    InvitationListResource,
    InvitationResource,
)
from backend.api.resources.training import (
    CurrentUserSavedTrainingsResource,
    CurrentUserTrainingsResource,
    TrainingDocumentResource,
    TrainingEnrollmentsResource,
    TrainingInterestResource,
    TrainingListResource,
    TrainingResource,
    TrainingSavedResource,
    UserTrainingsResource,
)
from backend.api.resources.training_session import (
    TrainingCompletionsResource,
    TrainingInterestedResource,
    TrainingSessionEnrollResource,
    TrainingSessionListResource,
    TrainingSessionResource,
    TrainingSessionsByTrainingResource,
)
from backend.api.resources.user import UserCompanyAdminResource, UserDeactivateResource, UserListResource, UserMeResource, UserPermissionsResource, UserReactivateResource, UserResetPasswordResource, UserResource, UserRoleResource
from backend.persistence.db import engine
import backend.persistence.models  # ensure models are imported
from pathlib import Path
from backend.api.state import BLOCKLIST
from backend.api.sockets import socketio
from backend.api.socket_events import message


def create_app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY', 'change-this-secret-to-a-long-random-string-32chars-min')
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    api = Api(app)
    jwt = JWTManager(app)
    socketio.init_app(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(_jwt_header, jwt_payload):
        return jwt_payload.get('jti') in BLOCKLIST

    @jwt.unauthorized_loader
    def unauthorized(reason):
        return error_response(ERROR_CODES['UNAUTHORIZED'], reason, 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response(ERROR_CODES['INVALID_TOKEN'], reason, 401)

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return error_response(ERROR_CODES['TOKEN_EXPIRED'], 'token has expired', 401)

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return error_response(ERROR_CODES['TOKEN_REVOKED'], 'token has been revoked', 401)

    @app.errorhandler(NoAuthorizationError)
    def handle_no_authorization(_exc):
        return error_response(ERROR_CODES['UNAUTHORIZED'], 'Missing Authorization Header', 401)

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exception(exc):
        return error_response(ERROR_CODES['INVALID_TOKEN'], str(exc), 401)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc):
        if isinstance(exc, NoAuthorizationError):
            return error_response(ERROR_CODES['UNAUTHORIZED'], 'Missing Authorization Header', 401)
        if isinstance(exc, JWTExtendedException):
            return error_response(ERROR_CODES['INVALID_TOKEN'], str(exc), 401)
        return error_response(ERROR_CODES['INTERNAL_ERROR'], 'internal server error', 500)

    # ensure sqlite file exists (best-effort)
    try:
        if engine.url.drivername == 'sqlite':
            database_path = engine.url.database
            if database_path:
                db_path = Path(database_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                if not db_path.exists():
                    db_path.touch()
                    try:
                        db_path.chmod(0o644)
                    except Exception:
                        pass
    except Exception:
        pass
    engine.dispose()
    ensure_upload_dirs()

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_ROOT, filename)


    api.add_resource(AuthRegisterResource, '/auth/register')
    api.add_resource(AuthLoginResource, '/auth/login')
    api.add_resource(AuthRefreshResource, '/auth/refresh')
    api.add_resource(AuthLogoutResource, '/auth/logout')
    api.add_resource(AuthForgotPasswordResource, '/auth/forgot-password')
    api.add_resource(AuthResetPasswordResource, '/auth/reset-password')
    api.add_resource(UserListResource, '/users')
    api.add_resource(UserMeResource, '/users/me', '/me')
    api.add_resource(UserResource, '/users/<string:user_id>')
    api.add_resource(UserDeactivateResource,
                     '/users/<string:user_id>/deactivate')
    api.add_resource(UserReactivateResource,
                     '/users/<string:user_id>/reactivate')
    api.add_resource(UserRoleResource,
                     '/users/<string:user_id>/role')
    api.add_resource(UserPermissionsResource,
                     '/users/<string:user_id>/permissions')
    api.add_resource(UserCompanyAdminResource,
                     '/users/<string:user_id>/company-admin')
    api.add_resource(UserResetPasswordResource,
                     '/users/<string:user_id>/reset-password')

    api.add_resource(CompanyListResource, '/companies')
    api.add_resource(CompanyResource, '/companies/<string:company_id>')
    api.add_resource(CompanyDeactivateResource,
                     '/companies/<string:company_id>/deactivate')
    api.add_resource(CompanyReactivateResource,
                     '/companies/<string:company_id>/reactivate')
    api.add_resource(CompanyUsersResource,
                     '/companies/<string:company_id>/users')
    api.add_resource(CompanyAssignUserResource,
                     '/companies/<string:company_id>/users/<string:user_id>')

    api.add_resource(TrainingListResource, '/trainings')
    api.add_resource(TrainingResource, '/trainings/<string:training_id>')
    api.add_resource(TrainingDocumentResource,
                     '/trainings/<string:training_id>/documents')
    api.add_resource(TrainingInterestResource,
                     '/trainings/<string:training_id>/interest')
    api.add_resource(TrainingSavedResource,
                     '/trainings/<string:training_id>/save')
    api.add_resource(TrainingEnrollmentsResource,
                     '/trainings/<string:training_id>/enrollments')
    api.add_resource(TrainingInterestedResource,
                     '/trainings/<string:training_id>/interested')
    api.add_resource(TrainingSessionsByTrainingResource,
                     '/trainings/<string:training_id>/sessions')
    api.add_resource(UserTrainingsResource,
                     '/users/<string:user_id>/trainings')
    api.add_resource(CurrentUserTrainingsResource, '/me/trainings')
    api.add_resource(CurrentUserSavedTrainingsResource, '/me/saved-trainings')

    api.add_resource(TrainingSessionListResource, '/training-sessions')
    api.add_resource(TrainingSessionResource,
                     '/training-sessions/<string:session_id>')
    api.add_resource(TrainingSessionEnrollResource,
                     '/training-sessions/<string:session_id>/enroll')
    api.add_resource(TrainingCompletionsResource, '/trainings/completions')

    api.add_resource(ConversationListResource, '/conversations', '/rooms')
    api.add_resource(ConversationResource,
                     '/conversations/<string:conversation_id>',
                     '/rooms/<string:conversation_id>')
    api.add_resource(ConversationMessagesResource,
                     '/conversations/<string:conversation_id>/messages',
                     '/rooms/<string:conversation_id>/messages')
    api.add_resource(ConversationReadResource,
                     '/conversations/<string:conversation_id>/read',
                     '/rooms/<string:conversation_id>/read')

    api.add_resource(PresenceResource, '/presence')
    api.add_resource(MessageListResource, '/messages')
    api.add_resource(MessageAttachmentResource, '/messages/attachment')
    api.add_resource(DirectMessagesResource, '/messages/direct/<string:user_id>')
    api.add_resource(UnreadCountResource, '/messages/unread')
    api.add_resource(MessageReadResource, '/messages/<string:message_id>/read')
    api.add_resource(MessageResource, '/messages/<string:message_id>')

    api.add_resource(ContentResource, '/content/<string:key>')
    api.add_resource(ContactResource, '/contact')
    api.add_resource(MonthlyExportResource, '/exports/monthly')
    api.add_resource(InvitationListResource, '/invitations')
    api.add_resource(CurrentUserInvitationsResource, '/me/invitations')
    api.add_resource(InvitationResource, '/invitations/<string:invitation_id>')
    api.add_resource(NotificationListResource, '/notifications')
    api.add_resource(NotificationResource,
                     '/notifications/<string:notification_id>')

    api.add_resource(NewsListResource, '/news')
    api.add_resource(SavedNewsListResource, '/news/saved')
    api.add_resource(SavedNewsResource, '/news/saved/<string:saved_id>')
    api.add_resource(NewsResource, '/news/<string:news_id>')
    api.add_resource(NewsSyncResource, '/news/sync')

    api.add_resource(FormationUserListResource, '/formation-users')
    api.add_resource(FormationUserResource,
                     '/formation-users/<string:relation_id>')

    api.add_resource(EventListResource, '/events')
    api.add_resource(EventResource, '/events/<string:event_id>')

    @app.route('/status')
    def home():
        return jsonify({'ok': True})

    @app.route('/openapi.json')
    def openapi_json():
        """Return the OpenAPI specification as JSON."""
        return jsonify(OPENAPI_SPEC)

    @app.route('/')
    @app.route('/docs')
    @app.route('/swagger')
    def swagger_docs():
        """Serve the Swagger UI page for interactive API testing."""
        return SWAGGER_UI_HTML

    # Start daily news sync scheduler (skip in test mode and in the reloader
    # parent process so the job only runs once per server instance).
    if not app.testing and os.environ.get('WERKZEUG_RUN_MAIN', 'true') == 'true':
        try:
            from datetime import datetime, timezone
            from apscheduler.schedulers.background import BackgroundScheduler
            from backend.services.news_sync import sync_all
            from backend.services.agenda_export import generate_next_month_if_due

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(sync_all, 'interval', days=1,
                               id='news_sync', replace_existing=True,
                               next_run_time=datetime.now(timezone.utc))
            # On the 25th of each month, generate next month's agenda sheet.
            scheduler.add_job(generate_next_month_if_due, 'cron', day=25, hour=6,
                               id='agenda_export', replace_existing=True)
            scheduler.start()
            atexit.register(scheduler.shutdown)
        except Exception:
            pass

    return app
