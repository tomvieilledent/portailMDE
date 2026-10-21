"""Training session API resources."""

from datetime import datetime, timezone

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.resources._helpers import _can
from backend.models.training_session import TrainingSession as DomainSession
from backend.persistence.services import (
    FormationUserService,
    InvitationService,
    TrainingService,
    TrainingSessionService,
    UserService,
)


session_service = TrainingSessionService()
formation_service = FormationUserService()
training_service = TrainingService()
user_service = UserService()
invitation_service = InvitationService()


def _accessible_session_ids(identity):
    """Set of session ids a non-manager user may see/access.

    A regular user only reaches a programmed session they were invited to or
    are already enrolled in. Managers bypass this (they see every session).
    """
    invited = invitation_service.facade.target_ids_for_invitee(
        identity, 'session')
    enrolled = {e['session_id']
                for e in formation_service.facade.list_by_user(identity)
                if e.get('session_id')}
    return invited | enrolled


def _can_access_session(identity, current, sess):
    """Whether *current* user may see/enroll in *sess* (a session dict)."""
    if _can(current, 'manage_trainings'):
        return True
    if sess.get('is_public'):
        return True
    if sess.get('created_by') == identity:
        return True
    return sess['id'] in _accessible_session_ids(identity)


def _parse_dt(value):
    """Parse an ISO 8601 string or pass-through an existing datetime.

    Args:
        value (str | datetime | None): Value to parse.

    Returns:
        datetime | None: Parsed UTC datetime, or ``None`` on failure.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class TrainingSessionListResource(Resource):
    """List all training sessions with optional filters."""

    @jwt_required()
    def get(self):
        """Return sessions, optionally filtered by training or status.

        Query parameters:
            training_id (str): Filter by training UUID.
            status (str): Filter by session status.
            limit (int): Max sessions to return (default 100).

        Returns:
            tuple[dict, int]: ``{sessions}`` and 200.
        """
        status = request.args.get('status')
        training_id = request.args.get('training_id')
        limit = request.args.get('limit', default=100, type=int)
        sessions = session_service.facade.list(
            training_id=training_id, status=status, limit=limit)
        identity = get_jwt_identity()
        current = user_service.get_by_id(identity)
        if not _can(current, 'manage_trainings'):
            accessible = _accessible_session_ids(identity)
            sessions = [s for s in sessions
                        if s.get('is_public')
                        or s.get('created_by') == identity
                        or s['id'] in accessible]
        return {'sessions': sessions}


class TrainingSessionsByTrainingResource(Resource):
    """List or create sessions for a specific training."""

    @jwt_required()
    def get(self, training_id):
        """Return all sessions for a training.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{sessions}`` and 200, or 404.
        """
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        sessions = session_service.facade.list(training_id=training_id)
        identity = get_jwt_identity()
        current = user_service.get_by_id(identity)
        if not _can(current, 'manage_trainings'):
            accessible = _accessible_session_ids(identity)
            sessions = [s for s in sessions
                        if s.get('is_public')
                        or s.get('created_by') == identity
                        or s['id'] in accessible]
        return {'sessions': sessions}

    @jwt_required()
    def post(self, training_id):
        """Create a training session. Restricted to super admins.

        Args:
            training_id (str): Training UUID path parameter.

        Expected JSON body:
            start_date (str): ISO 8601 start datetime.
            end_date (str): ISO 8601 end datetime.
            max_participants (int): Maximum number of enrollees (≥ 1).
            location (str | None): Optional physical location.
            link (str | None): Optional remote meeting link.

        Returns:
            tuple[dict, int]: ``{session}`` and 201, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to create sessions', 403)
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)

        data = request.get_json(silent=True) or {}
        start_date = _parse_dt(data.get('start_date'))
        end_date = _parse_dt(data.get('end_date'))
        max_participants = data.get('max_participants')

        if not start_date or not end_date:
            return error_response(
                ERROR_CODES['BAD_REQUEST'],
                'start_date and end_date are required', 400)
        if not max_participants:
            return error_response(
                ERROR_CODES['BAD_REQUEST'],
                'max_participants is required', 400)

        try:
            DomainSession(training_id=training_id, start_date=start_date,
                          end_date=end_date, max_participants=max_participants)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        sess = session_service.facade.create(
            training_id=training_id,
            start_date=start_date,
            end_date=end_date,
            max_participants=int(max_participants),
            location=data.get('location'),
            link=data.get('link'),
            is_public=bool(data.get('is_public')),
            created_by=get_jwt_identity(),
        )
        return {'session': sess}, 201


class TrainingSessionResource(Resource):
    """Retrieve, update or cancel a single training session."""

    @jwt_required()
    def get(self, session_id):
        """Return a session by id.

        Args:
            session_id (str): TrainingSession UUID path parameter.

        Returns:
            tuple[dict, int]: ``{session}`` and 200, or 404.
        """
        sess = session_service.facade.get(session_id)
        if not sess:
            return error_response(ERROR_CODES['NOT_FOUND'], 'session not found', 404)
        identity = get_jwt_identity()
        current = user_service.get_by_id(identity)
        if not _can_access_session(identity, current, sess):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to view this session', 403)
        return {'session': sess}

    @jwt_required()
    def patch(self, session_id):
        """Update a session's fields. Restricted to super admins.

        When ``status`` is set to ``"completed"``, all enrolled users are
        automatically marked as completed via a bulk update.

        Args:
            session_id (str): TrainingSession UUID path parameter.

        Returns:
            tuple[dict, int]: ``{session}`` and 200, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to update sessions', 403)

        if not session_service.facade.get(session_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'session not found', 404)

        data = request.get_json(silent=True) or {}
        update: dict = {}

        for field in ('location', 'link', 'status'):
            if field in data:
                update[field] = data[field]
        if 'is_public' in data:
            update['is_public'] = bool(data['is_public'])
        for dt_field in ('start_date', 'end_date'):
            if dt_field in data:
                parsed = _parse_dt(data[dt_field])
                if not parsed:
                    return error_response(
                        ERROR_CODES['BAD_REQUEST'],
                        f'invalid {dt_field}', 400)
                update[dt_field] = parsed
        if 'max_participants' in data:
            try:
                update['max_participants'] = int(data['max_participants'])
            except (TypeError, ValueError):
                return error_response(
                    ERROR_CODES['BAD_REQUEST'],
                    'max_participants must be an integer', 400)

        if update.get('status') == 'completed':
            result = session_service.facade.complete(session_id)
            return {'session': result}

        result = session_service.facade.update(session_id, **update)
        return {'session': result}

    @jwt_required()
    def delete(self, session_id):
        """Cancel a session. Restricted to super admins.

        Args:
            session_id (str): TrainingSession UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to delete sessions', 403)
        result = session_service.facade.update(session_id, status='cancelled')
        if not result:
            return error_response(ERROR_CODES['NOT_FOUND'], 'session not found', 404)
        return {'msg': 'session cancelled'}


class TrainingSessionEnrollResource(Resource):
    """Enroll or unenroll the current user from a session."""

    @jwt_required()
    def post(self, session_id):
        """Enroll the current user in a session.

        Auto-upgrades any existing ``interested`` record for the same training
        to ``enrolled``. Rejects enrollment when the session is full.

        Args:
            session_id (str): TrainingSession UUID path parameter.

        Returns:
            tuple[dict, int]: ``{enrollment}`` and 201, or 404/409.
        """
        user_id = get_jwt_identity()
        sess = session_service.facade.get(session_id)
        if not sess:
            return error_response(ERROR_CODES['NOT_FOUND'], 'session not found', 404)
        current = user_service.get_by_id(user_id)
        if not _can_access_session(user_id, current, sess):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'you must be invited to enroll in this session', 403)
        if sess['status'] == 'full':
            return error_response(
                ERROR_CODES['CONFLICT'],
                'session is full — you can express interest in the training instead',
                409)
        enrollment, err = formation_service.facade.enroll(
            user_id, sess['training_id'], session_id)
        if err:
            return error_response(ERROR_CODES['CONFLICT'], err, 409)
        return {'enrollment': enrollment}, 201

    @jwt_required()
    def delete(self, session_id):
        """Unenroll the current user from a session.

        If the session was full, it is reverted to ``upcoming``.

        Args:
            session_id (str): TrainingSession UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        user_id = get_jwt_identity()
        sess = session_service.facade.get(session_id)
        if not sess:
            return error_response(ERROR_CODES['NOT_FOUND'], 'session not found', 404)
        if not formation_service.facade.unenroll(user_id, session_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'enrollment not found', 404)
        return {'msg': 'unenrolled'}


class TrainingCompletionsResource(Resource):
    """List completed training records.

    Super admins see all completions; regular users see only their own.
    """

    @jwt_required()
    def get(self):
        """Return completed training records.

        Returns:
            tuple[dict, int]: ``{completions}`` and 200, or 404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not current_user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        if _can(current_user, 'manage_trainings'):
            completions = formation_service.facade.list_completions()
        else:
            completions = formation_service.facade.list_completions(
                user_id=get_jwt_identity())
        return {'completions': completions}


class TrainingInterestedResource(Resource):
    """List users who expressed interest in a training (super admin only)."""

    @jwt_required()
    def get(self, training_id):
        """Return users who expressed interest in a training.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{interested}`` and 200, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to view interest', 403)
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        return {'interested': formation_service.facade.list_interested(
            training_id=training_id)}
